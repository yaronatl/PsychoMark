"""Offline S03 geometry comparison. Does not grade, train, or change the web engine."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

import cv2
import numpy as np

from .baseline import digest
from .config import Exam, Template, read_config, write_json
from .engine import Engine
from .images import normalized_gray, read_image, save_image
from .local_registration import refine_section
from .regions import crop, project_points, question_region
from .registration import Registrar, RegistrationError


def geometry_observations(
    manifest_path: Path, template_path: Path, source_path: Path, source_shape: tuple[int, int]
) -> tuple[dict[tuple[str, int], list[int]], dict]:
    """Read confirmed source rectangles only; mark labels never reach registration.

    This exploratory runner accepts development data only. Partial annotations are
    usable; missing geometry stays missing, and an automatic confirmation without a
    manual rectangle is not an independent geometric reference.
    """
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1 or manifest.get("split") != "development":
        raise ValueError("Geometry trials require a version-1 development corpus")
    template = read_config(template_path, Template)
    if manifest["provenance"]["snapshot_template_sha256"] != digest(template_path):
        raise ValueError("Corpus/template snapshot checksum mismatch")
    images = manifest["images"]
    if images["source"]["sha256"] != digest(source_path):
        raise ValueError("Corpus/source checksum mismatch")
    if images["reference"]["sha256"] != template.reference_sha256:
        raise ValueError("Corpus/reference checksum mismatch")
    height, width = source_shape
    if manifest["source_size"] != [width, height]:
        raise ValueError("Corpus source dimensions mismatch")
    sections = {s.id: s for s in template.sections}
    boxes, seen = {}, set()
    annotated = 0
    for question in manifest["questions"]:
        key = (question["section"], question["question"])
        section = sections.get(key[0])
        if (
            key in seen
            or section is None
            or type(key[1]) is not int
            or not 1 <= key[1] <= section.questions
        ):
            raise ValueError("Invalid or duplicate corpus question")
        seen.add(key)
        if question["choices"] != section.choices:
            raise ValueError("Corpus choice count mismatch")
        annotation = question.get("annotation")
        if annotation is None:
            continue
        annotated += 1
        bounds = annotation.get("manual_bounds")
        if bounds is None or annotation.get("geometry") != "confirmed":
            continue
        if (
            not isinstance(bounds, list)
            or len(bounds) != 4
            or any(type(v) is not int for v in bounds)
            or not 0 <= bounds[0] < bounds[2] <= width
            or not 0 <= bounds[1] < bounds[3] <= height
        ):
            raise ValueError("Invalid human source rectangle")
        boxes[key] = bounds
    return boxes, {
        "annotated_questions": annotated,
        "confirmed_manual_rectangles": len(boxes),
        "total_questions": len(seen),
        "split": "development",
        "manifest_sha256": digest(manifest_path),
    }


def compare_geometry(regions: list[dict], boxes: dict[tuple[str, int], list[int]]) -> dict:
    """Compare independent rectangles, never equate containment with answer accuracy."""
    indexed = {(r["section"], r["question"]): r for r in regions}
    observations = []
    for (section, question), b in boxes.items():
        r = indexed.get((section, question))
        observation = {
            "section": section,
            "question": question,
            "human_bounds": b,
            "located": r is not None,
        }
        if r is not None:
            centers = np.array([c["source_center"] for c in r["choices"]])
            inside = [bool(b[0] <= x < b[2] and b[1] <= y < b[3]) for x, y in centers]
            observation.update(
                all_choice_centers_inside=all(inside),
                center_distance_source_px=float(
                    np.linalg.norm(centers.mean(axis=0) - [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2])
                ),
            )
        observations.append(observation)
    distances = [o["center_distance_source_px"] for o in observations if o["located"]]
    return {
        "human_rectangles": len(boxes),
        "located": len(distances),
        "all_choice_centers_inside": sum(
            o.get("all_choice_centers_inside", False) for o in observations
        ),
        "median_center_distance_source_px": float(np.median(distances)) if distances else None,
        "answer_accuracy": None,
        "observations": observations,
    }


def _warp(
    source: np.ndarray, transform: np.ndarray, template: Template
) -> tuple[np.ndarray, np.ndarray]:
    size = (template.width, template.height)
    return (
        cv2.warpPerspective(source, transform, size, borderValue=(255, 255, 255)),
        cv2.warpPerspective(
            np.full(source.shape[:2], 255, np.uint8), transform, size, flags=cv2.INTER_NEAREST
        ),
    )


def _regions(
    source: np.ndarray,
    aligned: np.ndarray,
    valid: np.ndarray,
    inverse: np.ndarray,
    section,
    directory: Path,
) -> list[dict]:
    directory.mkdir(parents=True, exist_ok=True)
    regions = []
    for question in range(1, section.questions + 1):
        region = question_region(section, question, inverse, valid, source.shape[:2])
        save_image(directory / f"q{question:03d}.png", crop(aligned, region.reference_bounds))
        regions.append(region.model_dump())
    return regions


def run_geometry_trial(
    template_path: Path, source_path: Path, output: Path, manifest_path: Path | None = None
) -> dict:
    """Compare raw/normalized global registration and guarded local affine corrections.

    The four variants are raw/global, raw/local, normalized/global, normalized/local.
    Labels and human rectangles are used only after all candidate geometry is fixed.
    Reports and images belong in private storage. Output must be a new directory.
    """
    if output.exists():
        raise ValueError("Output must be a new directory")
    template = read_config(template_path, Template)
    engine = Engine.from_file(template_path)
    source = read_image(source_path)
    boxes, corpus = (
        ({}, None)
        if manifest_path is None
        else geometry_observations(manifest_path, template_path, source_path, source.shape[:2])
    )
    output.mkdir(parents=True)
    report = {
        "schema_version": 1,
        "purpose": "geometry_development_trial_not_answer_validation",
        "source_sha256": digest(source_path),
        "template_sha256": engine.template_digest,
        "reference_sha256": template.reference_sha256,
        "code_sha256": {
            name: digest(Path(__file__).with_name(name))
            for name in (
                "geometry_trial.py",
                "local_registration.py",
                "registration.py",
                "regions.py",
                "images.py",
                "engine.py",
            )
        },
        "versions": {"opencv": cv2.__version__, "numpy": np.__version__},
        "corpus": corpus,
        "variants": {},
        "complete": False,
    }
    write_json(output / "template.json", template.model_dump())
    # Optical extraction remains the historical result. Candidate trials change no notes.
    selection = Exam(
        template_id=template.template_id,
        sections={s.id: list(range(1, s.questions + 1)) for s in template.sections},
    )
    historical, _ = engine.analyze(source, selection)
    write_json(output / "historical-result.json", historical)
    for variant in ("raw", "normalized"):
        data = {"registration": None, "sections": {}, "global_regions": [], "local_regions": []}
        report["variants"][variant] = data
        try:
            registrar = (
                engine.registrar
                if variant == "raw"
                else Registrar(normalized_gray(engine.reference), template)
            )
            match_image = (
                source
                if variant == "raw"
                else cv2.cvtColor(normalized_gray(source), cv2.COLOR_GRAY2BGR)
            )
            _, _, _, diagnostic = registrar.align(match_image)
        except (RegistrationError, ValueError) as exc:
            data["error"] = str(exc)
        else:
            data["registration"] = diagnostic
            global_transform = np.asarray(diagnostic["input_to_reference"])
            global_inverse = np.linalg.inv(global_transform)
            aligned, valid = _warp(source, global_transform, template)
            gray = normalized_gray(aligned)
            for section in template.sections:
                folder = output / variant / section.id
                data["global_regions"].extend(
                    _regions(source, aligned, valid, global_inverse, section, folder / "global")
                )
                refinement = refine_section(engine.gray_reference, gray, valid, section)
                entry = {
                    "refinement": refinement,
                    "quality_before": engine.section_quality(gray, valid, global_inverse, section),
                }
                data["sections"][section.id] = entry
                if refinement["reference_to_global"] is None:
                    continue
                # ECC maps target reference -> global-aligned input; compose before sampling.
                local = np.asarray(refinement["reference_to_global"])
                transform = np.linalg.inv(local) @ global_transform
                inverse = global_inverse @ local
                entry.update(
                    source_to_reference=transform.tolist(), reference_to_source=inverse.tolist()
                )
                local_aligned, local_valid = _warp(source, transform, template)
                local_gray = normalized_gray(local_aligned)
                entry["quality_after"] = engine.section_quality(
                    local_gray, local_valid, inverse, section
                )
                data["local_regions"].extend(
                    _regions(source, local_aligned, local_valid, inverse, section, folder / "local")
                )
                save_image(folder / "local-valid.png", local_valid)
                # Explicit round-trip evidence; no accuracy claim from this algebraic check.
                points = [section.center(1, 1), section.center(section.questions, section.choices)]
                back = project_points(project_points(points, inverse), transform)
                entry["round_trip_error_px"] = float(
                    np.linalg.norm(np.asarray(back) - points, axis=1).max()
                )
        data["global_comparison"] = compare_geometry(data["global_regions"], boxes)
        data["local_comparison"] = compare_geometry(data["local_regions"], boxes)
    _write_review(output, report, engine.reference)
    report["artifact_sha256"] = {
        p.relative_to(output).as_posix(): digest(p)
        for p in sorted(output.rglob("*"))
        if p.is_file()
    }
    report["complete"] = True
    write_json(output / "report.json", report)
    return report


def _write_review(output: Path, report: dict, reference: np.ndarray) -> None:
    lines = [
        "# S03 — Essai de géométrie",
        "",
        "Développement uniquement. Aucun entraînement ni activation dans l’application.",
        "",
        "Les centres contenus dans un cadre humain ne prouvent ni la lecture des marques ni la précision des bords de cases.",
        "",
    ]
    cards = []
    for variant, data in report["variants"].items():
        lines.append(f"## {variant}")
        if "error" in data:
            lines.append(f"Refus global : {data['error']}")
        for kind in ("global", "local"):
            metrics = data[f"{kind}_comparison"]
            lines.append(
                f"- {kind} : {metrics['located']}/{metrics['human_rectangles']} cadres comparables ; {metrics['all_choice_centers_inside']} avec tous les centres contenus."
            )
        for section, entry in data["sections"].items():
            r = entry["refinement"]
            lines.append(f"- Grille {section} : {r['status']} ({r['reason']}).")
        for region in data["global_regions"]:
            sid, q = region["section"], region["question"]
            relative = f"{variant}/{sid}"
            save_image(
                output / relative / "global" / f"ref{q:03d}.png",
                crop(reference, region["reference_bounds"]),
            )
            images = [
                f'<figure><figcaption>{label}</figcaption><img src="{relative}/{path}" alt="{label}"></figure>'
                for label, path in (
                    ("Référence", f"global/ref{q:03d}.png"),
                    ("Global", f"global/q{q:03d}.png"),
                )
            ]
            if (output / relative / "local" / f"q{q:03d}.png").exists():
                images.append(
                    f'<figure><figcaption>Local contrôlé</figcaption><img src="{relative}/local/q{q:03d}.png" alt="Local contrôlé"></figure>'
                )
            cards.append(
                f"<section><h2>{html.escape(variant)} · {html.escape(sid)} · Q{q}</h2><div>{''.join(images)}</div></section>"
            )
    summary = "\n".join(lines) + "\n"
    (output / "summary.md").write_text(summary, encoding="utf-8")
    (output / "review.html").write_text(
        '<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        "<title>S03 — Géométrie</title><style>body{font:16px sans-serif;margin:24px;max-width:1100px}pre{white-space:pre-wrap}"
        "section{border-top:1px solid #888;padding:16px 0}section div{display:flex;flex-wrap:wrap;gap:12px}figure{margin:0}"
        "img{height:280px;max-width:100%;object-fit:contain;object-position:left}figcaption{margin-bottom:8px}</style>"
        f"<h1>Comparaison géométrique S03</h1><pre>{html.escape(summary)}</pre>{''.join(cards)}</html>",
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
        run_geometry_trial(args.template, args.source, args.output, args.manifest)
    except (ValueError, OSError, KeyError, TypeError, cv2.error) as exc:
        parser.exit(2, f"Geometry trial failed: {exc}\n")
    print(f"Geometry trial written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
