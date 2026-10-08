"""Private, human-labelled acquisitions. Predictions are never annotation defaults."""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import stat
import tempfile
import threading
import uuid
import zipfile
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal

import cv2
import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import Field, model_validator

from .baseline import _export_regions, digest
from .config import ConfigModel, Exam, Identifier, Template, read_config, write_json
from .engine import Engine
from .images import MAX_FILE_BYTES, read_image, save_image
from .regions import crop, question_region
from .sheets import read_upload
from .store import Conflict

Split = Literal["development", "train", "calibration", "test"]
Mark = Literal["empty", "marked", "ambiguous", "unreadable"]
Status = Literal["single", "blank", "multiple", "uncertain", "unreadable"]
MAX_EXPANDED_BYTES = 150 * 1024 * 1024


class ImportOptions(ConfigModel):
    physical_sheet_id: Identifier
    group_id: Identifier
    split: Split = "development"
    training_allowed: bool = False


class Annotation(ConfigModel):
    expected_revision: int = Field(strict=True, ge=1)
    section: Identifier
    question: int = Field(strict=True, ge=1)
    reviewer: Identifier
    status: Status
    choices: list[Annotated[int, Field(strict=True, ge=1, le=10)]]
    marks: list[Mark] = Field(min_length=2, max_length=10)
    geometry: Literal["confirmed", "source_only", "incorrect"]
    manual_bounds: tuple[Annotated[int, Field(strict=True, ge=0)], ...] | None = None
    notes: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def consistent(self) -> Annotation:
        marked = [i for i, mark in enumerate(self.marks, 1) if mark == "marked"]
        expected = (
            "unreadable"
            if "unreadable" in self.marks
            else "uncertain"
            if "ambiguous" in self.marks
            else "multiple"
            if len(marked) > 1
            else "single"
            if marked
            else "blank"
        )
        if self.status != expected or self.choices != marked:
            raise ValueError("Le statut et les choix doivent correspondre aux marques visibles.")
        if self.manual_bounds is not None and len(self.manual_bounds) != 4:
            raise ValueError("Le cadrage doit contenir quatre coordonnées entières.")
        return self


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".pending")
    write_json(temporary, value)
    os.replace(temporary, path)


def _pixel_digest(image: np.ndarray) -> str:
    # Shape is part of identity; different file encoding of identical pixels is a duplicate.
    return hashlib.sha256(str(image.shape).encode() + image.tobytes()).hexdigest()


def _unpack(file: UploadFile, directory: Path) -> tuple[Engine, np.ndarray, Exam]:
    payload = file.file.read(MAX_FILE_BYTES + 1)
    if len(payload) > MAX_FILE_BYTES:
        raise ValueError("Le fichier dépasse la limite de 64 Mio.")
    required = {"template.json", "template.reference.png", "copy.png", "result.json"}
    allowed = required | {"README.txt", "zones.png", "annotated.png"}
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            entries = archive.infolist()
            names = [entry.filename for entry in entries]
            if len(names) != len(set(names)) or not required.issubset(names):
                raise ValueError("Archive incomplète ou entrées dupliquées.")
            if set(names) - allowed or any(
                entry.is_dir() or stat.S_ISLNK(entry.external_attr >> 16) for entry in entries
            ):
                raise ValueError("L’archive contient des chemins ou fichiers non autorisés.")
            if sum(entry.file_size for entry in entries) > MAX_EXPANDED_BYTES:
                raise ValueError("Archive décompressée trop volumineuse (150 Mio maximum).")
            for entry in entries:
                if entry.filename in required:
                    (directory / entry.filename).write_bytes(archive.read(entry))
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError) as exc:
        raise ValueError("Archive ZIP invalide ou non prise en charge.") from exc
    template = read_config(directory / "template.json", Template)
    if template.reference != "template.reference.png":
        raise ValueError("La référence doit être exactement template.reference.png.")
    engine = Engine.from_file(directory / "template.json")
    previous = json.loads((directory / "result.json").read_text())
    if not isinstance(previous, dict):
        raise ValueError("Résultat de diagnostic invalide.")
    exam = Exam.model_validate(previous.get("exam"))
    exam.validate_for(template)
    # Only the validated selection is used. Ignore predictions, names and any other fields.
    exam = exam.model_copy(update={"name": "corpus-selection"})
    return engine, read_image(directory / "copy.png"), exam


