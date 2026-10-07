from collections import Counter

import cv2
import numpy as np
import pytest

from psychomark.calibration import calibrate
from psychomark.config import Exam
from psychomark.demo import make_layout, perspective, render_blank, render_filled
from psychomark.engine import Engine


def decisions(result):
    return [
        {key: a[key] for key in ("section", "question", "status", "answer")}
        for a in result["answers"]
    ]


def test_all_240_questions_with_fills_ticks_crosses_blanks_and_erasure_traces(sheet):
    result, preview = sheet["engine"].analyze(sheet["filled"])
    assert decisions(result) == sheet["truth"]
    assert Counter(a["status"] for a in result["answers"]) == {
        "single": 208,
        "multiple": 8,
        "uncertain": 16,
        "blank": 8,
    }
    assert result["status"] == "needs_review"
    assert preview.shape == sheet["filled"].shape
    assert not np.array_equal(preview, sheet["filled"])


@pytest.mark.parametrize(
    "rotation", [cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180, cv2.ROTATE_90_COUNTERCLOCKWISE]
)
def test_right_angle_rotations_keep_question_mapping(sheet, rotation):
    result, _ = sheet["engine"].analyze(cv2.rotate(sheet["filled"], rotation))
    assert decisions(result) == sheet["truth"]


def test_perspective_lighting_noise_and_jpeg(sheet):
    transformed = perspective(sheet["filled"])
    success, encoded = cv2.imencode(".jpg", transformed, [cv2.IMWRITE_JPEG_QUALITY, 90])
    assert success
    photo = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    result, _ = sheet["engine"].analyze(photo)
    assert decisions(result) == sheet["truth"]


def test_blank_reference_has_no_detected_answers(sheet):
    result, _ = sheet["engine"].analyze(sheet["blank"])
    assert result["status"] == "complete"
    assert len(result["answers"]) == 240
    assert all(a["status"] == "blank" and a["answer"] is None for a in result["answers"])


def test_nonconsecutive_sections_and_questions_ignore_unused_marks(sheet):
    exam = Exam(template_id=sheet["layout"].template_id, sections={"2": [1, 9, 21], "7": [10]})
    result, _ = sheet["engine"].analyze(sheet["filled"], exam)
    expected = [a for a in sheet["truth"] if a["question"] in exam.sections.get(a["section"], [])]
    assert decisions(result) == expected
    assert len(result["answers"]) == 4
    assert result["status"] == "complete"


@pytest.mark.parametrize("damage", ["blur", "low_resolution", "empty", "mirror"])
def test_unusable_pages_do_not_become_blank_or_guessed_answers(sheet, damage):
    source = sheet["filled"]
    if damage == "blur":
        source = cv2.GaussianBlur(source, (0, 0), 7)
    elif damage == "low_resolution":
        source = cv2.resize(source, None, fx=0.35, fy=0.35, interpolation=cv2.INTER_AREA)
    elif damage == "empty":
        source = np.full_like(source, 255)
    else:
        source = cv2.flip(source, 1)
    result, _ = sheet["engine"].analyze(source)
    assert result["status"] == "unreadable"
    assert len(result["answers"]) == 240
    assert all(a["status"] == "unreadable" and a["answer"] is None for a in result["answers"])


def test_cut_off_bottom_section_is_rejected(sheet):
    result, _ = sheet["engine"].analyze(sheet["filled"][:1150])
    bottom = [a for a in result["answers"] if a["section"] in {"5", "8"}]
    assert bottom and all(a["status"] == "unreadable" for a in bottom)
    top = [a for a in result["answers"] if a["section"] == "1"]
    expected = [a for a in sheet["truth"] if a["section"] == "1"]
    assert [{key: a[key] for key in expected[0]} for a in top] == expected


def test_frame_damage_blocks_just_the_affected_active_section(sheet):
    source = sheet["filled"].copy()
    x, y, w, h = (int(v) for v in sheet["layout"].sections[0].bounds)
    cv2.rectangle(source, (x, y), (x + w, y + h), (255, 255, 255), 10)
    result, _ = sheet["engine"].analyze(source)
    assert all(a["status"] == "unreadable" for a in result["answers"] if a["section"] == "1")
    assert any(a["status"] == "single" for a in result["answers"] if a["section"] == "8")


def test_locally_blurred_bubbles_are_not_read_as_blank_despite_sharp_frame(sheet):
    source = sheet["filled"].copy()
    x, y, w, h = (int(v) for v in sheet["layout"].sections[0].bounds)
    region = (slice(y + 22, y + h - 5), slice(x + 5, x + w - 5))
    source[region] = cv2.GaussianBlur(source[region], (0, 0), 5)
    result, _ = sheet["engine"].analyze(source)
    assert all(a["status"] == "unreadable" for a in result["answers"] if a["section"] == "1")
    assert any(a["status"] == "single" for a in result["answers"] if a["section"] == "8")


def test_different_layout_vertical_questions_and_five_choices(tmp_path):
    layout = make_layout(vertical=True)
    blank = render_blank(layout)
    filled, truth = render_filled(blank, layout)
    path = tmp_path / "vertical.json"
    calibrate(blank, layout, path)
    result, _ = Engine.from_file(path).analyze(filled)
    assert decisions(result) == truth
    assert any(a["answer"] == 5 for a in result["answers"])


def test_wrong_sheet_template_is_not_silently_accepted(sheet):
    other = render_blank(make_layout(vertical=True))
    result, _ = sheet["engine"].analyze(other)
    assert result["status"] == "unreadable"
    assert all(a["answer"] is None for a in result["answers"])
