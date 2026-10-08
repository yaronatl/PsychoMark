"""S05 offline reader comparison, with explicit errors, coverage and abstentions."""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from .baseline import digest
from .classic_reader import PARAMETERS, read_classic_question
from .config import write_json
from .engine import Engine, bubble_roi, edge_energy
from .geometry_trial import compare_geometry, geometry_observations
from .images import normalized_gray, read_image, save_image
from .photometric_trial import _observations
from .photometry import project_photo
from .regions import crop, question_region
from .registration import Registrar, RegistrationError


def evaluate_reader(answers: list[dict], labels: dict, geometry: dict) -> dict:
    """Report development error/coverage without excluding unreadable labelled questions.

    A single/blank on a human ambiguity is an automatic error. Automatic answers with
    unconfirmed/outside geometry are reported as unverified, never credited correct.
    State agreement for review cases is not evidence of correctly read individual marks.
    """
    indexed = {(a["section"], a["question"]): a for a in answers}
    located = {(o["section"], o["question"]): o for o in geometry["observations"]}
    rows = []
    for key, human in labels.items():
        answer = indexed.get(key)
        if answer is None:
            raise ValueError("Missing question in reader output")
        auto = answer["status"] in {"single", "blank"}
        geo = located.get(key, {}).get("all_choice_centers_inside", False)
        expected = [i for i, m in enumerate(human["marks"], 1) if m == "marked"]
        correct = None
        if auto and geo:
            correct = answer["status"] == human["status"] and (
                answer["status"] == "blank" or expected == [answer["answer"]]
            )
        rows.append(
            {
                "section": key[0],
                "question": key[1],
                "human_status": human["status"],
                "predicted_status": answer["status"],
                "answer": answer["answer"],
                "automatic": auto,
                "geometry_comparable": bool(geo),
                "correct": correct,
            }
        )

    def counts(items: list[dict]) -> dict:
        automatic = sum(r["automatic"] for r in items)
        verified = sum(r["correct"] is not None for r in items)
        errors = sum(r["correct"] is False for r in items)
        return {
            "annotated_questions": len(items),
            "automatic": automatic,
            "review": len(items) - automatic,
            "predicted_status_counts": dict(Counter(r["predicted_status"] for r in items)),
            "unverified_automatic": automatic - verified,
            "correct_automatic": verified - errors,
            "incorrect_automatic": errors,
            "coverage": automatic / len(items) if items else None,
            "error_rate_on_geometry_comparable_automatic": errors / verified if verified else None,
        }

    return dict(
        counts(rows),
        independent_test=False,
        by_human_status={
            s: counts([r for r in rows if r["human_status"] == s])
            for s in ("single", "blank", "multiple", "uncertain", "unreadable")
        },
        observations=rows,
    )


