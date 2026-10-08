import copy
import json
from types import SimpleNamespace

import cv2
import numpy as np
import pytest

from psychomark.baseline import (
    _export_regions,
    compare_results,
    digest,
    main,
    run_baseline,
    summarize,
)
from psychomark.calibration import calibrate
from psychomark.config import Exam, Section
from psychomark.demo import make_layout, perspective, render_blank, render_filled
from psychomark.engine import bubble_roi
from psychomark.images import normalized_gray, read_image, save_image
from psychomark.regions import crop, project_points, question_region


def load(path):
    return json.loads(path.read_text())


def test_baseline_preserves_engine_and_exact_sampling_regions(sheet, tmp_path):
    source = tmp_path / "input.png"
    photo = perspective(sheet["filled"])
    save_image(source, photo)
    before = digest(source)
    exam = Exam(template_id=sheet["layout"].template_id, sections={"1": [2, 9], "7": [21]})
    expected, _ = sheet["engine"].analyze(photo, exam)
    output = tmp_path / "baseline"
    report = run_baseline(sheet["template_path"], source, output, exam)
    assert load(output / "result.json") == expected
    assert digest(source) == before
    regions = load(output / "regions.json")
    assert [(r["section"], r["question"]) for r in regions["questions"]] == [
        (a["section"], a["question"]) for a in expected["answers"]
    ]
    transform = np.array(regions["input_to_reference"])
    inverse = np.array(regions["reference_to_input"])
    aligned = cv2.warpPerspective(
        photo,
        transform,
        (sheet["layout"].width, sheet["layout"].height),
        borderValue=(255, 255, 255),
    )
    for region in regions["questions"]:
        raw = read_image(output / region["assets"]["copy"])
        assert np.array_equal(raw, crop(aligned, region["reference_bounds"]))
        normalized = cv2.imread(str(output / region["assets"]["normalized_copy"]), 0)
        assert np.array_equal(
            normalized, crop(normalized_gray(aligned), region["reference_bounds"])
        )
        section = next(s for s in sheet["layout"].sections if s.id == region["section"])
        sampling = cv2.imread(str(output / region["assets"]["sampling"]), 0)
        x0, y0, _, _ = region["reference_bounds"]
        for choice in region["choices"]:
            center = choice["reference_center"]
            source_center = project_points([center], inverse)
            assert np.allclose(project_points(source_center, transform)[0], center)
            assert np.allclose(source_center[0], choice["source_center"])
            roi, interior = bubble_roi(section, region["question"], choice["choice"])
            expected_mask = (interior & (sheet["engine"].gray_reference[roi] > 200)) * 255
            actual_mask = sampling[
                roi[0].start - y0 : roi[0].stop - y0, roi[1].start - x0 : roi[1].stop - x0
            ]
            assert np.array_equal(actual_mask, expected_mask)
    pending = load(output / "annotations.pending.json")
    assert all(q["status"] is None and q["geometry_valid"] is None for q in pending["questions"])
    assert report["summary"]["automatic_error_rate"] is None
    assert report["summary"]["questions"] == 3
    assert all(digest(output / name) == value for name, value in report["artifact_sha256"].items())
    assert "<details>" in (output / "review.html").read_text()
    with pytest.raises(ValueError, match="new directory"):
        run_baseline(sheet["template_path"], source, output, exam)


def test_registration_failure_has_no_invented_regions_or_accuracy(sheet, tmp_path):
    source = tmp_path / "empty.png"
    save_image(source, np.full_like(sheet["filled"], 255))
    output = tmp_path / "baseline"
    report = run_baseline(sheet["template_path"], source, output)
    assert report["summary"]["questions"] == 240
    assert report["summary"]["automatic_fraction"] == 0
    assert report["summary"]["automatic_error_rate"] is None
    assert report["summary"]["page_rejected"] is True
    regions = load(output / "regions.json")
    assert regions["questions"] == []
    assert regions["input_to_reference"] is None
    assert not (output / "questions").exists()
    assert len(load(output / "annotations.pending.json")["questions"]) == 240


def test_vertical_five_choices_and_nonconsecutive_questions(tmp_path):
    layout = make_layout(vertical=True)
    blank = render_blank(layout)
    filled, _ = render_filled(blank, layout)
    template = tmp_path / "vertical.json"
    calibrate(blank, layout, template)
    source = tmp_path / "vertical.png"
    save_image(source, cv2.rotate(filled, cv2.ROTATE_90_CLOCKWISE))
    section = layout.sections[0]
    exam = Exam(template_id=layout.template_id, sections={section.id: [3, 1]})
    output = tmp_path / "baseline"
    run_baseline(template, source, output, exam)
    regions = load(output / "regions.json")["questions"]
    assert [r["question"] for r in regions] == [3, 1]
    for region in regions:
        assert [c["choice"] for c in region["choices"]] == [1, 2, 3, 4, 5]
        for choice in region["choices"]:
            assert choice["reference_center"] == list(
                section.center(region["question"], choice["choice"])
            )


