"""Persistent visual calibration drafts; published geometries are immutable.

All routes share the web OMR lock: PDFium, calibration, registry updates and tests
are serialized within the single-worker prototype. Metadata commits use replace;
failed calibrations never replace the last usable version.
"""

from __future__ import annotations

import json
import re
import shutil
import tempfile
import threading
import uuid
import zipfile
from collections.abc import Iterator
from pathlib import Path

import numpy as np
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import Field

from .calibration import calibrate
from .config import ConfigModel, Layout, Section, write_json
from .engine import Engine
from .images import MAX_FILE_BYTES, SUPPORTED, iter_pages, read_image, save_image
from .readability import with_readability
from .store import Conflict


class CalibrationRequest(ConfigModel):
    expected_revision: int = Field(strict=True, ge=1)
    name: str = Field(min_length=1, max_length=120)
    sections: list[Section] = Field(min_length=1, max_length=50)


class PublishRequest(ConfigModel):
    expected_revision: int = Field(strict=True, ge=1)
    checked_overlay: bool


class SheetLibrary:
    """Files live under the application's private data directory, never in Git."""

    def __init__(self, root: Path) -> None:
        self.root = root / "sheets"
        self.root.mkdir(parents=True, exist_ok=True)

    def directory(self, identifier: str) -> Path:
        if not re.fullmatch(r"sheet_[0-9a-f]{32}", identifier):
            raise KeyError(identifier)
        return self.root / identifier

    def get(self, identifier: str) -> dict:
        path = self.directory(identifier) / "metadata.json"
        if not path.is_file():
            raise KeyError(identifier)
        return json.loads(path.read_text(encoding="utf-8"))

    def list(self) -> list[dict]:
        return [self.get(p.parent.name) for p in sorted(self.root.glob("*/metadata.json"))]

    def save(self, item: dict) -> None:
        directory = self.directory(item["id"])
        temporary = directory / f"{uuid.uuid4().hex}.tmp"
        try:
            write_json(temporary, item)
            temporary.replace(directory / "metadata.json")
        finally:
            temporary.unlink(missing_ok=True)

    def template_path(self, item: dict) -> Path:
        if not item.get("calibration"):
            raise ValueError("Vérifiez d’abord les zones de la feuille.")
        return self.directory(item["id"]) / item["calibration"] / "template.json"

    @staticmethod
    def check_revision(item: dict, revision: int, *, editable: bool = True) -> None:
        if item["revision"] != revision:
            raise Conflict("Cette feuille a changé dans un autre onglet. Rechargez la page.")
        if editable and item["published"]:
            raise Conflict(
                "Ce modèle est enregistré. Importez une nouvelle version pour le modifier."
            )


def read_upload(file: UploadFile, root: Path) -> np.ndarray:
    """Decode exactly one page and remove the temporary upload, including on failure."""
    suffix = Path(file.filename or "").suffix.lower()
    temporary = root / f"upload-{uuid.uuid4().hex}{suffix}"
    try:
        if suffix not in SUPPORTED:
            raise ValueError("Choisissez un PNG, JPG, TIFF ou PDF d’une seule page.")
        size = 0
        with temporary.open("wb") as stream:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_FILE_BYTES:
                    raise ValueError("Le fichier dépasse la limite de 64 Mio.")
                stream.write(chunk)
        pages = iter_pages(temporary)
        try:
            first = next(pages, None)
            if first is None or first.error:
                raise ValueError(first.error if first else "Le fichier ne contient aucune page.")
            if next(pages, None) is not None:
                raise ValueError("Importez une seule page pour créer ou essayer un modèle.")
            return first.image
        finally:
            pages.close()
    finally:
        temporary.unlink(missing_ok=True)
        file.file.close()