def run_reader_trial(
    template_path: Path, source_path: Path, output: Path, manifest_path: Path | None = None
) -> dict:
    """Compare historical, fixed-geometry legacy and candidate without changing Engine."""
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
    historical, _ = engine.analyze(source)
    write_json(output / "historical-result.json", historical)
    report = {
        "schema_version": 1,
        "purpose": "reader_development_trial_no_web_activation",
        "source_sha256": digest(source_path),
        "template_sha256": digest(template_path),
        "reference_sha256": template.reference_sha256,
        "corpus": corpus,
        "parameters": PARAMETERS,
        "preprocessing": "existing_normalized_gray",
        "versions": {"opencv": cv2.__version__, "numpy": np.__version__},
        "code_sha256": {
            name: digest(Path(__file__).with_name(name))
            for name in (
                "reader_trial.py",
                "classic_reader.py",
                "engine.py",
                "registration.py",
                "images.py",
                "regions.py",
                "photometry.py",
                "photometric_trial.py",
                "geometry_trial.py",
                "config.py",
            )
        },
        "registration": None,
        "quality": {},
        "complete": False,
    }
    legacy, candidate, regions = [], [], []
    try:
        registrar = Registrar(normalized_gray(engine.reference), template)
        _, _, _, diagnostic = registrar.align(
            cv2.cvtColor(normalized_gray(source), cv2.COLOR_GRAY2BGR)
        )
    except (RegistrationError, ValueError) as exc:
        report["registration_error"] = str(exc)
        for s in template.sections:
            for q in range(1, s.questions + 1):
                legacy.append(engine.unreadable(s.id, q, "registration_failed"))
                candidate.append(engine.unreadable(s.id, q, "registration_failed"))
    else:
        report["registration"] = diagnostic
        transform = np.asarray(diagnostic["input_to_reference"])
        inverse = np.linalg.inv(transform)
        aligned, available = project_photo(source, transform, (template.width, template.height))
        valid = available.astype(np.uint8) * 255
        gray = normalized_gray(aligned)
        raw_gray = cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY)
        edges = edge_energy(gray)
        for s in template.sections:
            quality = engine.section_quality(gray, valid, inverse, s)
            report["quality"][s.id] = quality
            for q in range(1, s.questions + 1):
                region = question_region(s, q, inverse, valid, source.shape[:2])
                regions.append(region.model_dump())
                old = (
                    engine.unreadable(s.id, q, ",".join(quality["issues"]))
                    if quality["issues"]
                    else engine.read_question(gray, valid, edges, s, q)
                )
                new, masks = read_classic_question(
                    engine, gray, valid, edges, s, q, quality, raw_gray
                )
                legacy.append(old)
                candidate.append(new)
                folder = output / "questions" / f"{len(candidate):04d}"
                folder.mkdir(parents=True)
                bounds = region.reference_bounds
                for name, image in (
                    ("copy", aligned),
                    ("reference", engine.reference),
                    ("normalized", gray),
                ):
                    save_image(folder / f"{name}.png", crop(image, bounds))
                mask = np.zeros(crop(gray, bounds).shape, np.uint8)
                for choice, area in enumerate(masks, 1):
                    roi, _ = bubble_roi(s, q, choice)
                    target = (
                        slice(roi[0].start - bounds[1], roi[0].stop - bounds[1]),
                        slice(roi[1].start - bounds[0], roi[1].stop - bounds[0]),
                    )
                    mask[target] |= area.astype(np.uint8) * 255
                save_image(folder / "sampling.png", mask)
    geometry = compare_geometry(regions, boxes)
    report["geometry_comparison"] = geometry
    write_json(output / "regions.json", regions)
    # Historical geometry must not borrow the candidate's successful registration.
    historical_regions = []
    old_registration = historical["diagnostics"].get("registration")
    if old_registration is not None:
        old_transform = np.asarray(old_registration["input_to_reference"])
        _, old_valid = project_photo(source, old_transform, (template.width, template.height))
        historical_regions = [
            question_region(
                s,
                q,
                np.linalg.inv(old_transform),
                old_valid.astype(np.uint8) * 255,
                source.shape[:2],
            ).model_dump()
            for s in template.sections
            for q in range(1, s.questions + 1)
        ]
    report["variants"] = {}
    for name, answers, geo in (
        ("historical", historical["answers"], compare_geometry(historical_regions, boxes)),
        ("normalized_legacy", legacy, geometry),
        ("classic_v1", candidate, geometry),
    ):
        report["variants"][name] = {
            "answers": answers,
            "status_counts": dict(Counter(a["status"] for a in answers)),
            "evaluation": evaluate_reader(answers, labels, geo),
        }
    old_rows = report["variants"]["normalized_legacy"]["evaluation"]["observations"]
    new_rows = report["variants"]["classic_v1"]["evaluation"]["observations"]
    report["paired_changes"] = {
        "automatic_errors_added": sum(
            n["correct"] is False and o["correct"] is not False
            for o, n in zip(old_rows, new_rows, strict=True)
        ),
        "automatic_errors_removed": sum(
            o["correct"] is False and n["correct"] is not False
            for o, n in zip(old_rows, new_rows, strict=True)
        ),
        "review_to_correct_automatic": sum(
            not o["automatic"] and n["correct"] is True
            for o, n in zip(old_rows, new_rows, strict=True)
        ),
        "correct_automatic_to_review": sum(
            o["correct"] is True and not n["automatic"]
            for o, n in zip(old_rows, new_rows, strict=True)
        ),
    }
    _write_report(output, report)
    report["artifact_sha256"] = {
        p.relative_to(output).as_posix(): digest(p)
        for p in sorted(output.rglob("*"))
        if p.is_file()
    }
    report["complete"] = True
    write_json(output / "report.json", report)
    return report


