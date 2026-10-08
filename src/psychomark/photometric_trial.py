"""Offline S04 controlled photograph compensation trial, without answer decisions."""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from .baseline import digest
from .config import write_json
from .engine import Engine, bubble_roi
from .geometry_trial import compare_geometry, geometry_observations
from .images import normalized_gray, read_image, save_image
from .photometry import (
    PARAMETERS,
    VARIANTS,
    measure_question,
    prepare_pair,
    print_residuals,
    project_photo,
)
from .regions import crop, question_region
from .registration import Registrar, RegistrationError


def _observations(path: Path) -> dict[tuple[str, int], dict]:
    """Validate visual labels after manifest identity/split checks; omit personal fields."""
    manifest = json.loads(path.read_text(encoding="utf-8"))
    labels = {}
    for question in manifest["questions"]:
        annotation = question.get("annotation")
        if annotation is None:
            continue
        marks = annotation.get("marks")
        if (
            not isinstance(marks, list)
            or len(marks) != question["choices"]
            or any(m not in {"empty", "marked", "ambiguous", "unreadable"} for m in marks)
        ):
            raise ValueError("Invalid human mark labels")
        marked = [i for i, mark in enumerate(marks, 1) if mark == "marked"]
        status = (
            "unreadable"
            if "unreadable" in marks
            else "uncertain"
            if "ambiguous" in marks
            else "multiple"
            if len(marked) > 1
            else "single"
            if marked
            else "blank"
        )
        if annotation.get("status") != status or annotation.get("choices") != marked:
            raise ValueError("Human status/choices disagree with mark labels")
        if annotation.get("geometry") not in {"confirmed", "incorrect", "source_only"}:
            raise ValueError("Invalid human geometry status")
        labels[(question["section"], question["question"])] = {"marks": marks, "status": status}
    return labels


def _distribution(values: list[float]) -> dict:
    return {
        "count": len(values),
        "median": float(np.median(values)) if values else None,
        "p10": float(np.percentile(values, 10)) if values else None,
        "p90": float(np.percentile(values, 90)) if values else None,
    }


def compare_signals(
    questions: list[dict], labels: dict[tuple[str, int], dict], geometry: dict
) -> dict:
    """Evaluate signal separation only. Missing/rejected observations keep denominators.

    A positive single-mark margin is merely a ranking diagnostic; no blank detection,
    confidence, or automatic answer accuracy follows from it. Ambiguities stay separate.
    """
    indexed = {(q["section"], q["question"]): q for q in questions}
    located = {(o["section"], o["question"]): o for o in geometry["observations"]}
    groups = {m: [] for m in ("empty", "marked", "ambiguous", "unreadable")}
    excluded, margins, observations = Counter(), [], []
    for key, label in labels.items():
        geo = located.get(key)
        question = indexed.get(key)
        reason = (
            "no_confirmed_manual_geometry"
            if geo is None
            else "registration_failed"
            if question is None
            else "choice_centers_outside_human_box"
            if not geo.get("all_choice_centers_inside")
            else "unavailable_sampling_pixels"
            if not all(s["usable"] for s in question["scores"])
            else None
        )
        if reason is not None:
            excluded[reason] += 1
            continue
        values = [s["mean_positive_delta"] for s in question["scores"]]
        for mark, value in zip(label["marks"], values, strict=True):
            groups[mark].append(value)
        margin = None
        if label["status"] == "single":
            selected = label["marks"].index("marked")
            margin = values[selected] - max(v for i, v in enumerate(values) if i != selected)
            margins.append(margin)
        observations.append(
            {
                "section": key[0],
                "question": key[1],
                "human_status": label["status"],
                "marks": label["marks"],
                "mean_positive_delta": values,
                "single_mark_margin": margin,
            }
        )
    return {
        "annotated_questions": len(labels),
        "evaluated_questions": len(observations),
        "excluded_questions": dict(excluded),
        "human_status_counts": dict(Counter(v["status"] for v in labels.values())),
        "label_signals": {key: _distribution(values) for key, values in groups.items()},
        "single_mark_margin": _distribution(margins),
        "single_mark_positive_margin": sum(m > 0 for m in margins),
        "answer_accuracy": None,
        "observations": observations,
    }


