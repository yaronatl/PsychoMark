import json
from collections import Counter

import cv2
import numpy as np
import pytest

from psychomark.baseline import digest
from psychomark.calibration import calibrate
from psychomark.classic_reader import read_classic_question
from psychomark.config import Layout, Section, write_json
from psychomark.demo import draw_mark, perspective, render_blank, render_filled
from psychomark.engine import Engine, edge_energy
from psychomark.images import normalized_gray, save_image
from psychomark.reader_trial import evaluate_reader, run_reader_trial


def _read(engine, image, section=None):
    gray = normalized_gray(image)
    edges = edge_energy(gray)
    valid = np.full(gray.shape, 255, np.uint8)
    answers = []
    for s in [section] if section else engine.template.sections:
        quality = engine.section_quality(gray, valid, np.eye(3), s)
        answers.extend(
            read_classic_question(
                engine, gray, valid, edges, s, q, quality, cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            )[0]
            for q in range(1, s.questions + 1)
        )
    return answers


def test_fills_ticks_crosses_blank_multiple_and_erasure_traces(sheet):
    answers = _read(sheet["engine"], sheet["filled"])
    assert [
        {key: a[key] for key in ("section", "question", "status", "answer")} for a in answers
    ] == sheet["truth"]
    assert all(a["status"] == "blank" for a in _read(sheet["engine"], sheet["blank"]))


