"""Single-operator web prototype backed by the existing OMR engine."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import shutil
import threading
import uuid
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import Field

from .config import ConfigModel, Layout
from .demo import create_demo
from .development import codespaces_origin, source_revision
from .engine import Engine
from .grading import Assessment, Review, grade
from .images import MAX_FILE_BYTES, SUPPORTED, iter_pages, read_image, save_image
from .store import Conflict, Store

OMR_LOCK = threading.Lock()  # PDFium and OpenCV's RNG are shared process resources.
STATIC = Path(__file__).with_name("static")
TORPH_STYLE_HASH = (STATIC / "vendor" / "torph-style-hash.txt").read_text().strip()


class ExamUpdate(ConfigModel):
    expected_revision: int = Field(strict=True, ge=1)
    exam: Assessment


def create_app(
    data_dir: Path,
    template_paths: list[Path] | None = None,
    *,
    development: bool = False,
    external_origin: str | None = None,
) -> FastAPI:
    data_dir = data_dir.resolve()
    store = Store(data_dir)
    if not template_paths:
        demo_dir = data_dir / "demo"
        if not demo_dir.exists():
            create_demo(demo_dir)
        template_paths = [demo_dir / "template.json"]
    engines = {}
    for path in template_paths:
        engine = Engine.from_file(path)
        if engine.template.template_id in engines:
            raise ValueError("Duplicate template identifier")
        engines[engine.template.template_id] = engine

    app = FastAPI(title="PsychoMark", docs_url=None, redoc_url=None)
    app.state.store = store
    app.state.engines = engines

    @app.get("/api/health")
    def health():
        return {"app": "psychomark", "development": development}

    if development:

        @app.get("/api/dev/revision")
        def revision():
            return {"revision": source_revision(Path(__file__).parent)}

    @app.middleware("http")
    async def local_headers(request: Request, call_next):
        # No cross-origin writes to this unauthenticated local prototype.
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            allowed_origins = {str(request.base_url).rstrip("/")}
            if external_origin:
                allowed_origins.add(external_origin)
            if origin and origin.rstrip("/") not in allowed_origins:
                return JSONResponse(
                    {"detail": "Origine de requête non autorisée."}, status_code=403
                )
            length = request.headers.get("content-length", "0")
            if not length.isdigit() or int(length) > MAX_FILE_BYTES + 1024 * 1024:
                return JSONResponse(
                    {"detail": "Le fichier dépasse la limite de 64 Mio."}, status_code=413
                )
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; "
            f"style-src 'self' 'sha256-{TORPH_STYLE_HASH}'; "
            "img-src 'self' blob:; object-src 'none'; frame-ancestors 'none'; base-uri 'self'"
        )
        return response

    @app.exception_handler(KeyError)
    async def missing(request, exc):
        return JSONResponse({"detail": "Élément introuvable."}, status_code=404)

    @app.exception_handler(Conflict)
    async def conflict(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=409)

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=422)

    def get_engine(identifier):
        if identifier not in engines:
            raise HTTPException(422, "Ce modèle de feuille n’est pas disponible sur ce serveur.")
        return engines[identifier]

    def copy_response(identifier, full=True):
        item = store.get_copy(identifier)
        result = grade(
            Assessment.model_validate(item["exam_snapshot"]), item["extraction"], item["reviews"]
        )
        response = {
            "id": item["id"],
            "exam_id": item["exam_id"],
            "exam_revision": item["exam_revision"],
            "filename": item["filename"],
            "page": item["page"],
            "revision": item["revision"],
            "created_at": item["created_at"],
            "grade": result,
            "aligned": "registration" in item["extraction"].get("diagnostics", {}),
        }
        if full:
            response.update(
                {
                    "exam": item["exam_snapshot"],
                    "extraction": item["extraction"],
                    "reviews": item["reviews"],
                    "history": store.history(identifier),
                    "choices": {s["id"]: s["choices"] for s in item["layout"]["sections"]},
                }
            )
        else:
            result.pop("rows")
        return response

    def process_file(exam_record, path, filename):
        assessment = Assessment.model_validate(exam_record["exam"])
        engine = get_engine(assessment.template_id)
        created, errors = [], []
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        with OMR_LOCK:
            for page in iter_pages(path):
                if page.error:
                    errors.append({"page": page.number, "message": page.error})
                    continue
                extraction, annotated = engine.analyze(page.image, assessment.selection())
                extraction["file_sha256"] = digest
                identifier = uuid.uuid4().hex
                destination = data_dir / "copies" / identifier
                destination.mkdir(parents=True)
                try:
                    save_image(destination / "original.png", page.image)
                    save_image(destination / "annotated.png", annotated)
                    registration = extraction.get("diagnostics", {}).get("registration")
                    if registration:
                        transform = np.array(registration["input_to_reference"])
                        aligned = cv2.warpPerspective(
                            page.image,
                            transform,
                            (engine.template.width, engine.template.height),
                            borderValue=(255,) * 3,
                        )
                        save_image(destination / "aligned.png", aligned)
                    layout = Layout.model_validate(
                        engine.template.model_dump(exclude={"reference", "reference_sha256"})
                    )
                    store.create_copy(
                        identifier,
                        exam_record,
                        layout.model_dump(),
                        filename,
                        page.number,
                        extraction,
                    )
                except Exception:
                    shutil.rmtree(destination)
                    raise
                created.append(copy_response(identifier, full=False))
        return {"copies": created, "errors": errors}

    @app.get("/api/templates")
    def templates():
        return [
            {
                "id": identifier,
                "synthetic": identifier.startswith("demo_"),
                "sections": [
                    {"id": s.id, "questions": s.questions, "choices": s.choices}
                    for s in e.template.sections
                ],
            }
            for identifier, e in engines.items()
        ]

    @app.get("/api/exams")
    def list_exams():
        return store.list_exams()

    @app.post("/api/exams", status_code=201)
    def new_exam(exam: Assessment):
        exam.validate_for(get_engine(exam.template_id).template)
        return store.create_exam(exam.model_dump())

    @app.get("/api/exams/{identifier}")
    def get_exam(identifier: str):
        return dict(
            store.get_exam(identifier),
            copies=[copy_response(cid, full=False) for cid in store.copy_ids(identifier)],
        )

    @app.put("/api/exams/{identifier}")
    def update_exam(identifier: str, update: ExamUpdate):
        store.get_exam(identifier)
        update.exam.validate_for(get_engine(update.exam.template_id).template)
        return store.update_exam(identifier, update.exam.model_dump(), update.expected_revision)

    @app.post("/api/exams/{identifier}/copies")
    def upload(identifier: str, file: UploadFile = File()):
        record = store.get_exam(identifier)
        filename = (file.filename or "copie").replace("\\", "/").split("/")[-1][:200]
        suffix = Path(filename).suffix.lower()
        if suffix not in SUPPORTED:
            raise HTTPException(
                422, "Format non pris en charge. Utilise une image JPG, PNG, TIFF ou un PDF."
            )
        directory = data_dir / "incoming"
        directory.mkdir(exist_ok=True)
        path = directory / (uuid.uuid4().hex + suffix)
        try:
            with path.open("xb") as handle:
                size = 0
                while chunk := file.file.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_FILE_BYTES:
                        raise HTTPException(413, "Le fichier dépasse la limite de 64 Mio.")
                    handle.write(chunk)
            return process_file(record, path, filename)
        finally:
            file.file.close()
            path.unlink(missing_ok=True)

    @app.post("/api/demo")
    def demo():
        engine = engines.get("demo_eight_sections_v1")
        if not engine:
            raise HTTPException(
                422, "La démonstration nécessite le modèle de démonstration par défaut."
            )
        # This key is used exclusively for marking, never by Engine.analyze.
        assessment = Assessment(
            name="Examen de démonstration",
            template_id=engine.template.template_id,
            sections={"1": list(range(1, 13)), "8": list(range(1, 9))},
            answer_key={
                sid: {str(q): ((q + index) % 4) + 1 for q in range(1, n + 1)}
                for sid, index, n in [("1", 0, 12), ("8", 7, 8)]
            },
        )
        assessment.validate_for(engine.template)
        record = store.create_exam(assessment.model_dump())
        demo_dir = data_dir / "demo"
        if not demo_dir.exists():
            create_demo(demo_dir)
        return dict(
            process_file(record, demo_dir / "copy.png", "copie-demonstration.png"),
            exam_id=record["id"],
        )

    @app.get("/api/copies/{identifier}")
    def get_copy(identifier: str):
        return copy_response(identifier)

    @app.patch("/api/copies/{identifier}/reviews")
    def review_copy(identifier: str, review: Review):
        item = store.get_copy(identifier)
        review.validate_for(
            Assessment.model_validate(item["exam_snapshot"]), Layout.model_validate(item["layout"])
        )
        store.review(identifier, review)
        return copy_response(identifier)

    @app.get("/api/copies/{identifier}/image/{view}")
    def image(identifier: str, view: str):
        store.get_copy(identifier)
        if view not in {"original", "annotated", "aligned"}:
            raise HTTPException(404)
        path = data_dir / "copies" / identifier / f"{view}.png"
        if not path.is_file():
            raise HTTPException(404)
        return FileResponse(path, media_type="image/png")

    @app.get("/api/copies/{identifier}/crop/{section}/{question}")
    def crop(identifier: str, section: str, question: int):
        item = store.get_copy(identifier)
        if question not in item["exam_snapshot"]["sections"].get(section, []):
            raise HTTPException(404)
        path = data_dir / "copies" / identifier / "aligned.png"
        if not path.exists():
            raise HTTPException(422, "L’alignement a échoué. Consulte l’image complète.")
        layout = Layout.model_validate(item["layout"])
        s = next(s for s in layout.sections if s.id == section)
        centers = [s.center(question, c) for c in range(1, s.choices + 1)]
        rx, ry = s.bubble_radius
        # Keep context without showing marks belonging to the adjacent question.
        pad_x = (
            min(12, max(1, (abs(s.question_step[0]) - 2 * rx) / 2 - 1))
            if s.question_step[1] == 0
            else 12
        )
        pad_y = (
            min(12, max(1, (abs(s.question_step[1]) - 2 * ry) / 2 - 1))
            if s.question_step[0] == 0
            else 12
        )
        x0 = max(0, int(min(p[0] for p in centers) - rx - pad_x))
        x1 = min(layout.width, int(max(p[0] for p in centers) + rx + pad_x + 1))
        y0 = max(0, int(min(p[1] for p in centers) - ry - pad_y))
        y1 = min(layout.height, int(max(p[1] for p in centers) + ry + pad_y + 1))
        cropped = read_image(path)[y0:y1, x0:x1]
        ok, encoded = cv2.imencode(".png", cropped)
        if not ok:
            raise HTTPException(500, "Impossible de créer l’extrait.")
        return Response(encoded.tobytes(), media_type="image/png")

    @app.get("/api/copies/{identifier}/export/{format}")
    def export(identifier: str, format: str):
        result = copy_response(identifier)
        if format == "json":
            data, mime = json.dumps(result, indent=2, ensure_ascii=False), "application/json"
        elif format == "csv":
            buffer = io.StringIO()
            writer = csv.DictWriter(
                buffer,
                fieldnames=[
                    "section",
                    "question",
                    "expected",
                    "detected_status",
                    "detected_answer",
                    "answer",
                    "verdict",
                    "reviewed",
                ],
            )
            writer.writeheader()
            for row in result["grade"]["rows"]:
                writer.writerow({k: row[k] for k in writer.fieldnames})
            data, mime = "\ufeff" + buffer.getvalue(), "text/csv"
        else:
            raise HTTPException(404)
        return Response(
            data,
            media_type=mime,
            headers={
                "Content-Disposition": f'attachment; filename="correction-{identifier}.{format}"'
            },
        )

    app.mount("/assets", StaticFiles(directory=STATIC), name="assets")

    @app.get("/")
    def index():
        if development:
            html = (STATIC / "index.html").read_text(encoding="utf-8")
            return HTMLResponse(
                html.replace("</body>", '<script src="/assets/live.js" defer></script></body>')
            )
        return FileResponse(STATIC / "index.html")

    return app


def development_app():
    configuration = json.loads(os.environ["PSYCHOMARK_WEB_CONFIG"])
    cv2.setNumThreads(2)
    paths = [Path(p) for p in configuration["templates"]] or None
    return create_app(
        Path(configuration["data_dir"]),
        paths,
        development=True,
        external_origin=configuration["external_origin"],
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description="Interface locale PsychoMark")
    parser.add_argument("--data-dir", type=Path, default=Path("artifacts/web"))
    parser.add_argument(
        "--template", type=Path, action="append", help="Modèle calibré ; peut être répété"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Recharger le serveur et le navigateur après une modification",
    )
    args = parser.parse_args(argv)
    cv2.setNumThreads(2)
    import uvicorn

    external_origin = codespaces_origin(args.port)
    if args.reload:
        os.environ["PSYCHOMARK_WEB_CONFIG"] = json.dumps(
            {
                "data_dir": str(args.data_dir.resolve()),
                "templates": [str(p.resolve()) for p in args.template or []],
                "external_origin": external_origin,
            }
        )
        uvicorn.run(
            "psychomark.web:development_app",
            factory=True,
            reload=True,
            reload_dirs=[str(Path(__file__).parent)],
            host=args.host,
            port=args.port,
        )
    else:
        uvicorn.run(
            create_app(args.data_dir, args.template, external_origin=external_origin),
            host=args.host,
            port=args.port,
        )


if __name__ == "__main__":
    main()
