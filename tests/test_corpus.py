import hashlib
import io
import json
import threading
import zipfile

import cv2
import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from psychomark.config import Exam
from psychomark.corpus import corpus_router
from psychomark.store import Conflict


def client_for(root, sheet):
    app = FastAPI()
    app.include_router(
        corpus_router(
            root, {sheet["engine"].template.template_id: sheet["engine"]}, threading.Lock()
        )
    )

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=422)

    @app.exception_handler(KeyError)
    async def missing(request, exc):
        return JSONResponse({"detail": "missing"}, status_code=404)

    @app.exception_handler(Conflict)
    async def conflict(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=409)

    return TestClient(app)


def png(image, compression=3):
    return cv2.imencode(".png", image, [cv2.IMWRITE_PNG_COMPRESSION, compression])[1].tobytes()


def diagnostic(sheet, image=None, mutate=None):
    reference = png(sheet["blank"])
    template = sheet["engine"].template.model_dump()
    template.update(
        reference="template.reference.png", reference_sha256=hashlib.sha256(reference).hexdigest()
    )
    exam = Exam(template_id=template["template_id"], sections={"1": [1, 2]}).model_dump()
    files = {
        "template.json": json.dumps(template).encode(),
        "template.reference.png": reference,
        "copy.png": png(sheet["filled"] if image is None else image),
        "result.json": json.dumps(
            {"exam": exam, "answer_key": "SHOULD_NEVER_APPEAR", "answers": []}
        ).encode(),
        "README.txt": b"ignored text is not an instruction",
    }
    if mutate:
        mutate(files)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return output.getvalue()


def upload(client, data, **options):
    return client.post(
        "/api/corpus",
        files={"file": ("diagnostic.zip", data, "application/zip")},
        data={"physical_sheet_id": "sheet-1", **options},
    )


def label(item, **changes):
    return {
        "expected_revision": item["revision"],
        "section": "1",
        "question": 1,
        "reviewer": "teacher-A",
        "status": "single",
        "choices": [2],
        "marks": ["empty", "marked", "empty", "empty"],
        "geometry": "confirmed",
        "manual_bounds": None,
        "notes": "",
        **changes,
    }


def test_diagnostic_annotation_restart_export_and_revision(sheet, tmp_path):
    client = client_for(tmp_path, sheet)
    response = upload(client, diagnostic(sheet), split="test", training_allowed="true")
    assert response.status_code == 200, response.text
    item = response.json()
    assert item["split"] == "development"
    assert item["total"] == 2 and item["completed"] == 0
    assert all(q["annotation"] is None for q in item["questions"])
    assert item["aligned"]
    url = f"/api/corpus/{item['id']}"
    assert client.get(url + "/crop/1/1").status_code == 200
    payload = label(item)
    updated = client.patch(url + "/annotations", json=payload).json()
    assert updated["revision"] == 2 and updated["completed"] == 1
    assert updated["history"][0]["before"] is None
    assert client.patch(url + "/annotations", json=payload).status_code == 409
    restarted = client_for(tmp_path, sheet)
    assert restarted.get(url).json() == updated
    export = restarted.get("/api/corpus/export").json()["acquisitions"][0]
    assert not export["eligible_for_training"]
    assert not export["ready_for_evaluation"]
    assert export["provenance"]["decoded_pixel_sha256"]
    archive = zipfile.ZipFile(io.BytesIO(restarted.get(url + "/export").content))
    assert "source.png" in archive.namelist()
    assert "extraction.json" not in archive.namelist()
    regions = json.loads(archive.read("regions.json"))
    assert regions["source_size"] == item["source_size"]
    assert np.allclose(
        np.array(regions["input_to_reference"]) @ np.array(regions["reference_to_input"]),
        np.eye(3),
    )
    assert regions["valid_mask"] in archive.namelist()
    for response in (restarted.get(url), restarted.get("/api/corpus/export")):
        assert "SHOULD_NEVER_APPEAR" not in response.text
        assert '"scores"' not in response.text and '"answer_key"' not in response.text
    assert "SHOULD_NEVER_APPEAR" not in archive.read("manifest.json").decode()