def sheet_router(
    library: SheetLibrary, engines: dict[str, Engine], lock: threading.Lock
) -> APIRouter:
    router = APIRouter(prefix="/api/sheets")

    @router.get("")
    def list_sheets() -> list[dict]:
        return library.list()

    @router.post("")
    def import_sheet(file: UploadFile = File(...)) -> dict:
        with lock:
            reference = read_upload(file, library.root)
            height, width = reference.shape[:2]
            if min(width, height) < 128 or max(width, height) > 10000:
                raise ValueError("La feuille doit mesurer entre 128 et 10 000 pixels par côté.")
            identifier = "sheet_" + uuid.uuid4().hex
            directory = library.directory(identifier)
            directory.mkdir()
            item = {
                "id": identifier,
                "name": Path(file.filename or "Nouvelle feuille").stem[:120] or "Nouvelle feuille",
                "width": width,
                "height": height,
                "revision": 1,
                "sections": [],
                "calibration": None,
                "published": False,
                "test": None,
            }
            try:
                save_image(directory / "blank.png", reference)
                library.save(item)
            except Exception:
                shutil.rmtree(directory)
                raise
            return item

    @router.get("/{identifier}")
    def get_sheet(identifier: str) -> dict:
        return library.get(identifier)

    @router.put("/{identifier}/calibration")
    def check_layout(identifier: str, request: CalibrationRequest) -> dict:
        with lock:
            item = library.get(identifier)
            library.check_revision(item, request.expected_revision)
            if not request.name.strip():
                raise ValueError("Donnez un nom à la feuille.")
            layout = Layout(
                template_id=identifier,
                width=item["width"],
                height=item["height"],
                sections=request.sections,
            )
            folder = "calibration-" + uuid.uuid4().hex
            destination = library.directory(identifier) / folder
            try:
                calibrate(
                    read_image(library.directory(identifier) / "blank.png"),
                    layout,
                    destination / "template.json",
                )
                item.update(
                    name=request.name.strip(),
                    sections=[s.model_dump() for s in layout.sections],
                    calibration=folder,
                    revision=item["revision"] + 1,
                    test=None,
                )
                library.save(item)
            except Exception:
                shutil.rmtree(destination, ignore_errors=True)
                raise
            return item

    @router.post("/{identifier}/publish")
    def publish(identifier: str, request: PublishRequest) -> dict:
        with lock:
            item = library.get(identifier)
            library.check_revision(item, request.expected_revision)
            if not request.checked_overlay:
                raise ValueError("Vérifiez l’aperçu des cases avant d’enregistrer ce modèle.")
            engine = Engine.from_file(library.template_path(item))
            item.update(published=True, revision=item["revision"] + 1)
            library.save(item)
            engines[identifier] = engine
            return item

    @router.post("/{identifier}/test")
    def test_sheet(identifier: str, revision: int, file: UploadFile = File(...)) -> dict:
        with lock:
            try:
                item = library.get(identifier)
                library.check_revision(item, revision, editable=False)
                engine = Engine.from_file(library.template_path(item))
                image = read_upload(file, library.root)
                extraction, annotated = engine.analyze(image)
                folder = "test-" + uuid.uuid4().hex
                destination = library.directory(identifier) / folder
                destination.mkdir()
                try:
                    save_image(destination / "annotated.png", annotated)
                    save_image(destination / "original.png", image)
                    write_json(destination / "result.json", extraction)
                    item["test"] = folder
                    library.save(item)
                except Exception:
                    shutil.rmtree(destination, ignore_errors=True)
                    raise
                return {"sheet": item, "extraction": with_readability(extraction)}
            finally:
                file.file.close()

    @router.get("/{identifier}/test")
    def test_result(identifier: str) -> dict:
        item = library.get(identifier)
        if not item["test"]:
            raise KeyError("test")
        path = library.directory(identifier) / item["test"] / "result.json"
        return with_readability(json.loads(path.read_text(encoding="utf-8")))

    @router.get("/{identifier}/diagnostic")
    def diagnostic(identifier: str, expected_test: str | None = None) -> StreamingResponse:
        # Snapshot pointers under the same lock as calibration/test commits. Their
        # files are immutable; a later test cannot mix versions in this archive.
        with lock:
            item = library.get(identifier)
            if not item["test"]:
                raise KeyError("test")
            if expected_test is not None and item["test"] != expected_test:
                raise Conflict(
                    "Un autre essai a été effectué. Rechargez la page avant de télécharger."
                )
            template = library.template_path(item)
            test = library.directory(identifier) / item["test"]
        archive = tempfile.TemporaryFile(dir=library.root)
        try:
            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
                for source, name in [
                    (template, "template.json"),
                    (template.with_suffix(".reference.png"), "template.reference.png"),
                    (template.with_suffix(".preview.png"), "zones.png"),
                    (test / "original.png", "copy.png"),
                    (test / "annotated.png", "annotated.png"),
                    (test / "result.json", "result.json"),
                ]:
                    bundle.write(source, name)
                bundle.writestr(
                    "README.txt",
                    (
                        "Diagnostic PsychoMark : référence, géométrie, copie décodée et résultat.\n"
                        "Les images peuvent contenir des informations personnelles.\n"
                        "Aucun corrigé, aucune base d’examens ni autre copie n’est inclus.\n"
                        "Ce dossier permet de reproduire l’analyse avec le moteur et sa version\n"
                        "indiquée dans result.json. Les seuils sont dans template.json.\n"
                    ),
                )
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
            headers={"Content-Disposition": f'attachment; filename="diagnostic-{identifier}.zip"'},
        )

    @router.get("/{identifier}/image/{kind}")
    def image(identifier: str, kind: str) -> FileResponse:
        item = library.get(identifier)
        if kind == "blank":
            path = library.directory(identifier) / "blank.png"
        elif kind == "preview" and item["calibration"]:
            path = library.template_path(item).with_suffix(".preview.png")
        elif kind in {"test", "original"} and item["test"]:
            filename = "annotated.png" if kind == "test" else "original.png"
            path = library.directory(identifier) / item["test"] / filename
        else:
            raise KeyError(kind)
        return FileResponse(path, media_type="image/png")

    return router