def _paired_change(baseline: dict, candidate: dict) -> dict:
    indexed = {(o["section"], o["question"]): o for o in baseline["observations"]}
    changes = {m: [] for m in ("empty", "marked", "ambiguous", "unreadable")}
    ranking = Counter({"improved": 0, "regressed": 0, "unchanged": 0})
    paired = 0
    for observation in candidate["observations"]:
        previous = indexed.get((observation["section"], observation["question"]))
        if previous is None:
            continue
        paired += 1
        for label, before, after in zip(
            observation["marks"],
            previous["mean_positive_delta"],
            observation["mean_positive_delta"],
            strict=True,
        ):
            changes[label].append(after - before)
        if observation["single_mark_margin"] is not None:
            before, after = (
                previous["single_mark_margin"] > 0,
                observation["single_mark_margin"] > 0,
            )
            ranking[
                "improved" if after > before else "regressed" if before > after else "unchanged"
            ] += 1
    return {
        "baseline": "normalized",
        "paired_questions": paired,
        "signal_change_by_label": {key: _distribution(values) for key, values in changes.items()},
        "single_mark_ranking_change": dict(ranking),
    }


def run_photometric_trial(
    template_path: Path, source_path: Path, output: Path, manifest_path: Path | None = None
) -> dict:
    """Run fixed image ablations on one globally aligned source and identical ROIs.

    Development data only, no model training. Preserve historical engine output and
    quality diagnostics. Candidate measurements never bypass guards in the live engine.
    """
    if output.exists():
        raise ValueError("Output must be a new directory")
    engine = Engine.from_file(template_path)
    template = engine.template
    source = read_image(source_path)
    boxes, corpus = (
        ({}, None)
        if manifest_path is None
        else geometry_observations(manifest_path, template_path, source_path, source.shape[:2])
    )
    labels = {} if manifest_path is None else _observations(manifest_path)
    output.mkdir(parents=True)
    report = {
        "schema_version": 1,
        "purpose": "photometric_development_trial_not_answer_validation",
        "source_sha256": digest(source_path),
        "source_size": [source.shape[1], source.shape[0]],
        "reference_size": [template.width, template.height],
        "template_file_sha256": digest(template_path),
        "template_sha256": engine.template_digest,
        "reference_sha256": template.reference_sha256,
        "code_sha256": {
            name: digest(Path(__file__).with_name(name))
            for name in (
                "photometry.py",
                "photometric_trial.py",
                "geometry_trial.py",
                "config.py",
                "images.py",
                "regions.py",
                "engine.py",
                "registration.py",
            )
        },
        "versions": {"opencv": cv2.__version__, "numpy": np.__version__},
        "parameters": PARAMETERS,
        "geometry_method": "normalized_global_registration_fixed_for_all_variants",
        "sampling_method": "historical_ellipse_interior_and_original_normalized_reference_gt_200",
        "corpus": corpus,
        "registration": None,
        "geometry_comparison": compare_geometry([], boxes),
        "variants": {},
        "complete": False,
    }
    write_json(output / "template.json", template.model_dump())
    historical, _ = engine.analyze(source)
    write_json(output / "historical-result.json", historical)
    try:
        # Exactly one candidate homography; the seven photometric variants cannot move it.
        registrar = Registrar(normalized_gray(engine.reference), template)
        _, _, _, diagnostic = registrar.align(
            cv2.cvtColor(normalized_gray(source), cv2.COLOR_GRAY2BGR)
        )
    except (RegistrationError, ValueError) as exc:
        report["registration_error"] = str(exc)
        for name in VARIANTS:
            report["variants"][name] = {
                "status": "registration_failed",
                "sections": {},
                "questions": [],
                "comparison": compare_signals([], labels, report["geometry_comparison"]),
            }
    else:
        report["registration"] = diagnostic
        transform = np.asarray(diagnostic["input_to_reference"])
        inverse = np.linalg.inv(transform)
        aligned, valid = project_photo(source, transform, (template.width, template.height))
        regions = [
            question_region(section, q, inverse, valid.astype(np.uint8) * 255, source.shape[:2])
            for section in template.sections
            for q in range(1, section.questions + 1)
        ]
        report["geometry_comparison"] = compare_geometry([r.model_dump() for r in regions], boxes)
        write_json(output / "regions.json", [r.model_dump() for r in regions])
        save_image(output / "valid.png", valid.astype(np.uint8) * 255)
        for index, region in enumerate(regions):
            folder = output / "questions" / f"{index:04d}"
            folder.mkdir(parents=True)
            save_image(folder / "original-copy.png", crop(aligned, region.reference_bounds))
            save_image(
                folder / "original-reference.png", crop(engine.reference, region.reference_bounds)
            )
            section = next(s for s in template.sections if s.id == region.section)
            x0, y0, x1, y1 = region.reference_bounds
            sampling = np.zeros((y1 - y0, x1 - x0), np.uint8)
            for choice in range(1, section.choices + 1):
                roi, interior = bubble_roi(section, region.question, choice)
                target = (
                    slice(roi[0].start - y0, roi[0].stop - y0),
                    slice(roi[1].start - x0, roi[1].stop - x0),
                )
                sampling[target] |= (interior & (engine.gray_reference[roi] > 200)).astype(
                    np.uint8
                ) * 255
            save_image(folder / "sampling.png", sampling)
        gray = normalized_gray(aligned)
        report["historical_quality_at_fixed_geometry"] = {
            s.id: engine.section_quality(gray, valid.astype(np.uint8) * 255, inverse, s)
            for s in template.sections
        }
        for name in VARIANTS:
            pair = prepare_pair(
                engine.reference, aligned, valid, template, transform, source.shape[:2], name
            )
            questions = [
                {
                    "section": s.id,
                    "question": q,
                    "scores": measure_question(pair, engine.gray_reference, s, q),
                }
                for s in template.sections
                for q in range(1, s.questions + 1)
            ]
            report["variants"][name] = {
                "status": "measured_not_decided",
                "processing": pair.diagnostics,
                "sections": {s.id: print_residuals(pair, s) for s in template.sections},
                "questions": questions,
                "comparison": compare_signals(questions, labels, report["geometry_comparison"]),
            }
            # Export exact inputs and residuals, never a denoised substitute for the original.
            delta = np.maximum(pair.reference.astype(float) - pair.copy, 0).astype(np.uint8)
            for index, region in enumerate(regions):
                folder = output / "questions" / f"{index:04d}"
                for suffix, image in (
                    ("reference", pair.reference),
                    ("copy", pair.copy),
                    ("residual", delta),
                    ("valid", pair.valid.astype(np.uint8) * 255),
                ):
                    save_image(
                        folder / f"{name}-{suffix}.png", crop(image, region.reference_bounds)
                    )
    baseline = report["variants"]["normalized"]["comparison"]
    for variant in report["variants"].values():
        variant["change_vs_normalized"] = _paired_change(baseline, variant["comparison"])
    _write_review(output, report)
    report["artifact_sha256"] = {
        p.relative_to(output).as_posix(): digest(p)
        for p in sorted(output.rglob("*"))
        if p.is_file()
    }
    report["complete"] = True
    write_json(output / "report.json", report)
    return report