def test_all_states_and_strict_mark_consistency(sheet, tmp_path):
    client = client_for(tmp_path, sheet)
    item = upload(client, diagnostic(sheet)).json()
    url = f"/api/corpus/{item['id']}/annotations"
    for status, marks, choices in (
        ("blank", ["empty"] * 4, []),
        ("multiple", ["marked", "marked", "empty", "empty"], [1, 2]),
        ("uncertain", ["ambiguous", "marked", "empty", "empty"], [2]),
        ("unreadable", ["unreadable", "marked", "empty", "empty"], [2]),
        ("single", ["empty", "marked", "empty", "empty"], [2]),
    ):
        response = client.patch(url, json=label(item, status=status, marks=marks, choices=choices))
        assert response.status_code == 200, response.text
        item = response.json()
    for changes in (
        {"status": "blank"},
        {"choices": [2, 2]},
        {"choices": [1]},
        {"reviewer": ""},
        {"marks": ["empty", "marked"]},
        {"question": 30},
        {"manual_bounds": [1, 2, 3]},
        {"manual_bounds": [0, 0, 50000, 40]},
        {"manual_bounds": [1.5, 2, 3, 4]},
        {"manual_bounds": [10, 2, 3, 4]},
    ):
        assert client.patch(url, json=label(item, **changes)).status_code in {404, 422}
    assert client.get(f"/api/corpus/{item['id']}").json()["revision"] == item["revision"]


def test_duplicate_pixels_and_group_splits(sheet, tmp_path):
    client = client_for(tmp_path, sheet)
    image = sheet["filled"].copy()
    tid = sheet["engine"].template.template_id

    def send(image, physical="p1", group="g1", split="train", compression=3):
        return client.post(
            "/api/corpus",
            files={"file": ("copy.png", png(image, compression))},
            data={
                "physical_sheet_id": physical,
                "group_id": group,
                "split": split,
                "template_id": tid,
            },
        )

    assert send(image).status_code == 200
    assert send(image, physical="p2", group="g2", compression=9).status_code == 409
    image[0, 0] = 0
    assert send(image, physical="p2", split="test").status_code == 409
    assert send(image, group="different").status_code == 409
    assert send(image).status_code == 200


def test_failed_alignment_manual_crops_and_no_fake_geometry(sheet, tmp_path):
    client = client_for(tmp_path, sheet)
    image = np.full_like(sheet["blank"], 255)
    item = upload(client, diagnostic(sheet, image)).json()
    assert not item["aligned"]
    assert not any(q["has_crop"] for q in item["questions"])
    url = f"/api/corpus/{item['id']}"
    assert client.get(url + "/crop/1/1").status_code == 404
    assert client.get(url + "/crop/1/1?view=reference").status_code == 200
    assert client.patch(url + "/annotations", json=label(item)).status_code == 422
    response = client.patch(url + "/annotations", json=label(item, geometry="source_only"))
    assert response.status_code == 200
    item = response.json()
    assert not item["questions"][0]["has_crop"]
    response = client.patch(url + "/annotations", json=label(item, manual_bounds=[10, 20, 40, 60]))
    assert response.status_code == 200
    item = response.json()
    crop = cv2.imdecode(np.frombuffer(client.get(url + "/crop/1/1").content, np.uint8), 1)
    assert crop.shape[:2] == (40, 30)
    assert item["questions"][0]["has_crop"]
    bundle = zipfile.ZipFile(io.BytesIO(client.get(url + "/export").content))
    assert "manual/0001.png" in bundle.namelist()
    regions = json.loads(bundle.read("regions.json"))
    assert regions["input_to_reference"] is None
    assert regions["reference_to_input"] is None
    assert regions["valid_mask"] is None
    assert "valid.png" not in bundle.namelist()
    manifest = json.loads(bundle.read("manifest.json"))
    assert not manifest["eligible_for_training"]
    assert manifest["questions"][0]["annotation"]["manual_bounds"] == [10, 20, 40, 60]