def _write_report(output: Path, report: dict) -> None:
    lines = [
        "# S05 — Lecteur classique expérimental",
        "",
        "Données de développement uniquement. Aucun entraînement ni activation web.",
        "Les taux portent sur cette acquisition connue, pas sur de nouvelles copies.",
        "",
        "| Variante | Annotations | Automatiques | Correctes | Erreurs | Non vérifiables | À revoir |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, data in report["variants"].items():
        e = data["evaluation"]
        lines.append(
            f"| {name} | {e['annotated_questions']} | {e['automatic']} | {e['correct_automatic']} | {e['incorrect_automatic']} | {e['unverified_automatic']} | {e['review']} |"
        )
    lines.extend(["", "## Répartition du candidat par annotation humaine"])
    for status, e in report["variants"]["classic_v1"]["evaluation"]["by_human_status"].items():
        lines.append(
            f"- {status} : {e['annotated_questions']} annotations, {e['correct_automatic']} automatiques correctes, {e['incorrect_automatic']} erreurs automatiques, {e['review']} à revoir, {e['unverified_automatic']} non vérifiables."
        )
        lines.append(
            f"  États prédits : {json.dumps(e['predicted_status_counts'], ensure_ascii=False)}"
        )
    lines.extend(
        [
            "",
            "## Changements face au lecteur historique à géométrie identique",
            json.dumps(report["paired_changes"], ensure_ascii=False),
            "",
            "Les refus de géométrie, de résolution, de cadrage et de netteté restent actifs.",
            "Une marque dominante ne suffit pas : les autres choix sont contrôlés séparément.",
            "Une ambiguïté humaine convertie en réponse automatique compte comme erreur.",
        ]
    )
    summary = "\n".join(lines) + "\n"
    (output / "summary.md").write_text(summary, encoding="utf-8")
    cards = []
    for index, answer in enumerate(report["variants"]["classic_v1"]["answers"], 1):
        folder = f"questions/{index:04d}"
        if not (output / folder).exists():
            continue
        images = "".join(
            f'<figure><figcaption>{name}</figcaption><img loading="lazy" src="{folder}/{name}.png" alt="{name}"></figure>'
            for name in ("reference", "copy", "normalized", "sampling")
        )
        cards.append(
            f"<details><summary>{html.escape(answer['section'])} · Q{answer['question']} · {answer['status']}</summary><div>{images}</div><pre>{html.escape(json.dumps(answer, indent=2))}</pre></details>"
        )
    (output / "review.html").write_text(
        '<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        "<title>S05 — Lecteur classique</title><style>body{font:16px sans-serif;margin:24px}pre{white-space:pre-wrap}"
        "details{border-top:1px solid #aaa;padding:12px}details div{display:flex;gap:16px;flex-wrap:wrap}"
        "figure{margin:0}img{height:240px;border:1px solid #aaa;max-width:100%;object-fit:contain}</style>"
        f"<h1>Comparaison S05</h1><pre>{html.escape(summary)}</pre>{''.join(cards)}</html>",
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
        run_reader_trial(args.template, args.source, args.output, args.manifest)
    except (ValueError, OSError, KeyError, TypeError, cv2.error) as exc:
        parser.exit(2, f"Reader trial failed: {exc}\n")
    print(f"Reader trial written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
