"""S06 private, versioned bubble datasets. Question labels never validate bubble geometry."""

from __future__ import annotations

import hashlib
import html
import json
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from .baseline import digest
from .config import write_json
from .engine import Engine
from .images import normalized_gray, read_image, save_image
from .photometric_trial import _observations
from .photometry import project_photo
from .regions import crop, question_region
from .registration import Registrar, RegistrationError

CLASSES = ("empty", "marked", "ambiguous", "unreadable")
PREPROCESSING = "bubble-gray-letterbox32-v1"
SIZE = 32


def letterbox(image: np.ndarray) -> np.ndarray:
    """Grayscale, preserve aspect ratio and pad white; resizing adds no source detail."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    if gray.ndim != 2 or min(gray.shape) < 1 or gray.dtype != np.uint8:
        raise ValueError("Expected nonempty uint8 image")
    height, width = gray.shape
    scale = SIZE / max(height, width)
    resized = cv2.resize(
        gray,
        (max(1, round(width * scale)), max(1, round(height * scale))),
        interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR,
    )
    result = np.full((SIZE, SIZE), 255, np.uint8)
    h, w = resized.shape
    result[(SIZE - h) // 2 : (SIZE - h) // 2 + h, (SIZE - w) // 2 : (SIZE - w) // 2 + w] = resized
    return result


def local_file(root: Path, name: str) -> Path:
    """Resolve a dataset asset without escaping the private dataset directory."""
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("Missing or out-of-directory dataset asset")
    return path


def _asset(output: Path, name: str, image: np.ndarray) -> dict:
    path = output / name
    path.parent.mkdir(parents=True, exist_ok=True)
    save_image(path, image)
    return {"path": name, "sha256": digest(path)}


def _finish(output: Path, rows: list[dict], kind: str, provenance: dict) -> dict:
    manifest = {
        "schema_version": 1,
        "kind": kind,
        "preprocessing": PREPROCESSING,
        "classes": list(CLASSES),
        "samples": rows,
        "provenance": provenance,
        "code_sha256": digest(Path(__file__)),
    }
    write_json(output / "dataset.json", manifest)
    write_json(
        output / "geometry-review.json",
        {
            "schema_version": 1,
            "dataset_sha256": digest(output / "dataset.json"),
            "decisions": [
                {"sample_id": r["id"], "status": "pending", "reviewer": None} for r in rows
            ],
        },
    )
    cards = []
    for r in rows:
        images = "".join(
            f'<img loading="lazy" src="{html.escape(r[k]["path"], quote=True)}" alt="{k}">'
            for k in ("question_context", "copy", "reference")
            if k in r
        )
        cards.append(f"<article><p>{r['id']} · {html.escape(r['label'])}</p>{images}</article>")
    (output / "review.html").write_text(
        '<!doctype html><html lang="fr"><meta charset="utf-8"><title>S06 — Régions à vérifier</title>'
        "<style>body{font:16px sans-serif;margin:24px}main{display:flex;flex-wrap:wrap;gap:16px}"
        "article{border:1px solid #aaa;padding:8px}img{height:128px;max-width:220px;object-fit:contain}</style>"
        "<h1>S06 — Découpes proposées</h1><p>Contexte de question, case photographiée, référence."
        " Les annotations portent sur les marques visibles. Vérifier séparément que chaque découpe"
        " correspond bien au choix annoncé. Aucun clic dans cette galerie ne valide les régions.</p>"
        f"<main>{''.join(cards)}</main></html>",
        encoding="utf-8",
    )
    return manifest


def prepare_dataset(manifest_path: Path, output: Path) -> dict:
    """Extract proposed native-scale crops from an S02 export; never auto-confirm them.

    This development tool refuses reserved calibration/test acquisitions. It leaves
    the original manifest and labels untouched. Marks do not enter registration.
    """
    if output.exists():
        raise ValueError("Output must be a new directory")
    m = json.loads(manifest_path.read_text())
    if m.get("schema_version") != 1 or m.get("split") not in {"train", "development"}:
        raise ValueError("S06 preparation accepts train/development exports only")
    for key in ("physical_sheet_id", "group_id"):
        if not isinstance(m.get(key), str) or not m[key].strip():
            raise ValueError("Missing physical-sheet/group identity")
    if type(m.get("training_allowed")) is not bool:
        raise ValueError("Missing training permission")
    root = manifest_path.parent
    source_path, template_path = local_file(root, "source.png"), local_file(root, "template.json")
    local_file(root, json.loads(template_path.read_text())["reference"])
    engine = Engine.from_file(template_path)
    source = read_image(source_path)
    if (
        m["images"]["source"]["sha256"] != digest(source_path)
        or m["images"]["reference"]["sha256"] != engine.template.reference_sha256
        or m["provenance"]["snapshot_template_sha256"] != digest(template_path)
        or m["source_size"] != [source.shape[1], source.shape[0]]
    ):
        raise ValueError("Export fingerprint/dimensions mismatch")
    sections = {s.id: s for s in engine.template.sections}
    seen = set()
    for q in m["questions"]:
        key = (q["section"], q["question"])
        s = sections.get(key[0])
        if (
            key in seen
            or s is None
            or type(key[1]) is not int
            or not 1 <= key[1] <= s.questions
            or q["choices"] != s.choices
        ):
            raise ValueError("Invalid/duplicate question or choice count")
        seen.add(key)
    labels = _observations(manifest_path)
    registrar = Registrar(normalized_gray(engine.reference), engine.template)
    registration_attempts = []
    registration_preprocessing = "existing_normalized_gray"
    try:
        _, _, _, registration = registrar.align(
            cv2.cvtColor(normalized_gray(source), cv2.COLOR_GRAY2BGR)
        )
    except RegistrationError as exc:
        # Normalization can remove useful print contrast on a clean photocopy.
        # Reuse the historical registrar with every original geometric guard intact;
        # no label, saved transform or guessed coordinates can make it pass.
        registration_attempts.append(
            {"preprocessing": registration_preprocessing, "error": str(exc)}
        )
        registration_preprocessing = "historical_raw_gray"
        _, _, _, registration = engine.registrar.align(source)
    registration_attempts.append({"preprocessing": registration_preprocessing, "accepted": True})
    transform = np.asarray(registration["input_to_reference"])
    inverse = np.linalg.inv(transform)
    aligned, available = project_photo(
        source, transform, (engine.template.width, engine.template.height)
    )
    valid = available.astype(np.uint8) * 255
    output.mkdir(parents=True)
    rows = []
    pixel_hash = hashlib.sha256(source.tobytes()).hexdigest()
    for q in m["questions"]:
        key = (q["section"], q["question"])
        if key not in labels:
            continue
        region = question_region(sections[key[0]], key[1], inverse, valid, source.shape[:2])
        context = _asset(
            output, f"contexts/{len(rows):05d}.png", crop(aligned, region.reference_bounds)
        )
        for c, label in zip(region.choices, labels[key]["marks"], strict=True):
            identifier = f"{len(rows):05d}"
            issues = []
            if c.valid_fraction < 0.99:
                issues.append("partial_crop")
            # Candidate-specific conservative sampling floor, not a production threshold.
            if min(c.source_diameters_px) < 6:
                issues.append("low_source_resolution")
            if q["annotation"]["geometry"] != "confirmed":
                issues.append("question_geometry_unconfirmed")
            bounds = q["annotation"].get("manual_bounds")
            if bounds is not None:
                if (
                    len(bounds) != 4
                    or any(type(v) is not int for v in bounds)
                    or not 0 <= bounds[0] < bounds[2] <= source.shape[1]
                    or not 0 <= bounds[1] < bounds[3] <= source.shape[0]
                ):
                    raise ValueError("Invalid annotated source rectangle")
                if not (
                    bounds[0] <= c.source_center[0] < bounds[2]
                    and bounds[1] <= c.source_center[1] < bounds[3]
                ):
                    issues.append("outside_confirmed_question")
            rows.append(
                {
                    "id": identifier,
                    "section": key[0],
                    "question": key[1],
                    "choice": c.choice,
                    "label": label,
                    "split": m["split"],
                    "training_allowed": m["training_allowed"],
                    "group_id": m["group_id"],
                    "physical_sheet_id": m["physical_sheet_id"],
                    "acquisition_sha256": pixel_hash,
                    "geometry_validated": False,
                    "source_diameters_px": list(c.source_diameters_px),
                    "source_quad": c.source_quad,
                    "reference_bounds": c.reference_bounds,
                    "valid_fraction": c.valid_fraction,
                    "quality_issues": issues,
                    "copy": _asset(
                        output, f"crops/{identifier}.png", crop(aligned, c.reference_bounds)
                    ),
                    "reference": _asset(
                        output,
                        f"references/{identifier}.png",
                        crop(engine.reference, c.reference_bounds),
                    ),
                    "question_context": context,
                }
            )
    return _finish(
        output,
        rows,
        "real",
        {
            "manifest_sha256": digest(manifest_path),
            "source_sha256": digest(source_path),
            "template_sha256": digest(template_path),
            "reference_sha256": engine.template.reference_sha256,
            "registration": registration,
            "registration_preprocessing": registration_preprocessing,
            "registration_attempts": registration_attempts,
            "opencv": cv2.__version__,
            "code_sha256": {
                name: digest(Path(__file__).with_name(name))
                for name in (
                    "images.py",
                    "regions.py",
                    "registration.py",
                    "photometry.py",
                    "engine.py",
                )
            },
        },
    )


def synthetic_dataset(output: Path, seed: int = 17, groups: int = 8) -> dict:
    """Balanced toy marks for pipeline tests, never a source of real accuracy claims."""
    if output.exists() or groups < 2:
        raise ValueError("Use a new directory and at least two synthetic groups")
    output.mkdir(parents=True)
    rng = np.random.default_rng(seed)
    rows = []
    for g in range(groups):
        for example in range(32):
            label = CLASSES[example % len(CLASSES)]
            height, width = int(rng.integers(22, 32)), int(rng.integers(16, 26))
            reference = np.full((height, width), 250, np.uint8)
            center = (width // 2, height // 2)
            cv2.ellipse(reference, center, (width // 2 - 2, height // 2 - 2), 0, 0, 360, 150, 1)
            cv2.putText(
                reference,
                str(example % 5 + 1),
                (width // 2 - 3, height // 2 + 3),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.3,
                150,
                1,
            )
            image = reference.copy()
            if label in {"marked", "ambiguous"}:
                color = int(rng.integers(20, 90) if label == "marked" else rng.integers(175, 215))
                if example % 3 == 0:
                    cv2.ellipse(
                        image, center, (max(2, width // 3), height // 3), 0, 0, 360, color, -1
                    )
                else:
                    cv2.line(image, (3, height // 2), (width // 2, height - 4), color, 2)
                    cv2.line(image, (width // 2, height - 4), (width - 3, 3), color, 2)
            elif label == "unreadable":
                image[:] = rng.integers(60, 190, image.shape, dtype=np.uint8)
                image = cv2.GaussianBlur(image, (7, 7), 2)
            # Mild noise never erases a label; destructive ambiguity has its own class.
            image = np.clip(image.astype(float) + rng.normal(0, 2, image.shape), 0, 255).astype(
                np.uint8
            )
            identifier = f"{len(rows):05d}"
            group = f"synthetic-{seed}-{g}"
            rows.append(
                {
                    "id": identifier,
                    "section": "synthetic",
                    "question": example // 4 + 1,
                    "choice": example % 4 + 1,
                    "label": label,
                    "group_id": group,
                    "physical_sheet_id": group,
                    "acquisition_sha256": group,
                    "split": "development" if g == groups - 1 else "train",
                    "training_allowed": True,
                    "geometry_validated": True,
                    "quality_issues": [],
                    "valid_fraction": 1.0,
                    "source_diameters_px": [width - 4, height - 4],
                    "copy": _asset(output, f"crops/{identifier}.png", image),
                    "reference": _asset(output, f"references/{identifier}.png", reference),
                }
            )
    return _finish(output, rows, "synthetic", {"seed": seed, "groups": groups})


def load_dataset(path: Path) -> tuple[dict, list[dict], np.ndarray]:
    """Verify immutable assets and optional, hash-bound per-case geometry review."""
    m = json.loads(path.read_text())
    if (
        m.get("schema_version") != 1
        or m.get("kind") not in {"real", "synthetic"}
        or m.get("preprocessing") != PREPROCESSING
        or m.get("classes") != list(CLASSES)
    ):
        raise ValueError("Unsupported dataset/preprocessing/classes")
    review_path = path.parent / "geometry-review.json"
    decisions = {}
    if review_path.exists():
        review = json.loads(review_path.read_text())
        if review.get("schema_version") != 1 or review.get("dataset_sha256") != digest(path):
            raise ValueError("Stale geometry review")
        for d in review["decisions"]:
            if (
                d["sample_id"] in decisions
                or d["status"] not in {"pending", "confirmed", "rejected"}
                or (d["status"] != "pending" and not str(d.get("reviewer") or "").strip())
            ):
                raise ValueError("Invalid geometry review")
            decisions[d["sample_id"]] = d["status"]
    rows, tensors, seen = [], [], set()
    for r in m["samples"]:
        if (
            r["id"] in seen
            or r["label"] not in CLASSES
            or r["split"] not in {"train", "development"}
            or type(r["training_allowed"]) is not bool
            or type(r["geometry_validated"]) is not bool
            or any(
                not isinstance(r[k], str) or not r[k]
                for k in ("group_id", "physical_sheet_id", "acquisition_sha256")
            )
            or type(r["question"]) is not int
            or r["question"] < 1
            or type(r["choice"]) is not int
            or not 1 <= r["choice"] <= 10
        ):
            raise ValueError("Invalid/duplicate sample or reserved split")
        seen.add(r["id"])
        pair = []
        for key in ("copy", "reference"):
            asset = local_file(path.parent, r[key]["path"])
            if digest(asset) != r[key]["sha256"]:
                raise ValueError("Dataset asset checksum mismatch")
            pair.append(letterbox(read_image(asset)))
        confirmed = (m["kind"] == "synthetic" and r["geometry_validated"]) or decisions.get(
            r["id"]
        ) == "confirmed"
        if decisions.get(r["id"]) == "rejected":
            confirmed = False
        diameters = np.asarray(r["source_diameters_px"], dtype=float)
        if (
            diameters.shape != (2,)
            or not np.isfinite(diameters).all()
            or (diameters <= 0).any()
            or not 0 <= r["valid_fraction"] <= 1
            or not isinstance(r["quality_issues"], list)
            or any(not isinstance(issue, str) for issue in r["quality_issues"])
        ):
            raise ValueError("Invalid source quality metadata")
        issues = list(r["quality_issues"])
        if r["valid_fraction"] < 0.99:
            issues.append("partial_crop")
        if diameters.min() < 6:
            issues.append("low_source_resolution")
        rows.append(
            dict(
                r,
                geometry_validated=confirmed,
                dataset_kind=m["kind"],
                quality_issues=sorted(set(issues)),
            )
        )
        tensors.append(np.stack(pair))
    if set(decisions) - seen or not rows:
        raise ValueError("Unknown review sample or empty dataset")
    return m, rows, np.asarray(tensors, dtype=np.float32) / 255.0


def validate_groups(rows: list[dict]) -> None:
    """Prevent identical acquisitions, physical sheets or related groups crossing splits."""
    assignments, samples = {}, set()
    for r in rows:
        for kind in ("group_id", "physical_sheet_id", "acquisition_sha256"):
            key = (kind, r[kind])
            if key in assignments and assignments[key] != r["split"]:
                raise ValueError(f"Data leakage across splits: {kind}")
            assignments[key] = r["split"]
        key = (r["acquisition_sha256"], r["section"], r["question"], r["choice"])
        if key in samples:
            raise ValueError("Duplicate acquisition/question/choice")
        samples.add(key)


def dataset_summary(rows: list[dict]) -> dict:
    """Aggregate counts without student identities or individual observations."""
    return {
        "samples": len(rows),
        "groups": len({r["group_id"] for r in rows}),
        "class_counts": dict(Counter(r["label"] for r in rows)),
        "geometry_confirmed": sum(r["geometry_validated"] for r in rows),
        "quality_rejected": sum(bool(r["quality_issues"]) for r in rows),
    }