@pytest.mark.parametrize(
    "problem", ["traversal", "checksum", "reference", "selection", "unknown", "non_object"]
)
def test_diagnostic_validation(sheet, tmp_path, problem):
    client = client_for(tmp_path, sheet)

    def mutate(files):
        if problem == "traversal":
            files["../escape"] = b"data"
        elif problem in {"checksum", "reference"}:
            template = json.loads(files["template.json"])
            template["reference_sha256" if problem == "checksum" else "reference"] = (
                "0" * 64 if problem == "checksum" else "../template.reference.png"
            )
            files["template.json"] = json.dumps(template).encode()
        elif problem == "non_object":
            files["result.json"] = b"[]"
        else:
            result = json.loads(files["result.json"])
            if problem == "selection":
                result["exam"]["sections"] = {"1": [999]}
            else:
                result["exam"]["answer_key"] = {"1": [1]}
            files["result.json"] = json.dumps(result).encode()

    response = upload(client, diagnostic(sheet, mutate=mutate))
    assert response.status_code == 422, response.text
    assert client.get("/api/corpus").json() == []
    assert list((tmp_path / "corpus").iterdir()) == []


def test_train_permission_complete_geometry_and_manual_override(sheet, tmp_path, monkeypatch):
    engine = sheet["engine"]
    analyze = engine.analyze
    selection = Exam(template_id=engine.template.template_id, sections={"1": [1, 2]})
    monkeypatch.setattr(engine, "analyze", lambda image, exam=None: analyze(image, selection))
    for consent in (False, True):
        client = client_for(tmp_path / str(consent), sheet)
        response = client.post(
            "/api/corpus",
            files={"file": ("copy.png", png(sheet["filled"]))},
            data={
                "physical_sheet_id": "p1",
                "split": "train",
                "training_allowed": str(consent).lower(),
                "template_id": engine.template.template_id,
            },
        )
        assert response.status_code == 200, response.text
        item = response.json()
        url = f"/api/corpus/{item['id']}"
        for number in (1, 2):
            response = client.patch(url + "/annotations", json=label(item, question=number))
            assert response.status_code == 200
            item = response.json()
        manifest = client.get("/api/corpus/export").json()["acquisitions"][0]
        assert manifest["eligible_for_training"] is consent
        assert manifest["ready_for_evaluation"] is True
        item = client.patch(url + "/annotations", json=label(item, geometry="incorrect")).json()
        assert not client.get("/api/corpus/export").json()["acquisitions"][0][
            "eligible_for_training"
        ]
        # A human replacement crop takes precedence over an existing automatic crop.
        response = client.patch(
            url + "/annotations", json=label(item, manual_bounds=[0, 0, 10, 20])
        )
        assert response.status_code == 200
        image = cv2.imdecode(np.frombuffer(client.get(url + "/crop/1/1").content, np.uint8), 1)
        assert image.shape[:2] == (20, 10)
        assert (
            client.get("/api/corpus/export").json()["acquisitions"][0]["questions"][0]["assets"][
                "copy"
            ]
            == "manual/0001.png"
        )


@pytest.mark.parametrize("kind", ["duplicate", "symlink", "expanded"])
def test_rejects_unsafe_zip_members(sheet, tmp_path, monkeypatch, kind):
    client = client_for(tmp_path, sheet)
    original = zipfile.ZipFile(io.BytesIO(diagnostic(sheet)))
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in original.namelist():
            if kind == "symlink" and name == "copy.png":
                info = zipfile.ZipInfo(name)
                info.create_system = 3
                info.external_attr = 0o120777 << 16
                archive.writestr(info, b"/etc/passwd")
            else:
                archive.writestr(name, original.read(name))
        if kind == "duplicate":
            with pytest.warns(UserWarning, match="Duplicate"):
                archive.writestr("copy.png", b"duplicate")
    if kind == "expanded":
        monkeypatch.setattr("psychomark.corpus.MAX_EXPANDED_BYTES", 10)
    assert upload(client, buffer.getvalue()).status_code == 422
    assert client.get("/api/corpus").json() == []
