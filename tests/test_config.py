import json

import pytest
from pydantic import ValidationError

from psychomark.calibration import calibrate
from psychomark.config import Exam, Layout, Thresholds
from psychomark.demo import make_layout
from psychomark.engine import Engine


@pytest.mark.parametrize("sections", [{"9": [1]}, {"1": [31]}, {"1": [1, 1]}, {"1": []}])
def test_invalid_exam_selection_rejected(sheet, sections):
    exam = Exam(template_id=sheet["layout"].template_id, sections=sections)
    with pytest.raises(ValueError):
        exam.validate_for(sheet["layout"])


def test_exam_for_another_template_rejected(sheet):
    with pytest.raises(ValueError, match="identifiers"):
        Exam(template_id="other", sections={"1": [1]}).validate_for(sheet["layout"])


@pytest.mark.parametrize(
    "change", ["overlap", "outside", "duplicate", "unknown_field", "nonfinite"]
)
def test_bad_geometry_fails_before_analysis(change):
    value = make_layout().model_dump()
    if change == "overlap":
        value["sections"][0]["question_step"] = [1, 0]
    elif change == "outside":
        value["sections"][0]["first_center"] = [0, 0]
    elif change == "duplicate":
        value["sections"][1]["id"] = "1"
    elif change == "unknown_field":
        value["sections"][0]["answers"] = 4
    else:
        value["sections"][0]["bubble_radius"] = [float("nan"), 10]
    with pytest.raises(ValidationError):
        Layout.model_validate(value)


def test_threshold_order_is_checked():
    with pytest.raises(ValidationError):
        Thresholds(trace_coverage=0.8, marked_coverage=0.1)


def test_reference_checksum_prevents_silent_changes(sheet, tmp_path):
    value = json.loads(sheet["template_path"].read_text())
    (tmp_path / value["reference"]).write_bytes(b"changed")
    path = tmp_path / "template.json"
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="checksum"):
        Engine.from_file(path)


def test_calibration_will_not_overwrite_an_existing_file(sheet, tmp_path):
    path = tmp_path / "template.json"
    path.write_text("keep me")
    with pytest.raises(ValueError, match="overwrite"):
        calibrate(sheet["blank"], sheet["layout"], path)
    assert path.read_text() == "keep me"


def test_marked_sheet_is_not_accepted_as_blank_reference(sheet, tmp_path):
    with pytest.raises(ValueError, match="marked or misconfigured"):
        calibrate(sheet["filled"], sheet["layout"], tmp_path / "template.json")
