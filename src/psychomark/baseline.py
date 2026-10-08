"""Offline, private baseline replay. No answer key, threshold change or model training."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import platform
import sys
from collections import Counter
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

import cv2
import numpy as np

from .config import Exam, read_config, write_json
from .engine import Engine, bubble_roi
from .images import normalized_gray, read_image, save_image
from .regions import crop, question_region


def digest(path: Path) -> str:
    """Hash file contents, without exposing a potentially identifying filename."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(result: dict) -> dict:
    """Report coverage for every expected question, including rejected sections/pages."""
    counts = Counter(answer["status"] for answer in result["answers"])
    total = sum(counts.values())
    automatic = counts["single"] + counts["blank"]
    return {
        "questions": total,
        "status_counts": dict(sorted(counts.items())),
        "automatic": automatic,
        "automatic_fraction": automatic / total if total else None,
        "review": total - automatic,
        "page_rejected": result["status"] == "unreadable",
        "automatic_errors": None,
        "automatic_error_rate": None,
        "ground_truth": "not_annotated",
        "accuracy_note": "Aucune précision mesurée sans annotation humaine indépendante.",
    }


def compare_results(current: dict, previous: dict) -> dict:
    """Compare engine observations, never treat a previous prediction as human truth."""
    for field in ("template_sha256", "reference_sha256", "exam"):
        if current.get(field) != previous.get(field):
            raise ValueError(f"Comparison requires identical {field}")

    def indexed(result: dict) -> dict:
        answers = result["answers"]
        index = {(a["section"], a["question"]): a for a in answers}
        if len(index) != len(answers):
            raise ValueError("Duplicate question in comparison result")
        return index

    before, after = indexed(previous), indexed(current)
    if before.keys() != after.keys():
        raise ValueError("Comparison requires identical question selections")
    decision_fields = ("status", "answer", "candidates", "reason")
    changed = [
        {"section": sid, "question": q}
        for sid, q in after
        if any(before[sid, q][f] != after[sid, q][f] for f in decision_fields)
    ]
    return {
        "kind": "historical_predictions_not_ground_truth",
        "source_identity": "unverified_no_source_fingerprint",
        "decision_changes": changed,
        "scores_identical": all(before[k]["scores"] == after[k]["scores"] for k in after),
        "diagnostics_identical": current["diagnostics"] == previous["diagnostics"],
        "page_status_identical": current["status"] == previous["status"],
    }


def _verify_previous_source(previous_path: Path, previous: dict, source_digest: str) -> str:
    fingerprints = []
    if previous.get("file_sha256"):
        fingerprints.append(previous["file_sha256"])
    companion = previous_path.parent / "report.json"
    if companion.is_file():
        metadata = json.loads(companion.read_text(encoding="utf-8"))
        if metadata.get("purpose") == "development_baseline_not_independent_evaluation":
            if metadata.get("artifact_sha256", {}).get(previous_path.name) != digest(previous_path):
                raise ValueError("Previous result does not match its companion report")
            fingerprints.append(metadata["provenance"]["input_sha256"])
    if not fingerprints:
        return "unverified_no_source_fingerprint"
    if any(value != source_digest for value in fingerprints):
        raise ValueError("Comparison requires the same source image fingerprint")
    return "verified_source_bytes"