def test_source_resolution_is_not_inflated_by_reference_upscaling(sheet):
    section = sheet["layout"].sections[0]
    valid = np.full(sheet["blank"].shape[:2], 255, np.uint8)
    inverse = np.diag([0.4, 0.4, 1])
    region = question_region(section, 1, inverse, valid, (600, 800))
    assert np.allclose(region.choices[0].source_diameters_px, np.array(section.bubble_radius) * 0.8)


def test_cropped_section_keeps_rejection_and_missing_pixels(sheet, tmp_path):
    source = tmp_path / "cropped.png"
    save_image(source, sheet["filled"][:1150])
    exam = Exam(template_id=sheet["layout"].template_id, sections={"5": [1, 2]})
    output = tmp_path / "baseline"
    run_baseline(sheet["template_path"], source, output, exam)
    result = load(output / "result.json")
    assert all(a["status"] == "unreadable" for a in result["answers"])
    regions = load(output / "regions.json")["questions"]
    assert regions and any(r["valid_fraction"] < 1 for r in regions)
    assert any(c["valid_fraction"] < 1 for r in regions for c in r["choices"])


def test_comparison_is_predictions_not_truth_and_checks_compatibility(sheet):
    result, _ = sheet["engine"].analyze(sheet["filled"])
    other = copy.deepcopy(result)
    other["answers"][0]["status"] = "uncertain"
    comparison = compare_results(result, other)
    assert comparison["decision_changes"] == [{"section": "1", "question": 1}]
    assert comparison["kind"] == "historical_predictions_not_ground_truth"
    assert summarize(result)["automatic_error_rate"] is None
    other["exam"]["sections"]["1"] = [1]
    with pytest.raises(ValueError, match="identical exam"):
        compare_results(result, other)


def test_repeated_run_and_cli_compare(sheet, tmp_path):
    source = tmp_path / "input.png"
    save_image(source, sheet["filled"])
    exam = Exam(template_id=sheet["layout"].template_id, sections={"1": [1]})
    selection = tmp_path / "exam.json"
    selection.write_text(exam.model_dump_json())
    previous = tmp_path / "first"
    run_baseline(sheet["template_path"], source, previous, exam)
    current = tmp_path / "second"
    assert (
        main(
            [
                str(source),
                "--template",
                str(sheet["template_path"]),
                "--output",
                str(current),
                "--exam",
                str(selection),
                "--compare",
                str(previous / "result.json"),
            ]
        )
        == 0
    )
    report = load(current / "report.json")
    assert report["comparison"]["decision_changes"] == []
    assert report["comparison"]["diagnostics_identical"] is True
    assert report["comparison"]["source_identity"] == "verified_source_bytes"
    assert digest(previous / "regions.json") == digest(current / "regions.json")
    assert (
        main([str(source), "--template", str(sheet["template_path"]), "--output", str(current)])
        == 2
    )


def test_oblique_roi_rectangles_do_not_erase_another_bubble_mask(tmp_path):
    section = Section(
        id="x",
        questions=1,
        choices=2,
        bounds=(0, 0, 50, 50),
        first_center=(15, 15),
        question_step=(10, 0),
        choice_step=(8.1, 6.1),
        bubble_radius=(5, 5),
    )
    blank = np.full((60, 60, 3), 255, np.uint8)
    engine = SimpleNamespace(
        reference=blank,
        gray_reference=blank[:, :, 0],
        template=SimpleNamespace(width=60, height=60, sections=[section]),
    )
    result = {
        "diagnostics": {"registration": {"input_to_reference": np.eye(3).tolist()}},
        "answers": [{"section": "x", "question": 1}],
    }
    region = _export_regions(engine, blank, result, tmp_path)[0]
    mask = cv2.imread(str(tmp_path / region["assets"]["sampling"]), 0)
    assert np.count_nonzero(mask) == 90  # Overwriting overlapping rectangles loses two pixels.


def test_comparison_rejects_a_different_source_even_for_same_template(sheet, tmp_path):
    source = tmp_path / "filled.png"
    other = tmp_path / "blank.png"
    save_image(source, sheet["filled"])
    save_image(other, sheet["blank"])
    exam = Exam(template_id=sheet["layout"].template_id, sections={"1": [1]})
    previous = tmp_path / "first"
    run_baseline(sheet["template_path"], source, previous, exam)
    with pytest.raises(ValueError, match="same source image"):
        run_baseline(
            sheet["template_path"], other, tmp_path / "second", exam, previous / "result.json"
        )
    assert not (tmp_path / "second").exists()
