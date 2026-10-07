import copy
import io

import cv2
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from psychomark.web import create_app


@pytest.fixture
def client(sheet, tmp_path):
    with TestClient(create_app(tmp_path / "web", [sheet["template_path"]])) as client:
        yield client


def payload(sheet):
    return {
        "name": "Examen blanc",
        "template_id": sheet["layout"].template_id,
        "sections": {"1": [1, 2, 3, 4, 5]},
        "answer_key": {"1": {"1": 2, "2": 1, "3": 1, "4": 2, "5": 3}},
    }


def create_exam(client, sheet):
    response = client.post("/api/exams", json=payload(sheet))
    assert response.status_code == 201, response.text
    return response.json()


def upload(client, sheet, identifier):
    success, data = cv2.imencode(".png", sheet["filled"])
    assert success
    response = client.post(
        f"/api/exams/{identifier}/copies",
        files={"file": ("student.png", data.tobytes(), "image/png")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["errors"] == []
    return response.json()["copies"][0]


def test_complete_workflow_upload_review_export_and_revert(client, sheet):
    exam = create_exam(client, sheet)
    record = upload(client, sheet, exam["id"])
    url = f"/api/copies/{record['id']}"
    initial = client.get(url).json()
    assert initial["grade"]["pending"] == 2
    assert initial["grade"]["correct"] == 1
    assert initial["grade"]["incorrect"] == 1
    assert initial["grade"]["blank"] == 1
    assert initial["grade"]["out_of_20"] is None
    for q, revision in [(3, 1), (4, 2)]:
        answer = payload(sheet)["answer_key"]["1"][str(q)]
        result = client.patch(
            url + "/reviews",
            json={
                "expected_revision": revision,
                "section": "1",
                "question": q,
                "decision": "choice",
                "answer": answer,
            },
        )
        assert result.status_code == 200, result.text
    final = result.json()
    assert final["grade"]["out_of_20"] == 12
    assert final["grade"]["percentage"] == 60
    assert final["grade"]["status"] == "final"
    assert final["extraction"] == initial["extraction"]
    assert len(final["history"]) == 2
    assert client.get(url + "/image/original").headers["content-type"] == "image/png"
    crop = client.get(url + "/crop/1/3")
    assert crop.status_code == 200
    with Image.open(io.BytesIO(crop.content)) as image:
        assert image.width <= 27  # No neighbouring question's marks in the review crop.
    assert client.get(url + "/crop/1/99").status_code == 404
    export = client.get(url + "/export/json")
    assert export.json()["grade"]["out_of_20"] == 12
    assert "attachment" in export.headers["content-disposition"]
    csv = client.get(url + "/export/csv")
    assert "expected,detected_status" in csv.text
    reverted = client.patch(
        url + "/reviews",
        json={"expected_revision": 3, "section": "1", "question": 3, "decision": "automatic"},
    ).json()
    assert reverted["grade"]["pending"] == 1
    assert reverted["grade"]["out_of_20"] is None
    assert len(reverted["history"]) == 3


def test_exam_edits_do_not_retroactively_change_existing_grades(client, sheet):
    exam = create_exam(client, sheet)
    first = upload(client, sheet, exam["id"])
    changed = copy.deepcopy(exam["exam"])
    changed["name"] = "Nouveau corrigé"
    changed["answer_key"]["1"]["1"] = 1
    updated = client.put(f"/api/exams/{exam['id']}", json={"expected_revision": 1, "exam": changed})
    assert updated.status_code == 200
    second = upload(client, sheet, exam["id"])
    previous = client.get(f"/api/copies/{first['id']}").json()
    current = client.get(f"/api/copies/{second['id']}").json()
    assert previous["exam_revision"] == 1 and current["exam_revision"] == 2
    assert previous["grade"]["correct"] == 1 and current["grade"]["correct"] == 0
    assert previous["exam"]["name"] == "Examen blanc"


def test_stale_edits_and_reviews_are_rejected(client, sheet):
    exam = create_exam(client, sheet)
    record = upload(client, sheet, exam["id"])
    url = f"/api/copies/{record['id']}"
    body = {"expected_revision": 1, "section": "1", "question": 3, "decision": "blank"}
    assert client.patch(url + "/reviews", json=body).status_code == 200
    assert client.patch(url + "/reviews", json=body).status_code == 409
    assert len(client.get(url).json()["history"]) == 1
    edit = {"expected_revision": 1, "exam": exam["exam"]}
    assert client.put(f"/api/exams/{exam['id']}", json=edit).status_code == 200
    assert client.put(f"/api/exams/{exam['id']}", json=edit).status_code == 409


def test_web_supports_pdf_pages(client, sheet):
    exam = create_exam(client, sheet)
    blank = Image.fromarray(cv2.cvtColor(sheet["blank"], cv2.COLOR_BGR2RGB))
    filled = Image.fromarray(cv2.cvtColor(sheet["filled"], cv2.COLOR_BGR2RGB))
    content = io.BytesIO()
    blank.save(content, format="PDF", save_all=True, append_images=[filled], resolution=200)
    response = client.post(
        f"/api/exams/{exam['id']}/copies",
        files={"file": ("copies.pdf", content.getvalue(), "application/pdf")},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["errors"] == []
    assert [c["page"] for c in result["copies"]] == [1, 2]
    assert result["copies"][0]["grade"]["out_of_20"] == 0
    assert result["copies"][1]["grade"]["pending"] == 2


def test_bad_inputs_report_errors_without_making_fake_copies(client, sheet):
    exam = create_exam(client, sheet)
    url = f"/api/exams/{exam['id']}"
    response = client.post(
        url + "/copies", files={"file": ("bad.png", b"not an image", "image/png")}
    )
    assert response.status_code == 200
    assert response.json()["errors"] and not response.json()["copies"]
    assert client.get(url).json()["copies"] == []
    assert (
        client.post(url + "/copies", files={"file": ("bad.html", b"x", "text/html")}).status_code
        == 422
    )
    assert (
        client.post(
            url + "/copies", content=b"x", headers={"content-length": str(70 * 1024 * 1024)}
        ).status_code
        == 413
    )


def test_invalid_key_and_cross_origin_requests_rejected(client, sheet):
    invalid = payload(sheet)
    del invalid["answer_key"]["1"]["3"]
    assert client.post("/api/exams", json=invalid).status_code == 422
    assert (
        client.post(
            "/api/exams", json=payload(sheet), headers={"origin": "https://another-site.example"}
        ).status_code
        == 403
    )
    assert client.get("/api/exams").json() == []


def test_invalid_manual_question_or_choice_rejected(client, sheet):
    exam = create_exam(client, sheet)
    record = upload(client, sheet, exam["id"])
    url = f"/api/copies/{record['id']}/reviews"
    for q, answer in [(30, 1), (1, 5)]:
        response = client.patch(
            url,
            json={
                "expected_revision": 1,
                "section": "1",
                "question": q,
                "decision": "choice",
                "answer": answer,
            },
        )
        assert response.status_code == 422


def test_restart_preserves_exams_and_corrections(sheet, tmp_path):
    root = tmp_path / "persistent"
    with TestClient(create_app(root, [sheet["template_path"]])) as client:
        exam = create_exam(client, sheet)
        record = upload(client, sheet, exam["id"])
    with TestClient(create_app(root, [sheet["template_path"]])) as client:
        assert client.get(f"/api/exams/{exam['id']}").json()["copies"][0]["id"] == record["id"]
        assert client.get(f"/api/copies/{record['id']}").json()["grade"]["pending"] == 2


def test_static_interface_and_demo_end_to_end(client):
    html = client.get("/")
    assert html.status_code == 200 and '<html lang="fr">' in html.text
    assert client.get("/assets/app.js").status_code == 200
    response = client.post("/api/demo")
    assert response.status_code == 200, response.text
    copy = response.json()["copies"][0]
    assert copy["grade"]["total"] == 20 and copy["grade"]["pending"] == 6
    assert copy["grade"]["correct"] == 12