def _export_regions(engine: Engine, image: np.ndarray, result: dict, output: Path) -> list[dict]:
    registration = result["diagnostics"].get("registration")
    if registration is None:
        return []  # Never fabricate coordinates when alignment failed.
    transform = np.asarray(registration["input_to_reference"], dtype=np.float64)
    inverse = np.linalg.inv(transform)
    size = (engine.template.width, engine.template.height)
    # Reuse the exact recorded transform: no second ORB/RANSAC registration.
    aligned = cv2.warpPerspective(image, transform, size, borderValue=(255, 255, 255))
    # Normalization is page-wide. Applying it independently to crops would change values.
    normalized = normalized_gray(aligned)
    valid = cv2.warpPerspective(
        np.full(image.shape[:2], 255, np.uint8), transform, size, flags=cv2.INTER_NEAREST
    )
    save_image(output / "valid.png", valid)
    sections = {section.id: section for section in engine.template.sections}
    regions = []
    for index, answer in enumerate(result["answers"], 1):
        section = sections[answer["section"]]
        region = question_region(section, answer["question"], inverse, valid, image.shape[:2])
        directory = output / "questions" / f"{index:04d}"
        directory.mkdir(parents=True)
        raw = crop(aligned, region.reference_bounds)
        reference = crop(engine.reference, region.reference_bounds)
        mask = crop(valid, region.reference_bounds)
        interior_mask = np.zeros(mask.shape, np.uint8)
        sampling_mask = np.zeros(mask.shape, np.uint8)
        overlay = raw.copy()
        x0, y0, _, _ = region.reference_bounds
        for choice in region.choices:
            roi, interior = bubble_roi(section, answer["question"], choice.choice)
            target = (
                slice(roi[0].start - y0, roi[0].stop - y0),
                slice(roi[1].start - x0, roi[1].stop - x0),
            )
            interior_mask[target] |= interior.astype(np.uint8) * 255
            sampling_mask[target] |= (interior & (engine.gray_reference[roi] > 200)).astype(
                np.uint8
            ) * 255
            cx, cy = choice.reference_center
            cv2.ellipse(
                overlay,
                (round(cx - x0), round(cy - y0)),
                tuple(round(r) for r in section.bubble_radius),
                0,
                0,
                360,
                (210, 100, 0),
                1,
            )
        assets = {}
        images = {
            "copy": raw,
            "reference": reference,
            "valid": mask,
            "overlay": overlay,
            "interior": interior_mask,
            "sampling": sampling_mask,
            "normalized_copy": crop(normalized, region.reference_bounds),
            "normalized_reference": crop(engine.gray_reference, region.reference_bounds),
        }
        source_crop = crop(image, region.source_bounds)
        if source_crop.size:
            images["source"] = source_crop
        for name, data in images.items():
            path = directory / f"{name}.png"
            save_image(path, data)
            assets[name] = path.relative_to(output).as_posix()
        regions.append({**region.model_dump(), "assets": assets})
    return regions


def _write_review(output: Path, report: dict, result: dict, regions: list[dict]) -> None:
    rows = []
    answers = {(a["section"], a["question"]): a for a in result["answers"]}
    for region in regions:
        sid, q = region["section"], region["question"]
        assets = region["assets"]
        pictures = "".join(
            f'<figure><img src="{html.escape(assets[key], quote=True)}" '
            f'alt="{label}" style="width:{3 * (region["reference_bounds"][2] - region["reference_bounds"][0])}px">'
            f"<figcaption>{label}</figcaption></figure>"
            for key, label in (
                ("reference", "Référence"),
                ("copy", "Photo recalée"),
                ("overlay", "Zones lues"),
            )
        )
        links = " ".join(
            f'<a href="{html.escape(value, quote=True)}">{html.escape(key)}</a>'
            for key, value in assets.items()
        )
        observation = html.escape(json.dumps(answers[sid, q], ensure_ascii=False, indent=2))
        rows.append(
            f"<article><h2>Section {html.escape(sid)} · Question {q}</h2>"
            f'<div class="images">{pictures}</div><p>Fichiers natifs : {links}</p>'
            "<p>Lecture humaine : à renseigner. Placement : à vérifier.</p>"
            f"<details><summary>Prédiction historique — ouvrir après votre lecture</summary>"
            f"<pre>{observation}</pre></details></article>"
        )
    summary = report["summary"]
    document = (
        '<!doctype html><html lang="fr"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" '
        "content=\"default-src 'none'; img-src 'self'; style-src 'unsafe-inline'\">"
        "<title>PsychoMark — référence de comparaison</title><style>"
        "body{font:16px system-ui;margin:2rem;max-width:1100px;background:#fff;color:#222}"
        "article{border-top:1px solid #bbb;padding:1rem 0}.images{display:flex;gap:1rem;overflow:auto}"
        "figure{margin:0}img{image-rendering:pixelated}pre{white-space:pre-wrap}"
        "</style><h1>Référence de comparaison du moteur</h1>"
        "<p>Rapport privé. Agrandissements ×3 sans création de détail. "
        "Les positions exportées sont celles du moteur, pas une validation humaine.</p>"
        f"<p>{summary['questions']} questions ; {summary['automatic']} lectures automatiques ; "
        f"{summary['review']} à revoir. Aucune précision mesurée.</p>"
        "<p>Comparer les marques et leur position avant d’ouvrir la prédiction. "
        "Les observations humaines restent à saisir dans annotations.pending.json ; "
        "ce rapport ne les enregistre pas.</p>"
        + ("".join(rows) if rows else "<p>Alignement impossible : aucun extrait attribué.</p>")
        + "</html>"
    )
    (output / "review.html").write_text(document, encoding="utf-8")