def _public(item: dict) -> dict:
    questions = [
        {k: q[k] for k in ("section", "question", "choices", "has_crop", "annotation")}
        for q in item["questions"]
    ]
    return {
        **{
            key: item[key]
            for key in (
                "id",
                "revision",
                "physical_sheet_id",
                "group_id",
                "split",
                "training_allowed",
                "created_at",
                "source_size",
                "aligned",
                "history",
            )
        },
        "questions": questions,
        "completed": sum(q["annotation"] is not None for q in questions),
        "total": len(questions),
    }


def _manifest(item: dict) -> dict:
    complete = all(q["annotation"] is not None for q in item["questions"])
    geometry = complete and all(
        q["annotation"]["geometry"] == "confirmed" for q in item["questions"]
    )
    return {
        "schema_version": 1,
        "purpose": "human_annotations_not_validated_accuracy",
        **_public(item),
        "provenance": item["provenance"],
        "questions": [
            {
                **question,
                "assets": {
                    "copy": f"manual/{index:04d}.png"
                    if question["annotation"] and question["annotation"]["manual_bounds"]
                    else stored["copy_crop"],
                    "reference": stored["reference_crop"],
                },
            }
            for index, (question, stored) in enumerate(
                zip(_public(item)["questions"], item["questions"], strict=True), 1
            )
        ],
        "images": item["images"],
        "eligible_for_training": item["split"] == "train" and item["training_allowed"] and geometry,
        "ready_for_evaluation": geometry,
        "independent_evaluation_established": False,
        "case_coordinates_validated": False,
        "limitations": "Un cadrage de question ne valide pas les coordonnées de chaque case. "
        "Aucun entraînement ni accord inter-annotateurs n’a été effectué.",
    }