def _write_review(output: Path, report: dict) -> None:
    lines = [
        "# S04 — Comparaison photographique",
        "",
        "Essai de développement. Aucun entraînement, aucune décision ni activation web.",
        "",
        "Même géométrie et même masque de mesure pour toutes les variantes.",
        "Résidu : intensité positive référence − photo. Moins de résidu sur les vides est souhaitable ;",
        "en perdre sur les marques peut être une régression. Le classement ne valide pas une réponse.",
        "",
        "| Variante | Questions évaluées | Résidu médian vide | Résidu médian marqué | Marque unique en tête* |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, variant in report["variants"].items():
        metrics = variant["comparison"]
        signals = metrics["label_signals"]
        values = [signals[key]["median"] for key in ("empty", "marked")]
        empty, marked = ["—" if v is None else f"{v:.2f}" for v in values]
        lines.append(
            f"| {name} | {metrics['evaluated_questions']}/{metrics['annotated_questions']} | "
            f"{empty} | {marked} | {metrics['single_mark_positive_margin']}/{metrics['single_mark_margin']['count']} |"
        )
    lines.extend(
        [
            "",
            "*Comparaison exploratoire du signal sur les questions humaines à réponse unique ;",
            "ce n’est ni une prédiction automatique ni un taux de précision. Les blancs et ambiguïtés",
            "restent dans les mesures séparées ; aucune annotation manquante n’est un blanc.",
            "",
        ]
    )
    if report.get("registration_error"):
        lines.append(f"Refus géométrique : {report['registration_error']}")
    lines.append("## Changements appariés face à la normalisation existante")
    for name, variant in report["variants"].items():
        change = variant["change_vs_normalized"]
        ranking = change["single_mark_ranking_change"]
        changes = change["signal_change_by_label"]
        display = ", ".join(
            f"{label} : {changes[label]['median']:+.2f}"
            if changes[label]["median"] is not None
            else f"{label} : non mesuré"
            for label in ("empty", "marked", "ambiguous")
        )
        lines.append(
            f"- {name} : {change['paired_questions']} questions communes ; variation médiane du signal {display}. "
            f"Classement amélioré/régressé/inchangé : {ranking['improved']}/{ranking['regressed']}/{ranking['unchanged']}."
        )
    lines.append("## Contrôles d’impression et replis")
    for name, variant in report["variants"].items():
        for sid, metrics in variant["sections"].items():
            error = metrics["mae"]
            display = "absent" if error is None else f"{error:.2f}"
            fit = variant.get("processing", {}).get("contrast", {}).get(sid)
            suffix = "" if fit is None else f" ; contraste {fit['status']} ({fit['reason']})"
            lines.append(f"- {name}, grille {sid} : écart impression {display}{suffix}.")
    lines.extend(["", "## Contrôles historiques à géométrie fixe"])
    for sid, quality in report.get("historical_quality_at_fixed_geometry", {}).items():
        lines.append(f"- Grille {sid} : {', '.join(quality['issues']) or 'aucun refus local'}.")
    lines.extend(
        [
            "",
            "Les mesures expérimentales ne lèvent aucun de ces refus. Le résultat historique est conservé.",
            "La contenance des centres dans un cadre humain ne prouve pas le positionnement précis de chaque case.",
            "Les originaux restent inchangés ; les agrandissements ne créent aucun détail.",
        ]
    )
    summary = "\n".join(lines) + "\n"
    (output / "summary.md").write_text(summary, encoding="utf-8")
    cards = []
    for index, q in enumerate(report["variants"]["normalized"]["questions"]):
        prefix = f"questions/{index:04d}/"
        rows = [
            "<div><strong>Originaux recalés</strong>"
            f'<img src="{prefix}original-reference.png" alt="Référence originale">'
            f'<img src="{prefix}original-copy.png" alt="Photo originale recalée">'
            f'<img src="{prefix}sampling.png" alt="Masque de mesure fixe"></div>'
        ]
        for name in VARIANTS:
            images = "".join(
                f'<img loading="lazy" src="{prefix}{name}-{suffix}.png" alt="{name} {suffix}">'
                for suffix in ("reference", "copy", "residual", "valid")
            )
            rows.append(f"<div><strong>{name}</strong>{images}</div>")
        cards.append(
            f"<details><summary>Section {html.escape(q['section'])} · Question {q['question']}</summary>"
            f"<p>Référence · photo · résidu (clair = plus sombre sur la photo) · pixels valides</p>{''.join(rows)}</details>"
        )
    (output / "review.html").write_text(
        '<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        "<title>S04 — Comparaison photographique</title><style>body{font:16px sans-serif;margin:24px}"
        "pre{white-space:pre-wrap}details{border-top:1px solid #aaa;padding:16px 0}details div{display:flex;"
        "align-items:start;gap:16px;flex-wrap:wrap;margin:16px 0}strong{width:200px}"
        "img{height:240px;max-width:100%;object-fit:contain}summary{cursor:pointer}</style>"
        f"<h1>Comparaison photographique S04</h1><pre>{html.escape(summary)}</pre>{''.join(cards)}</html>",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        run_photometric_trial(args.template, args.source, args.output, args.manifest)
    except (ValueError, OSError, KeyError, TypeError, cv2.error) as exc:
        parser.exit(2, f"Photometric trial failed: {exc}\n")
    print(f"Photometric trial written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
