import json

import cv2
import numpy as np
import pytest

from psychomark.baseline import digest
from psychomark.calibration import calibrate
from psychomark.config import Layout, Section, Template, write_json
from psychomark.demo import draw_mark, render_blank
from psychomark.engine import Engine
from psychomark.images import normalized_gray, save_image
from psychomark.photometric_trial import compare_signals, run_photometric_trial
from psychomark.photometry import (
    VARIANTS,
    match_reference_contrast,
    measure_question,
    prepare_pair,
    project_photo,
    stable_controls,
)


@pytest.fixture
def small_sheet():
    # Five choices and vertical questions exercise axis-independent processing.
    section = Section(
        id="vertical",
        questions=6,
        choices=5,
        bounds=(70, 260, 450, 340),
        first_center=(125, 305),
        question_step=(0, 50),
        choice_step=(80, 0),
        bubble_radius=(12, 12),
    )
    layout = Layout(template_id="photometric_fixture", width=650, height=660, sections=[section])
    reference = render_blank(layout)
    template = Template(**layout.model_dump(), reference="ref.png", reference_sha256="0" * 64)
    return template, reference


def test_reference_tone_fit_ignores_marks_and_rejects_missing_controls(small_sheet):
    template, reference = small_sheet
    section = template.sections[0]
    gray = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
    copy = np.clip(gray.astype(float) * 0.7 + 45, 0, 255).astype(np.uint8)
    valid = np.ones(gray.shape, bool)
    adjusted, fit = match_reference_contrast(gray, copy, valid, section)
    assert fit["status"] == "accepted"
    assert fit["holdout_mae_after"] < 2 < fit["holdout_mae_before"]
    marked = cv2.cvtColor(copy, cv2.COLOR_GRAY2BGR)
    for q in range(1, section.questions + 1):
        for c in range(1, section.choices + 1):
            draw_mark(marked, section, q, c, "fill")
    marked = cv2.cvtColor(marked, cv2.COLOR_BGR2GRAY)
    other, other_fit = match_reference_contrast(gray, marked, valid, section)
    assert other_fit == fit and np.array_equal(other, adjusted)
    unchanged, rejected = match_reference_contrast(gray, copy, np.zeros_like(valid), section)
    assert rejected["reason"] == "insufficient_print_controls"
    assert np.array_equal(unchanged, gray)
    white = np.full_like(gray, 255)
    _, rejected = match_reference_contrast(white, white, valid, section)
    assert rejected["reason"] == "insufficient_print_contrast"
    # The holdout has contradictory print tones: fitting pixels alone must not authorize it.
    _, holdout = stable_controls(section, gray.shape)
    mismatch = copy.copy()
    mismatch[holdout] = 255 - mismatch[holdout]
    unchanged, rejected = match_reference_contrast(gray, mismatch, valid, section)
    assert rejected["reason"] == "held_out_print_mismatch"
    assert np.array_equal(unchanged, gray)


@pytest.mark.parametrize("pencil_gray", [185, 230])
def test_lighting_reduces_blank_signal_without_erasing_faint_or_coloured_marks(
    small_sheet, pencil_gray
):
    template, reference = small_sheet
    section = template.sections[0]
    marked = reference.copy()
    center = tuple(round(v) for v in section.center(1, 2))
    cv2.ellipse(marked, center, (8, 8), 0, 0, 360, (pencil_gray,) * 3, -1, cv2.LINE_AA)
    # Saturated ink must not disappear through a red/blue/green dropout channel.
    for q, colour in zip((2, 3, 4), ((20, 20, 220), (220, 20, 20), (20, 180, 20))):
        cx, cy = (round(v) for v in section.center(q, 4))
        cv2.line(marked, (cx - 6, cy - 6), (cx + 6, cy + 6), colour, 3)
    lighting = np.linspace(0.50, 0.85, template.width)[None, :, None]
    photo = (marked * lighting).astype(np.uint8)
    # Compression is a deterministic stressor; it provides no real-world accuracy evidence.
    ok, encoded = cv2.imencode(".jpg", photo, [cv2.IMWRITE_JPEG_QUALITY, 60])
    assert ok
    photo = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    originals = reference.copy(), photo.copy()
    valid = np.ones(reference.shape[:2], bool)
    scores = {}
    for name in VARIANTS:
        pair = prepare_pair(reference, photo, valid, template, np.eye(3), valid.shape, name)
        scores[name] = [
            measure_question(pair, normalized_gray(reference), section, q)
            for q in range(1, section.questions + 1)
        ]
        assert all(s["usable"] for question in scores[name] for s in question)
        assert pair.reference.dtype == pair.copy.dtype == np.uint8
        # The untreated baseline can lose the ranking under this lighting gradient.
        # The corrected variants must retain these faint/coloured strokes.
        for index, choice in enumerate((2, 4, 4, 4)):
            values = [s["mean_positive_delta"] for s in scores[name][index]]
            if name != "raw_gray":
                assert (
                    values[choice - 1] > max(v for i, v in enumerate(values) if i != choice - 1) + 5
                ), name
    raw_empty = np.mean([s["mean_positive_delta"] for s in scores["raw_gray"][5]])
    corrected_empty = np.mean([s["mean_positive_delta"] for s in scores["normalized"][5]])
    assert corrected_empty < raw_empty * 0.25
    assert np.array_equal(reference, originals[0]) and np.array_equal(photo, originals[1])


