"""Exercise calibration, persistence and exam use through the public web API."""

import copy
import io

import cv2
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from psychomark.web import create_app


@pytest.fixture
def client(sheet, tmp_path):
    with TestClient(create_app(tmp_path / "web", [sheet["template_path"]])) as value:
        yield value


def file_body(image):
    return {"file": ("blank.png", cv2.imencode(".png", image)[1].tobytes(), "image/png")}


def draft(client, sheet):
    response = client.post("/api/sheets", files=file_body(sheet["blank"]))
    assert response.status_code == 200, response.text
    item = response.json()
    body = {
        "expected_revision": item["revision"],
        "name": "Feuille de test",
        "sections": [section.model_dump() for section in sheet["layout"].sections],
    }
    return f"/api/sheets/{item['id']}", item, body


def checked(client, sheet):
    url, item, body = draft(client, sheet)
    response = client.put(url + "/calibration", json=body)
    assert response.status_code == 200, response.text
    return url, response.json(), body


def test_new_template_reads_and_grades_then_survives_restart(client, sheet, tmp_path):
    url, item, body = checked(client, sheet)
    identifier = item["id"]
    assert identifier not in {t["id"] for t in client.get("/api/templates").json()}
    preview = client.get(url + "/image/preview")
    assert preview.status_code == 200
    result = client.post(
        url + f"/test?revision={item['revision']}", files=file_body(sheet["filled"])
    )
    assert result.status_code == 200, result.text
    extraction = result.json()["extraction"]
    baseline, _ = sheet["engine"].analyze(sheet["filled"])
    assert extraction["answers"] == baseline["answers"]
    assert "grade" not in result.json()
    assert client.get("/api/exams").json() == []
    assert client.get(url + "/test").json() == extraction
    assert client.get(url + "/image/original").status_code == 200
    published = client.post(
        url + "/publish", json={"expected_revision": item["revision"], "checked_overlay": True}
    )
    assert published.status_code == 200, published.text
    assert (
        next(t for t in client.get("/api/templates").json() if t["id"] == identifier)["name"]
        == body["name"]
    )
    with TestClient(create_app(tmp_path / "web", [sheet["template_path"]])) as restarted:
        assert restarted.get(url).json()["published"]
        exam = restarted.post(
            "/api/exams",
            json={
                "name": "Examen court",
                "template_id": identifier,
                "sections": {"1": [1, 2]},
                "answer_key": {"1": {"1": 2, "2": 1}},
            },
        )
        assert exam.status_code == 201, exam.text
        result = restarted.post(
            f"/api/exams/{exam.json()['id']}/copies", files=file_body(sheet["filled"])
        )
        assert result.status_code == 200, result.text
        assert result.json()["copies"][0]["grade"]["total"] == 2
        assert result.json()["copies"][0]["grade"]["correct"] == 1


def test_invalid_update_keeps_last_calibration_and_optimistic_revision(client, sheet):
    url, item, body = checked(client, sheet)
    assert client.put(url + "/calibration", json=body).status_code == 409
    body["expected_revision"] = item["revision"]
    body["sections"][1] = copy.deepcopy(body["sections"][0])
    body["sections"][1]["id"] = "different"
    assert client.put(url + "/calibration", json=body).status_code == 422
    assert client.get(url).json() == item
    assert client.get(url + "/image/preview").status_code == 200
    body["sections"] = [s.model_dump() for s in sheet["layout"].sections]
    body["sections"][0]["first_center"] = [-100, 320]
    assert client.put(url + "/calibration", json=body).status_code == 422
    assert client.get(url).json() == item


def test_publish_requires_overlay_and_freezes_positions(client, sheet):
    url, item, body = draft(client, sheet)
    assert (
        client.post(
            url + "/publish", json={"expected_revision": 1, "checked_overlay": True}
        ).status_code
        == 422
    )
    item = client.put(url + "/calibration", json=body).json()
    request = {"expected_revision": item["revision"], "checked_overlay": False}
    assert client.post(url + "/publish", json=request).status_code == 422
    request["checked_overlay"] = True
    saved = client.post(url + "/publish", json=request).json()
    body["expected_revision"] = saved["revision"]
    assert client.put(url + "/calibration", json=body).status_code == 409
    assert client.get(url).json() == saved
    assert (
        client.post(url + "/test?revision=1", files=file_body(sheet["filled"])).status_code == 409
    )


def test_changed_calibration_invalidates_previous_test(client, sheet):
    url, item, body = checked(client, sheet)
    assert (
        client.post(
            url + f"/test?revision={item['revision']}", files=file_body(sheet["filled"])
        ).status_code
        == 200
    )
    body["expected_revision"] = item["revision"]
    body["sections"] = body["sections"][:1]
    changed = client.put(url + "/calibration", json=body)
    assert changed.status_code == 200, changed.text
    assert changed.json()["test"] is None
    assert client.get(url + "/test").status_code == 404
    assert client.get(url + "/image/test").status_code == 404


def test_bad_upload_and_multiple_pages_leave_no_drafts(client, sheet, tmp_path):
    for filename, content in [("file.exe", b"x"), ("file.png", b"not an image")]:
        response = client.post("/api/sheets", files={"file": (filename, content)})
        assert response.status_code == 422, response.text
    buffer = io.BytesIO()
    image = Image.fromarray(cv2.cvtColor(sheet["blank"], cv2.COLOR_BGR2RGB))
    image.save(buffer, format="PDF", save_all=True, append_images=[image])
    response = client.post("/api/sheets", files={"file": ("two.pdf", buffer.getvalue())})
    assert response.status_code == 422
    assert "une seule page" in response.json()["detail"]
    assert client.get("/api/sheets").json() == []
    assert list((tmp_path / "web" / "sheets").iterdir()) == []
    assert client.get("/api/sheets/unknown").status_code == 404
    assert (
        client.post(
            "/api/sheets",
            files=file_body(sheet["blank"]),
            headers={"Origin": "https://elsewhere.test"},
        ).status_code
        == 403
    )


def test_filled_reference_is_rejected_without_publishing(client, sheet):
    response = client.post("/api/sheets", files=file_body(sheet["filled"]))
    item = response.json()
    response = client.put(
        f"/api/sheets/{item['id']}/calibration",
        json={
            "expected_revision": 1,
            "name": "Not blank",
            "sections": [s.model_dump() for s in sheet["layout"].sections],
        },
    )
    assert response.status_code == 422
    assert client.get(f"/api/sheets/{item['id']}").json()["calibration"] is None
