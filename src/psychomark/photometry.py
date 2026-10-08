"""Experimental S04 image pairs. No labels, answer keys or optical decisions here."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .config import Section, Template
from .engine import bubble_roi
from .images import normalized_gray

# Fixed ablations, not a search optimized against the human annotations.
VARIANTS = (
    "raw_gray",
    "normalized",
    "min_channel",
    "reference_contrast",
    "reference_resolution",
    "reference_blur",
    "combined",
)
PARAMETERS = {
    "paper_sigma_reference_px": 25,
    "paper_floor": 40,
    "reference_blur_sigma_px": 0.8,
    "control_bubble_margin_reference_px": 4,
    "control_tile_reference_px": 8,
    "contrast_slope_bounds": [0.35, 2.5],
    "contrast_offset_bounds": [-100, 100],
    "minimum_control_pixels_per_partition": 160,
    "minimum_contrast_span": 40,
    "maximum_holdout_mae": 35,
    "maximum_holdout_regression": 0.5,
}


@dataclass
class ImagePair:
    """Native reference-sized uint8 planes; valid means all interpolation taps exist."""

    reference: np.ndarray
    copy: np.ndarray
    valid: np.ndarray
    diagnostics: dict


def project_photo(
    source: np.ndarray, transform: np.ndarray, size: tuple[int, int]
) -> tuple[np.ndarray, np.ndarray]:
    """Sample original colour once; reject pixels partially supplied by the border."""
    aligned = cv2.warpPerspective(source, transform, size, borderValue=(255, 255, 255))
    support = cv2.warpPerspective(np.ones(source.shape[:2], np.float32), transform, size)
    return aligned, support >= 1 - 1e-6


def stable_controls(section: Section, shape: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    """Printed-grid controls excluding every case, with an extra 4 reference px margin.

    Alternating 8px tiles separate fit/holdout pixels. These controls are a rendering
    diagnostic, not a second independent sheet or proof of correct registration.
    """
    height, width = shape
    mask = np.zeros(shape, np.uint8)
    x, y, w, h = section.bounds
    x0, y0 = max(0, int(np.floor(x))), max(0, int(np.floor(y)))
    x1, y1 = min(width, int(np.ceil(x + w))), min(height, int(np.ceil(y + h)))
    mask[y0:y1, x0:x1] = 1
    rx, ry = section.bubble_radius
    margin = PARAMETERS["control_bubble_margin_reference_px"]
    for question in range(1, section.questions + 1):
        for choice in range(1, section.choices + 1):
            cx, cy = section.center(question, choice)
            cv2.ellipse(
                mask,
                (round(cx), round(cy)),
                (int(np.ceil(rx + margin)), int(np.ceil(ry + margin))),
                0,
                0,
                360,
                0,
                -1,
            )
    tile = PARAMETERS["control_tile_reference_px"]
    rows = (np.arange(height) // tile) % 2
    columns = (np.arange(width) // tile) % 2
    partition = rows[:, None] == columns[None, :]
    return (mask > 0) & partition, (mask > 0) & ~partition


def _mae(reference: np.ndarray, copy: np.ndarray, mask: np.ndarray) -> float | None:
    if not np.any(mask):
        return None
    return float(np.mean(np.abs(reference[mask].astype(float) - copy[mask])))


def match_reference_contrast(
    reference: np.ndarray, copy: np.ndarray, valid: np.ndarray, section: Section
) -> tuple[np.ndarray, dict]:
    """Fit reference→photo tone on print only; never brighten or erase the photo.

    Bin medians give printed ink a voice despite the large amount of white paper.
    Reject weak support, extreme coefficients or worse held-out print residuals.
    A rejected fit returns the input reference and a recorded reason.
    """
    fit, holdout = stable_controls(section, reference.shape)
    fit &= valid
    holdout &= valid
    diagnostic = {
        "status": "rejected",
        "fit_pixels": int(fit.sum()),
        "holdout_pixels": int(holdout.sum()),
        "holdout_mae_before": _mae(reference, copy, holdout),
        "holdout_mae_after": None,
        "slope": None,
        "offset": None,
    }
    minimum = PARAMETERS["minimum_control_pixels_per_partition"]
    if min(fit.sum(), holdout.sum()) < minimum:
        return reference, dict(diagnostic, reason="insufficient_print_controls")
    x, y = reference[fit].astype(float), copy[fit].astype(float)
    points = []
    for low in range(0, 256, 32):
        selected = (x >= low) & (x < low + 32)
        if selected.sum() >= 16:
            points.append((float(np.median(x[selected])), float(np.median(y[selected]))))
    span = PARAMETERS["minimum_contrast_span"]
    if len(points) < 2 or np.ptp(np.asarray(points)[:, 0]) < span:
        return reference, dict(diagnostic, reason="insufficient_print_contrast")
    x, y = np.asarray(points).T
    slope, offset = np.linalg.lstsq(np.column_stack([x, np.ones_like(x)]), y, rcond=None)[0]
    diagnostic.update(slope=float(slope), offset=float(offset))
    s0, s1 = PARAMETERS["contrast_slope_bounds"]
    o0, o1 = PARAMETERS["contrast_offset_bounds"]
    if not s0 <= slope <= s1 or not o0 <= offset <= o1:
        return reference, dict(diagnostic, reason="tone_mapping_out_of_bounds")
    candidate = np.clip(reference.astype(float) * slope + offset, 0, 255).astype(np.uint8)
    after = _mae(candidate, copy, holdout)
    diagnostic["holdout_mae_after"] = after
    if (
        after > diagnostic["holdout_mae_before"] + PARAMETERS["maximum_holdout_regression"]
        or after > PARAMETERS["maximum_holdout_mae"]
    ):
        return reference, dict(diagnostic, reason="held_out_print_mismatch")
    return candidate, dict(diagnostic, status="accepted", reason="bounded_print_tone_fit")


def _resolution_reference(
    reference: np.ndarray, transform: np.ndarray, source_shape: tuple[int, int]
) -> tuple[np.ndarray, np.ndarray]:
    """Simulate the source sampling grid on the reference, without enhancing the photo.

    This is a fixed bilinear round trip, not an estimate of the printer/camera PSF.
    Two reference resamplings are deliberate. The source itself is sampled only once.
    """
    height, width = reference.shape[:2]
    source_height, source_width = source_shape
    inverse = np.linalg.inv(transform)
    projected = cv2.warpPerspective(
        reference, inverse, (source_width, source_height), borderValue=(255, 255, 255)
    )
    support = cv2.warpPerspective(
        np.ones((height, width), np.float32), inverse, (source_width, source_height)
    )
    result, _ = project_photo(projected, transform, (width, height))
    support = cv2.warpPerspective(support, transform, (width, height))
    return result, support >= 1 - 1e-6


def prepare_pair(
    reference: np.ndarray,
    aligned: np.ndarray,
    valid: np.ndarray,
    template: Template,
    transform: np.ndarray,
    source_shape: tuple[int, int],
    variant: str,
) -> ImagePair:
    """Apply one declared ablation. Geometry and manual observations are never fitted."""
    if variant not in VARIANTS:
        raise ValueError("Unknown photometric variant")
    ref = reference.copy()
    available = valid.copy()
    diagnostic = {"variant": variant, "contrast": {}}
    if variant in {"reference_resolution", "combined"}:
        ref, support = _resolution_reference(ref, transform, source_shape)
        available &= support
    if variant in {"reference_blur", "combined"}:
        ref = cv2.GaussianBlur(ref, (0, 0), PARAMETERS["reference_blur_sigma_px"])
    if variant == "raw_gray":
        ref_gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
        photo_gray = cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY)
    elif variant == "min_channel":
        # Minimum channel retains saturated red/blue/green strokes as dark ink.
        # It can also darken coloured print and noise; it is only an ablation.
        ref_gray = normalized_gray(cv2.cvtColor(ref.min(axis=2), cv2.COLOR_GRAY2BGR))
        photo_gray = normalized_gray(cv2.cvtColor(aligned.min(axis=2), cv2.COLOR_GRAY2BGR))
    else:
        ref_gray = normalized_gray(ref)
        photo_gray = normalized_gray(aligned)
    if variant in {"reference_contrast", "combined"}:
        # Each grid has its own printed background. Fit before evaluation, without labels.
        adjusted = ref_gray.copy()
        for section in template.sections:
            candidate, fit = match_reference_contrast(ref_gray, photo_gray, available, section)
            diagnostic["contrast"][section.id] = fit
            x, y, w, h = section.bounds
            ys = slice(max(0, int(np.floor(y))), min(template.height, int(np.ceil(y + h))))
            xs = slice(max(0, int(np.floor(x))), min(template.width, int(np.ceil(x + w))))
            adjusted[ys, xs] = candidate[ys, xs]
        ref_gray = adjusted
    return ImagePair(ref_gray, photo_gray, available, diagnostic)


def measure_question(
    pair: ImagePair, baseline_reference: np.ndarray, section: Section, question: int
) -> list[dict]:
    """Continuous residuals on an identical historical paper mask for every variant.

    Positive residual = photo darker than reference, in 8-bit intensity units.
    These are not probabilities, classifications or authorization to read a question.
    """
    scores = []
    for choice in range(1, section.choices + 1):
        roi, interior = bubble_roi(section, question, choice)
        mask = interior & (baseline_reference[roi] > 200)
        count = int(mask.sum())
        usable = count >= 12 and bool(np.all(pair.valid[roi][mask]))
        delta = pair.reference[roi].astype(float) - pair.copy[roi].astype(float)
        scores.append(
            {
                "choice": choice,
                "sampling_pixels": count,
                "usable": usable,
                "mean_positive_delta": float(np.maximum(delta[mask], 0).mean()) if usable else None,
                "mean_signed_delta": float(delta[mask].mean()) if usable else None,
            }
        )
    return scores


def print_residuals(pair: ImagePair, section: Section) -> dict:
    """Held-out frame/print rendering mismatch; lower is not automatically better OMR."""
    _, holdout = stable_controls(section, pair.reference.shape)
    holdout &= pair.valid
    return {"pixels": int(holdout.sum()), "mae": _mae(pair.reference, pair.copy, holdout)}
