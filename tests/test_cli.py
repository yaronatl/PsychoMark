import csv
import json

import cv2
from PIL import Image

from psychomark.cli import main
from psychomark.images import save_image


def test_cli_writes_consistent_json_csv_preview_and_summary(sheet, tmp_path):
    source = tmp_path / "copy.png"
    save_image(source, sheet["filled"])
    output = tmp_path / "results"
    exam = tmp_path / "exam.json"
    exam.write_text(
        json.dumps({"template_id": sheet["layout"].template_id, "sections": {"1": [1, 3, 4, 5]}})
    )
    args = [
        "analyze",
        str(source),
        "--template",
        str(sheet["template_path"]),
        "--exam",
        str(exam),
        "--output",
        str(output),
    ]
    assert main(args) == 0  # Completed extraction, but manual review is explicitly required.
    result = json.loads((output / "001-copy-page001.json").read_text())
    assert result["status"] == "needs_review"
    assert len(result["answers"]) == 4
    assert result["file_sha256"] and result["reference_sha256"]
    with (output / "001-copy-page001.csv").open() as f:
        rows = list(csv.DictReader(f))
    assert [r["status"] for r in rows] == [a["status"] for a in result["answers"]]
    assert (output / "001-copy-page001.annotated.png").is_file()
    assert json.loads((output / "summary.json").read_text())["has_failures"] is False
    before = (output / "001-copy-page001.json").read_bytes()
    assert main(args) == 2
    assert (output / "001-copy-page001.json").read_bytes() == before


def test_bad_input_does_not_stop_a_batch(sheet, tmp_path):
    broken = tmp_path / "broken.jpg"
    broken.write_text("not an image")
    good = tmp_path / "good.png"
    save_image(good, sheet["blank"])
    output = tmp_path / "results"
    assert (
        main(
            [
                "analyze",
                str(broken),
                str(good),
                "--template",
                str(sheet["template_path"]),
                "--output",
                str(output),
            ]
        )
        == 1
    )
    report = json.loads((output / "summary.json").read_text())
    assert [p["status"] for p in report["pages"]] == ["input_error", "complete"]


def test_multipage_pdf_processes_each_page(sheet, tmp_path):
    pages = [
        Image.fromarray(cv2.cvtColor(sheet[key], cv2.COLOR_BGR2RGB)) for key in ["blank", "filled"]
    ]
    pdf = tmp_path / "batch.pdf"
    pages[0].save(pdf, save_all=True, append_images=pages[1:], resolution=200)
    output = tmp_path / "results"
    assert (
        main(
            [
                "analyze",
                str(pdf),
                "--template",
                str(sheet["template_path"]),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    report = json.loads((output / "summary.json").read_text())
    assert [p["page"] for p in report["pages"]] == [1, 2]
    assert report["pages"][0]["counts"] == {"blank": 240}
    result = json.loads((output / report["pages"][1]["result"]).read_text())
    assert [
        {k: a[k] for k in ("section", "question", "status", "answer")} for a in result["answers"]
    ] == sheet["truth"]
