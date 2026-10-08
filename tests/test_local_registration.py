import cv2
import numpy as np
import pytest

from psychomark.demo import make_layout, render_blank, render_filled
from psychomark.images import normalized_gray
from psychomark.local_registration import refine_section
from psychomark.regions import project_points


def shifted(image, dx=3, dy=2):
    return cv2.warpAffine(
        image, np.float32([[1, 0, dx], [0, 1, dy]]), image.shape[1::-1], borderValue=(255, 255, 255)
    )


def test_local_affine_recovers_known_translation_without_using_marks(sheet):
    section = sheet["layout"].sections[0]
    reference = normalized_gray(sheet["blank"])
    valid = np.full(reference.shape, 255, np.uint8)
    results = []
    for image in (sheet["blank"], sheet["filled"]):
        result = refine_section(reference, normalized_gray(shifted(image)), valid, section)
        assert result["status"] == "accepted", result
        assert result["correlation_after"] > result["correlation_before"]
        transform = np.asarray(result["reference_to_global"])
        points = [section.center(q, c) for q in (1, 15, 30) for c in (1, 4)]
        assert np.allclose(project_points(points, transform), np.array(points) + [3, 2], atol=0.3)
        results.append(transform)
    # Compare the effect on page points, not affine intercepts about a distant origin.
    assert np.allclose(
        project_points(points, results[0]), project_points(points, results[1]), atol=0.1
    )


def test_identity_does_not_invent_a_local_gain(sheet):
    ref = normalized_gray(sheet["blank"])
    result = refine_section(
        ref,
        normalized_gray(sheet["filled"]),
        np.full(ref.shape, 255, np.uint8),
        sheet["layout"].sections[0],
    )
    assert result["status"] == "unchanged"
    assert np.array_equal(result["reference_to_global"], np.eye(3))


@pytest.mark.parametrize("defect", ["question_shift", "cropped", "missing_frame", "empty_source"])
def test_wrong_grid_and_missing_geometry_are_rejected(sheet, defect):
    ref = normalized_gray(sheet["blank"])
    sample = normalized_gray(sheet["filled"])
    valid = np.full(ref.shape, 255, np.uint8)
    section = sheet["layout"].sections[0]
    if defect == "question_shift":
        sample = normalized_gray(shifted(sheet["filled"], section.question_step[0], 0))
    elif defect == "cropped":
        x, y, w, _ = map(round, section.bounds)
        valid[y - 5 : y + 5, x : x + w] = 0
    elif defect == "missing_frame":
        ref[:] = 255
    else:
        sample[:] = 255
    result = refine_section(ref, sample, valid, section)
    assert result["status"] == "rejected", result
    assert result["reference_to_global"] is None


def test_nonhorizontal_grid_and_five_choices():
    layout = make_layout(vertical=True)
    ref = render_blank(layout)
    filled, _ = render_filled(ref, layout)
    result = refine_section(
        normalized_gray(ref),
        normalized_gray(shifted(filled, 2, -2)),
        np.full(ref.shape[:2], 255, np.uint8),
        layout.sections[0],
    )
    assert result["status"] == "accepted", result
    points = [layout.sections[0].center(1, 1), layout.sections[0].center(20, 5)]
    assert np.allclose(
        project_points(points, np.array(result["reference_to_global"])),
        np.array(points) + [2, -2],
        atol=0.4,
    )


def test_shape_mismatch_rejected(sheet):
    with pytest.raises(ValueError, match="matching"):
        refine_section(
            np.zeros((10, 20)), np.zeros((10, 21)), np.zeros((10, 20)), sheet["layout"].sections[0]
        )