def test_resolution_simulation_reduces_false_residual_on_a_downsampled_blank(small_sheet):
    template, reference = small_sheet
    scale = 0.55
    inverse = np.diag([scale, scale, 1.0])
    photo = cv2.warpPerspective(reference, inverse, (358, 363), borderValue=(255,) * 3)
    transform = np.linalg.inv(inverse)
    aligned, valid = project_photo(photo, transform, (template.width, template.height))
    baseline = prepare_pair(
        reference, aligned, valid, template, transform, photo.shape[:2], "normalized"
    )
    matched = prepare_pair(
        reference, aligned, valid, template, transform, photo.shape[:2], "reference_resolution"
    )
    before, after = [], []
    for q in range(1, 7):
        for pair, values in ((baseline, before), (matched, after)):
            values.extend(
                s["mean_positive_delta"]
                for s in measure_question(pair, normalized_gray(reference), template.sections[0], q)
            )
    assert np.mean(before) > 1
    assert np.mean(after) < 0.1
    assert np.array_equal(baseline.copy, matched.copy), "Only the reference is resolution-matched"


def test_missing_border_pixels_are_never_treated_as_white_answers(small_sheet):
    template, reference = small_sheet
    source = reference[:350, :250]
    transform = np.array([[1.0, 0, 0.5], [0, 1, 0], [0, 0, 1]])
    aligned, valid = project_photo(source, transform, (template.width, template.height))
    assert not valid[100, 0] and valid[100, 1]  # Partial bilinear support is unavailable.
    for name in VARIANTS:
        pair = prepare_pair(reference, aligned, valid, template, transform, source.shape[:2], name)
        scores = measure_question(pair, normalized_gray(reference), template.sections[0], 1)
        assert scores[0]["usable"]
        assert not scores[-1]["usable"] and scores[-1]["mean_positive_delta"] is None
        assert not np.any(pair.valid & ~valid)


def _trial_inputs(small_sheet, tmp_path, empty_source=False):
    template, reference = small_sheet
    layout = Layout.model_validate(template.model_dump(exclude={"reference", "reference_sha256"}))
    template_path = tmp_path / "template.json"
    template = calibrate(reference, layout, template_path)
    source = np.full_like(reference, 255) if empty_source else reference.copy()
    if not empty_source:
        draw_mark(source, template.sections[0], 1, 5)
    source_path = tmp_path / "source.png"
    save_image(source_path, source)
    manifest = {
        "schema_version": 1,
        "split": "development",
        "training_allowed": False,
        "source_size": [template.width, template.height],
        "provenance": {"snapshot_template_sha256": digest(template_path)},
        "images": {
            "source": {"sha256": digest(source_path)},
            "reference": {"sha256": template.reference_sha256},
        },
        "questions": [
            {
                "section": "vertical",
                "question": 1,
                "choices": 5,
                "annotation": {
                    "geometry": "confirmed",
                    "manual_bounds": [110, 287, 462, 323],
                    "marks": ["empty"] * 4 + ["marked"],
                    "choices": [5],
                    "status": "single",
                },
            },
            {
                "section": "vertical",
                "question": 2,
                "choices": 5,
                "annotation": {
                    "geometry": "confirmed",
                    "manual_bounds": [110, 338, 462, 370],
                    "marks": ["empty"] * 5,
                    "choices": [],
                    "status": "blank",
                },
            },
            {"section": "vertical", "question": 3, "choices": 5, "annotation": None},
        ],
    }
    path = tmp_path / "manifest.json"
    write_json(path, manifest)
    return template_path, source_path, path, manifest