def test_thicker_printed_glyphs_do_not_become_student_marks(sheet):
    image = cv2.erode(sheet["blank"], cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    original = image.copy()
    answers = _read(sheet["engine"], image)
    assert all(a["status"] in {"blank", "uncertain"} and a["answer"] is None for a in answers)
    gray = normalized_gray(image)
    valid = np.full(gray.shape, 255, np.uint8)
    edges = edge_energy(gray)
    legacy = [
        sheet["engine"].read_question(gray, valid, edges, s, q)
        for s in sheet["layout"].sections
        for q in range(1, s.questions + 1)
    ]
    assert any(a["status"] != "blank" for a in legacy), (
        "The synthetic regression must affect the baseline"
    )
    assert np.array_equal(image, original)
    filled, truth = render_filled(image, sheet["layout"])
    new = _read(sheet["engine"], filled)
    # This degradation can require review. Coverage is checked separately on clean
    # and perspective sheets; here no automated answer may contradict the truth.
    assert any(a["status"] == "uncertain" for a in new)
    for a, t in zip(new, truth, strict=True):
        if a["status"] in {"single", "blank"}:
            assert (a["status"], a["answer"]) == (t["status"], t["answer"])


@pytest.mark.parametrize("choices", [2, 5, 10])
def test_number_of_choices_is_not_fixed_and_all_marks_remain_multiple(tmp_path, choices):
    s = Section(
        id="v",
        questions=6,
        choices=choices,
        bounds=(70, 280, 620, 350),
        first_center=(100, 320),
        question_step=(0, 50),
        choice_step=(60, 0),
        bubble_radius=(10, 12),
    )
    layout = Layout(template_id="flexible", width=800, height=700, sections=[s])
    b = render_blank(layout)
    path = tmp_path / "t.json"
    calibrate(b, layout, path)
    e = Engine.from_file(path)
    image = b.copy()
    draw_mark(image, s, 1, choices)
    for c in range(1, choices + 1):
        draw_mark(image, s, 2, c)
    a = _read(e, image)
    assert a[0]["status"] == "single" and a[0]["answer"] == choices
    assert a[1]["status"] == "multiple" and a[1]["candidates"] == list(range(1, choices + 1))
    assert all(x["status"] == "blank" for x in a[2:])


def test_faint_competitor_is_not_discarded_for_a_darker_winner(sheet):
    image = sheet["blank"].copy()
    s = sheet["layout"].sections[0]
    draw_mark(image, s, 1, 1)
    center = tuple(round(v) for v in s.center(1, 2))
    cv2.ellipse(image, center, (5, 7), 0, 0, 360, (220, 220, 220), -1)
    answer = _read(sheet["engine"], image, s)[0]
    assert answer["status"] == "uncertain" and answer["answer"] is None
    assert 1 in answer["candidates"] and 2 in answer["candidates"]
    gray = normalized_gray(image)
    legacy = sheet["engine"].read_question(
        gray, np.full(gray.shape, 255, np.uint8), edge_energy(gray), s, 1
    )
    assert legacy["status"] == "single", "The fixture must expose the lost faint competitor"


def test_blurred_or_cut_bubbles_do_not_become_blank(sheet):
    e = sheet["engine"]
    s = e.template.sections[0]
    image = sheet["filled"].copy()
    x, y, w, h = map(int, s.bounds)
    roi = (slice(y + 22, y + h - 5), slice(x + 5, x + w - 5))
    image[roi] = cv2.GaussianBlur(image[roi], (0, 0), 5)
    assert all(a["status"] == "unreadable" for a in _read(e, image, s))
    gray = normalized_gray(sheet["blank"])
    edges = edge_energy(gray)
    valid = np.full(gray.shape, 255, np.uint8)
    cx, cy = map(round, s.center(1, 1))
    valid[cy - 8 : cy + 8, cx - 6 : cx + 6] = 0
    raw = cv2.cvtColor(sheet["blank"], cv2.COLOR_BGR2GRAY)
    a, _ = read_classic_question(e, gray, valid, edges, s, 1, {"issues": []}, raw)
    assert a["status"] == "unreadable" and a["answer"] is None
    a, _ = read_classic_question(
        e, gray, valid, edges, s, 1, {"issues": ["insufficient_resolution"]}, raw
    )
    assert a["reason"] == "insufficient_resolution"


def _manifest(sheet, source, path):
    e = sheet["engine"]
    s = e.template.sections[0]
    rows = []
    for q, marks, status, choices in [
        (1, ["empty", "marked", "empty", "empty"], "single", [2]),
        (5, ["empty"] * 4, "blank", []),
    ]:
        cx, cy = s.center(q, 1)
        rows.append(
            {
                "section": s.id,
                "question": q,
                "choices": 4,
                "annotation": {
                    "geometry": "confirmed",
                    "manual_bounds": [int(cx - 10), int(cy - 13), int(cx + 11), int(cy + 104)],
                    "marks": marks,
                    "status": status,
                    "choices": choices,
                },
            }
        )
    manifest = {
        "schema_version": 1,
        "split": "development",
        "training_allowed": False,
        "source_size": [e.template.width, e.template.height],
        "provenance": {"snapshot_template_sha256": digest(sheet["template_path"])},
        "images": {
            "source": {"sha256": digest(source)},
            "reference": {"sha256": e.template.reference_sha256},
        },
        "questions": rows,
    }
    write_json(path, manifest)
    return manifest


def test_runner_preserves_engine_and_labels_cannot_change_predictions(sheet, tmp_path):
    source = tmp_path / "photo.png"
    save_image(source, sheet["filled"])
    path = tmp_path / "manifest.json"
    m = _manifest(sheet, source, path)
    output = tmp_path / "trial"
    r = run_reader_trial(sheet["template_path"], source, output, path)
    assert r["complete"] and r["variants"]["classic_v1"]["evaluation"]["correct_automatic"] == 2
    expected, _ = sheet["engine"].analyze(sheet["filled"])
    assert json.loads((output / "historical-result.json").read_text()) == expected
    assert all(digest(output / k) == v for k, v in r["artifact_sha256"].items())
    m["questions"][0]["annotation"].update(marks=["marked", "empty", "empty", "empty"], choices=[1])
    write_json(path, m)
    repeat = run_reader_trial(sheet["template_path"], source, tmp_path / "changed-label", path)
    for name in r["variants"]:
        assert repeat["variants"][name]["answers"] == r["variants"][name]["answers"]
    assert repeat["variants"]["classic_v1"]["evaluation"]["incorrect_automatic"] == 1
    with pytest.raises(ValueError, match="new directory"):
        run_reader_trial(sheet["template_path"], source, output, path)


def test_registration_rejection_keeps_all_labelled_questions(sheet, tmp_path):
    source = tmp_path / "blank.png"
    save_image(source, np.full_like(sheet["blank"], 255))
    path = tmp_path / "manifest.json"
    m = _manifest(sheet, source, path)
    r = run_reader_trial(sheet["template_path"], source, tmp_path / "rejected", path)
    assert r["registration"] is None
    for data in r["variants"].values():
        assert data["evaluation"]["review"] == 2
        assert data["evaluation"]["error_rate_on_geometry_comparable_automatic"] is None
    m["split"] = "test"
    write_json(path, m)
    with pytest.raises(ValueError):
        run_reader_trial(sheet["template_path"], source, tmp_path / "reserved", path)


def test_evaluation_counts_automatic_answers_on_ambiguous_labels_as_errors():
    labels = {
        ("s", 1): {"status": "uncertain", "marks": ["ambiguous", "empty"]},
        ("s", 2): {"status": "blank", "marks": ["empty", "empty"]},
        ("s", 3): {"status": "single", "marks": ["marked", "empty"]},
    }
    answers = [
        {"section": "s", "question": 1, "status": "single", "answer": 1},
        {"section": "s", "question": 2, "status": "blank", "answer": None},
        {"section": "s", "question": 3, "status": "unreadable", "answer": None},
    ]
    geometry = {
        "observations": [{"section": "s", "question": 1, "all_choice_centers_inside": True}]
    }
    e = evaluate_reader(answers, labels, geometry)
    assert e["annotated_questions"] == 3 and e["review"] == 1
    assert e["incorrect_automatic"] == 1 and e["unverified_automatic"] == 1
    assert e["correct_automatic"] == 0


def test_perspective_jpeg_trial_has_no_silent_errors_on_synthetic_sheet(sheet, tmp_path):
    source = tmp_path / "perspective.jpg"
    save_image(source, perspective(sheet["filled"]))
    r = run_reader_trial(sheet["template_path"], source, tmp_path / "trial")
    assert r["registration"] is not None
    truth = {(t["section"], t["question"]): t for t in sheet["truth"]}
    answers = r["variants"]["classic_v1"]["answers"]
    counts = Counter(a["status"] for a in answers)
    assert counts["single"] > 100  # Do not let a reject-all implementation pass.
    for a in answers:
        if a["status"] in {"single", "blank"}:
            t = truth[a["section"], a["question"]]
            assert (a["status"], a["answer"]) == (t["status"], t["answer"])