def _write_summary(output: Path, report: dict, result: dict, engine: Engine) -> None:
    summary = report["summary"]
    lines = [
        "# Point de comparaison du moteur",
        "",
        "Rapport privé de développement ; les réponses humaines restent à confirmer.",
        "",
        f"- Questions attendues : **{summary['questions']}**.",
        f"- Lectures automatiques : **{summary['automatic']}**.",
        f"- Questions à revoir : **{summary['review']}**.",
        "- Précision : **non mesurée**, aucune annotation humaine validée.",
        "",
        "[Examiner les questions](review.html) · [Mesures](report.json) · [Résultat brut](result.json)",
        "",
        "## Positionnement et contrôles",
        "",
    ]
    registration = result["diagnostics"].get("registration")
    if registration:
        lines += [
            f"Alignement global réussi : {registration['inliers']} repères retenus ; "
            f"erreur médiane {registration['median_error_px']} pixels dans la référence.",
            "Cela ne valide pas le positionnement de chaque case.",
            "",
            "| Section | Taille minimale d’une case dans la photo (px) | Correspondance du cadre | Motifs de refus |",
            "|---|---:|---:|---|",
        ]
        for sid, quality in result["diagnostics"]["sections"].items():
            lines.append(
                f"| {sid} | {quality['min_source_bubble_diameter']} | "
                f"{quality['frame_support']} | {', '.join(quality['issues']) or 'Aucun'} |"
            )
        thresholds = engine.template.thresholds
        lines += [
            "",
            f"Seuils historiques inchangés : taille minimale {thresholds.min_source_bubble_diameter} px ; "
            f"correspondance minimale du cadre {thresholds.min_frame_support}.",
            "Une case agrandie à l’écran ne contient pas plus de détail que dans la photo.",
        ]
    else:
        lines.append("Alignement impossible : aucune position de question n’a été fabriquée.")
    if report["comparison"] is not None:
        comparison = report["comparison"]
        lines += [
            "",
            "## Comparaison avec le diagnostic précédent",
            "",
            f"Décisions différentes : {len(comparison['decision_changes'])}.",
            f"Diagnostics strictement identiques : {comparison['diagnostics_identical']}.",
            f"Identité de l’image source : {comparison['source_identity']}.",
            "Une différence numérique de transformation peut exister sans changer les décisions.",
            "La prédiction précédente ne constitue pas une vérité humaine.",
        ]
    lines += [
        "",
        "## Suite",
        "",
        "Vérifier les positions puis annoter les marques visibles. Les régions rejetées restent "
        "disponibles à l’inspection, sans devenir des réponses acceptées.",
        "Le fichier annotations.pending.json est une préparation ; aucune saisie automatique "
        "ni validation humaine n’a été inventée.",
        "",
    ]
    (output / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def run_baseline(
    template_path: Path,
    image_path: Path,
    output: Path,
    exam: Exam | None = None,
    previous_path: Path | None = None,
) -> dict:
    """Replay a single image into a new private folder, preserving engine JSON verbatim.

    This is development tooling, not an upload route. PDF pages must first be decoded
    explicitly. A refusal is a valid measurement, not a failed tool execution.
    """
    if output.exists():
        raise ValueError("Output must be a new directory; baseline artifacts are immutable")
    engine = Engine.from_file(template_path)
    image = read_image(image_path)
    if exam:
        exam.validate_for(engine.template)
    started = perf_counter()
    result, preview = engine.analyze(image, exam)
    duration = perf_counter() - started
    comparison = None
    if previous_path is not None:
        previous = json.loads(previous_path.read_text(encoding="utf-8"))
        comparison = compare_results(result, previous)
        comparison["source_identity"] = _verify_previous_source(
            previous_path, previous, digest(image_path)
        )
    output.mkdir(parents=True)
    write_json(output / "result.json", result)
    write_json(output / "template.json", engine.template.model_dump())
    write_json(output / "selection.json", result["exam"])
    save_image(output / "annotated.png", preview)
    regions = _export_regions(engine, image, result, output)
    registration = result["diagnostics"].get("registration")
    write_json(
        output / "regions.json",
        {
            "schema_version": 1,
            "coordinate_system": "decoded_source_and_reference_pixel_centers",
            "bounds_convention": "x0_y0_inclusive_x1_y1_exclusive",
            "source_size": [image.shape[1], image.shape[0]],
            "reference_size": [engine.template.width, engine.template.height],
            "input_to_reference": registration["input_to_reference"] if registration else None,
            "reference_to_input": np.linalg.inv(registration["input_to_reference"]).tolist()
            if registration
            else None,
            "local_alignment": None,
            "valid_mask": "valid.png" if registration else None,
            "questions": regions,
        },
    )
    write_json(
        output / "annotations.pending.json",
        {
            "schema_version": 1,
            "state": "pending_human_review",
            "source_sha256": digest(image_path),
            "template_sha256": engine.template_digest,
            "questions": [
                {
                    "section": a["section"],
                    "question": a["question"],
                    "geometry_valid": None,
                    "status": None,
                    "choices": None,
                    "reviewer": None,
                    "notes": "",
                }
                for a in result["answers"]
            ],
        },
    )
    source_root = Path(__file__).parent
    report = {
        "schema_version": 1,
        "purpose": "development_baseline_not_independent_evaluation",
        "reader": "historical_classic",
        "preprocessing": "images.normalized_gray",
        "ml_model": None,
        "provenance": {
            "input_sha256": digest(image_path),
            "template_file_sha256": digest(template_path),
            "template_sha256": engine.template_digest,
            "reference_sha256": engine.template.reference_sha256,
            "previous_result_sha256": digest(previous_path) if previous_path else None,
            "code_sha256": {p.name: digest(p) for p in sorted(source_root.glob("*.py"))},
            "versions": {
                "python": platform.python_version(),
                **{
                    name: version(name)
                    for name in (
                        "psychomark",
                        "numpy",
                        "opencv-python-headless",
                        "Pillow",
                        "pydantic",
                    )
                },
            },
            "opencv_threads": cv2.getNumThreads(),
            "ransac_seed": 0,
        },
        "timing": {"analyze_seconds": round(duration, 4), "includes_engine_initialization": False},
        "summary": summarize(result),
        "comparison": comparison,
        "complete": True,
    }
    _write_review(output, report, result, regions)
    _write_summary(output, report, result, engine)
    # Inventory detects changed crops/annotations without storing private image data in Git.
    report["artifact_sha256"] = {
        p.relative_to(output).as_posix(): digest(p)
        for p in sorted(output.rglob("*"))
        if p.is_file()
    }
    write_json(output / "report.json", report)  # Last file is the completion marker.
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--exam", type=Path)
    parser.add_argument("--compare", type=Path, help="Previous extraction JSON, not an answer key")
    args = parser.parse_args(argv)
    cv2.setNumThreads(2)
    try:
        report = run_baseline(
            args.template,
            args.image,
            args.output,
            read_config(args.exam, Exam) if args.exam else None,
            args.compare,
        )
    except (ValueError, OSError, KeyError, TypeError, cv2.error, np.linalg.LinAlgError) as exc:
        print(f"Baseline error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