def corpus_router(root: Path, engines: dict[str, Engine], lock: threading.Lock) -> APIRouter:
    """Mount a private single-worker corpus; all mutations share the OMR process lock."""
    root = root / "corpus"
    root.mkdir(parents=True, exist_ok=True)
    router = APIRouter(prefix="/api/corpus")

    def directory(identifier: str) -> Path:
        if not identifier.startswith("acq_") or len(identifier) != 36:
            raise KeyError(identifier)
        if any(c not in "0123456789abcdef" for c in identifier[4:]):
            raise KeyError(identifier)
        path = root / identifier
        if not (path / "metadata.json").is_file():
            raise KeyError(identifier)
        return path

    def get(identifier: str) -> dict:
        return json.loads((directory(identifier) / "metadata.json").read_text())

    def items() -> list[dict]:
        return [json.loads(p.read_text()) for p in sorted(root.glob("acq_*/metadata.json"))]

    def question(item: dict, section: str, number: int) -> dict:
        for q in item["questions"]:
            if q["section"] == section and q["question"] == number:
                return q
        raise KeyError("question")

    @router.get("")
    def listing() -> list[dict]:
        with lock:
            return [_public(item) for item in items()]

    @router.get("/export")
    def export_manifest() -> dict:
        with lock:
            return {"schema_version": 1, "acquisitions": [_manifest(item) for item in items()]}

    @router.post("")
    def create(
        file: UploadFile = File(...),
        physical_sheet_id: str = Form(...),
        group_id: str = Form(""),
        split: Split = Form("development"),
        training_allowed: bool = Form(False),
        template_id: str = Form(""),
    ) -> dict:
        options = ImportOptions(
            physical_sheet_id=physical_sheet_id,
            group_id=group_id or physical_sheet_id,
            split=split,
            training_allowed=training_allowed,
        )
        with lock, tempfile.TemporaryDirectory(prefix="import-", dir=root) as temporary:
            staging = Path(temporary)
            diagnostic = Path(file.filename or "").suffix.lower() == ".zip"
            try:
                if diagnostic:
                    engine, image, exam = _unpack(file, staging)
                    options.split = "development"
                else:
                    if template_id not in engines:
                        raise ValueError("Choisissez un modèle de feuille enregistré.")
                    engine = engines[template_id]
                    image = read_upload(file, staging)
                    exam = None
            finally:
                file.file.close()
            pixel_hash = _pixel_digest(image)
            for existing in items():
                if existing["provenance"]["decoded_pixel_sha256"] == pixel_hash:
                    raise Conflict(f"Cette image est déjà dans le corpus : {existing['id']}.")
                if existing["physical_sheet_id"] == options.physical_sheet_id:
                    if existing["group_id"] != options.group_id:
                        raise Conflict(
                            "Les photos d’une même feuille doivent garder le même groupe."
                        )
                if existing["group_id"] == options.group_id and existing["split"] != options.split:
                    raise Conflict("Un groupe doit rester dans un seul usage de données.")
            result, _ = engine.analyze(image, exam)
            save_image(staging / "source.png", image)
            save_image(staging / "reference.png", engine.reference)
            snapshot = engine.template.model_copy(
                update={
                    "reference": "reference.png",
                    "reference_sha256": digest(staging / "reference.png"),
                }
            )
            write_json(staging / "template.json", snapshot.model_dump())
            write_json(staging / "extraction.json", result)
            regions = _export_regions(engine, image, result, staging)
            by_question = {(r["section"], r["question"]): r for r in regions}
            registration = result["diagnostics"].get("registration")
            write_json(
                staging / "regions.json",
                {
                    "schema_version": 1,
                    "coordinate_system": "decoded_source_and_reference_pixel_centers",
                    "bounds_convention": "x0_y0_inclusive_x1_y1_exclusive",
                    "source_size": [image.shape[1], image.shape[0]],
                    "reference_size": [engine.template.width, engine.template.height],
                    "input_to_reference": registration["input_to_reference"]
                    if registration
                    else None,
                    "reference_to_input": np.linalg.inv(registration["input_to_reference"]).tolist()
                    if registration
                    else None,
                    "local_alignment": None,
                    "valid_mask": "valid.png" if registration else None,
                    "questions": regions,
                },
            )
            sections = {s.id: s for s in engine.template.sections}
            questions = []
            for index, answer in enumerate(result["answers"], 1):
                sid, number = answer["section"], answer["question"]
                region = by_question.get((sid, number))
                reference_path = f"references/{index:04d}.png"
                (staging / "references").mkdir(exist_ok=True)
                if region:
                    bounds = region["reference_bounds"]
                else:
                    bounds = question_region(
                        sections[sid],
                        number,
                        np.eye(3),
                        np.full(engine.reference.shape[:2], 255, np.uint8),
                        engine.reference.shape[:2],
                    ).reference_bounds
                save_image(staging / reference_path, crop(engine.reference, bounds))
                questions.append(
                    {
                        "section": sid,
                        "question": number,
                        "choices": sections[sid].choices,
                        "has_crop": region is not None,
                        "annotation": None,
                        "copy_crop": region["assets"]["copy"] if region else None,
                        "reference_crop": reference_path,
                    }
                )
            identifier = "acq_" + uuid.uuid4().hex
            item = {
                "schema_version": 1,
                "id": identifier,
                "revision": 1,
                **options.model_dump(),
                "created_at": _now(),
                "source_size": [image.shape[1], image.shape[0]],
                "aligned": bool(result["diagnostics"].get("registration")),
                "questions": questions,
                "history": [],
                "provenance": {
                    "kind": "diagnostic_development" if diagnostic else "image_upload",
                    "decoded_pixel_sha256": pixel_hash,
                    "pixel_hash_encoding": "shape_and_BGR_uint8",
                    "engine_version": result["engine_version"],
                    "template_sha256": engine.template_digest,
                    "snapshot_template_sha256": digest(staging / "template.json"),
                    "reference_sha256": engine.template.reference_sha256,
                    "code_sha256": {
                        p.name: digest(p) for p in sorted(Path(__file__).parent.glob("*.py"))
                    },
                },
                "images": {
                    "source": {"path": "source.png", "sha256": digest(staging / "source.png")},
                    "reference": {
                        "path": "reference.png",
                        "sha256": digest(staging / "reference.png"),
                    },
                },
            }
            # Imported predictions are discarded; only our internal replay is retained.
            for name in ("result.json", "copy.png", "template.reference.png"):
                (staging / name).unlink(missing_ok=True)
            _atomic(staging / "metadata.json", item)
            shutil.move(str(staging), str(root / identifier))
            return _public(item)

    @router.get("/{identifier}")
    def detail(identifier: str) -> dict:
        with lock:
            return _public(get(identifier))

    @router.patch("/{identifier}/annotations")
    def annotate(identifier: str, body: Annotation) -> dict:
        with lock:
            item = get(identifier)
            if body.expected_revision != item["revision"]:
                raise Conflict("La copie a changé. Rechargez-la avant d’enregistrer.")
            q = question(item, body.section, body.question)
            if len(body.marks) != q["choices"]:
                raise ValueError("Renseignez une marque pour chaque choix.")
            if body.manual_bounds is not None:
                x0, y0, x1, y1 = body.manual_bounds
                width, height = item["source_size"]
                if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
                    raise ValueError("Le cadrage doit être entièrement dans l’image source.")
            if body.geometry == "confirmed" and not (q["copy_crop"] or body.manual_bounds):
                raise ValueError("Confirmez un cadrage manuel quand l’alignement a échoué.")
            annotation = body.model_dump(exclude={"expected_revision", "section", "question"})
            annotation["recorded_at"] = _now()
            item["revision"] += 1
            item["history"].append(
                {
                    "revision": item["revision"],
                    "section": body.section,
                    "question": body.question,
                    "before": q["annotation"],
                    "after": annotation,
                }
            )
            q["annotation"] = annotation
            q["has_crop"] = bool(q["copy_crop"] or body.manual_bounds)
            _atomic(directory(identifier) / "metadata.json", item)
            return _public(item)

    @router.get("/{identifier}/image/{view}")
    def image(identifier: str, view: Literal["source", "reference"]) -> FileResponse:
        return FileResponse(directory(identifier) / f"{view}.png", media_type="image/png")

    @router.get("/{identifier}/crop/{section}/{number}")
    def question_crop(
        identifier: str, section: str, number: int, view: Literal["copy", "reference"] = "copy"
    ) -> Response:
        with lock:
            item = get(identifier)
            q = question(item, section, number)
            path = directory(identifier)
            annotation = q["annotation"]
            if view == "copy" and annotation and annotation["manual_bounds"]:
                data = crop(read_image(path / "source.png"), annotation["manual_bounds"])
                ok, encoded = cv2.imencode(".png", data)
                if not ok:
                    raise ValueError("Échec de l’encodage du cadrage.")
                return Response(encoded.tobytes(), media_type="image/png")
            relative = q["reference_crop"] if view == "reference" else q["copy_crop"]
            if relative is None:
                raise HTTPException(404, "Aucun cadrage attribué à cette question.")
            return FileResponse(path / relative, media_type="image/png")

    @router.get("/{identifier}/export")
    def export_acquisition(identifier: str) -> StreamingResponse:
        archive = tempfile.TemporaryFile(dir=root)
        try:
            with lock:
                item = get(identifier)
                path = directory(identifier)
                with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
                    bundle.writestr(
                        "manifest.json", json.dumps(_manifest(item), ensure_ascii=False)
                    )
                    for name in ("source.png", "reference.png", "template.json", "regions.json"):
                        bundle.write(path / name, name)
                    if (path / "valid.png").is_file():
                        bundle.write(path / "valid.png", "valid.png")
                    for folder in ("questions", "references"):
                        for asset in sorted((path / folder).rglob("*.png")):
                            bundle.write(asset, asset.relative_to(path).as_posix())
                    for index, q in enumerate(item["questions"], 1):
                        if q["annotation"] and q["annotation"]["manual_bounds"]:
                            data = crop(
                                read_image(path / "source.png"), q["annotation"]["manual_bounds"]
                            )
                            ok, encoded = cv2.imencode(".png", data)
                            if not ok:
                                raise ValueError("Échec de l’encodage du cadrage.")
                            bundle.writestr(f"manual/{index:04d}.png", encoded.tobytes())
            archive.seek(0)
        except Exception:
            archive.close()
            raise

        def chunks() -> Iterator[bytes]:
            try:
                while data := archive.read(1024 * 1024):
                    yield data
            finally:
                archive.close()

        return StreamingResponse(
            chunks(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="corpus-{identifier}.zip"',
            },
        )

    return router