def test_trial_is_reproducible_preserves_history_and_labels_cannot_change_images(
    small_sheet, tmp_path
):
    template, source, path, manifest = _trial_inputs(small_sheet, tmp_path)
    before = {p: digest(p) for p in (template, source, path)}
    output = tmp_path / "trial"
    report = run_photometric_trial(template, source, output, path)
    expected, _ = Engine.from_file(template).analyze(cv2.imread(str(source)))
    assert json.loads((output / "historical-result.json").read_text()) == expected
    assert report["complete"] and report["registration"] is not None
    assert report["geometry_comparison"]["all_choice_centers_inside"] == 2
    assert report["historical_quality_at_fixed_geometry"]["vertical"]["issues"] == []
    assert before == {p: digest(p) for p in before}
    for data in report["variants"].values():
        metrics = data["comparison"]
        assert metrics["annotated_questions"] == metrics["evaluated_questions"] == 2
        assert metrics["single_mark_positive_margin"] == 1
        assert metrics["label_signals"]["empty"]["count"] == 9  # Unannotated is not empty.
        assert metrics["answer_accuracy"] is None
    assert all(digest(output / name) == value for name, value in report["artifact_sha256"].items())
    with pytest.raises(ValueError, match="new directory"):
        run_photometric_trial(template, source, output, path)
    # Change a label to an intentionally wrong but structurally valid human observation.
    # The fitted images, scores, geometry and rejection reasons must remain identical.
    manifest["questions"][0]["annotation"].update(marks=["marked"] + ["empty"] * 4, choices=[1])
    write_json(path, manifest)
    other = tmp_path / "other"
    repeat = run_photometric_trial(template, source, other, path)
    assert repeat["registration"] == report["registration"]
    for name in VARIANTS:
        a, b = report["variants"][name], repeat["variants"][name]
        for key in ("processing", "sections", "questions"):
            assert a[key] == b[key]
        assert b["comparison"]["single_mark_positive_margin"] == 0
    assert {p.relative_to(output): digest(p) for p in output.rglob("*.png")} == {
        p.relative_to(other): digest(p) for p in other.rglob("*.png")
    }


def test_registration_failure_retains_denominators_and_no_fake_crops(small_sheet, tmp_path):
    template, source, path, _ = _trial_inputs(small_sheet, tmp_path, empty_source=True)
    output = tmp_path / "failed-registration"
    report = run_photometric_trial(template, source, output, path)
    assert report["complete"] and report["registration"] is None
    assert not list(output.rglob("*.png"))
    for data in report["variants"].values():
        metrics = data["comparison"]
        assert metrics["annotated_questions"] == 2 and metrics["evaluated_questions"] == 0
        assert metrics["excluded_questions"] == {"registration_failed": 2}
        assert metrics["answer_accuracy"] is None
        assert metrics["label_signals"]["empty"]["median"] is None


@pytest.mark.parametrize("problem", ["test_split", "identity", "labels", "status"])
def test_invalid_or_reserved_corpus_cannot_be_used_to_tune_treatments(
    small_sheet, tmp_path, problem
):
    template, source, path, manifest = _trial_inputs(small_sheet, tmp_path)
    if problem == "test_split":
        manifest["split"] = "test"
    elif problem == "identity":
        manifest["images"]["source"]["sha256"] = "0" * 64
    elif problem == "labels":
        manifest["questions"][0]["annotation"]["marks"] = ["marked"]
    else:
        manifest["questions"][0]["annotation"]["status"] = "blank"
    write_json(path, manifest)
    output = tmp_path / "rejected-input"
    with pytest.raises(ValueError):
        run_photometric_trial(template, source, output, path)
    assert not output.exists()


def test_ambiguity_and_unavailable_geometry_are_not_forced_into_decisions():
    labels = {
        ("s", 1): {"marks": ["ambiguous", "empty"], "status": "uncertain"},
        ("s", 2): {"marks": ["marked", "marked"], "status": "multiple"},
        ("s", 3): {"marks": ["unreadable", "empty"], "status": "unreadable"},
        ("s", 4): {"marks": ["empty", "empty"], "status": "blank"},
        ("s", 5): {"marks": ["empty", "empty"], "status": "blank"},
        ("s", 6): {"marks": ["empty", "empty"], "status": "blank"},
    }
    questions = [
        {
            "section": "s",
            "question": q,
            "scores": [{"usable": q != 4, "mean_positive_delta": value} for value in (35, 22)],
        }
        for q in range(1, 7)
    ]
    geometry = {
        "observations": [
            {"section": "s", "question": q, "all_choice_centers_inside": q != 5}
            for q in range(1, 6)
        ]
    }
    result = compare_signals(questions, labels, geometry)
    assert result["annotated_questions"] == 6 and result["evaluated_questions"] == 3
    assert result["single_mark_margin"]["count"] == 0
    assert result["label_signals"]["ambiguous"]["count"] == 1
    assert result["label_signals"]["marked"]["count"] == 2
    assert result["label_signals"]["unreadable"]["count"] == 1
    assert result["excluded_questions"] == {
        "unavailable_sampling_pixels": 1,
        "choice_centers_outside_human_box": 1,
        "no_confirmed_manual_geometry": 1,
    }
    assert result["answer_accuracy"] is None
