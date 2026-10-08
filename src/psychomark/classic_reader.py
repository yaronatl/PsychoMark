"""S05 experimental mark reader. No answer key, labels, training or web activation."""

from __future__ import annotations

import cv2
import numpy as np

from .config import Section
from .engine import Engine, bubble_roi

PARAMETERS = {
    "printed_ink_cutoff": 200,
    "print_exclusion_radius_reference_px": 1,
    "minimum_sampling_pixels": 12,
    "minimum_interior_fraction": 0.25,
    "dark_delta": 75,
    "trace_delta": 20,
    "strong_coverage": 0.22,
    "strong_component_fraction": 0.08,
    "strong_component_span": 0.35,
    "trace_coverage": 0.04,
    "minimum_single_margin": 0.12,
}


def choice_evidence(
    reference: np.ndarray,
    gray: np.ndarray,
    valid: np.ndarray,
    section: Section,
    question: int,
    choice: int,
    raw_gray: np.ndarray,
    reference_color: np.ndarray,
) -> tuple[dict, np.ndarray]:
    """Measure ink away from printed glyphs, without moving towards a dark mark.

    The output mask has the historical bubble ROI shape. Intensities are 0–255,
    coverages/component areas are fractions of the fixed usable interior. Span is
    the largest connected component's axis extent divided by the bubble diameter.
    Local contrast uses the 90th percentile of paper in a fixed surrounding patch.
    """
    roi, interior = bubble_roi(section, question, choice)
    # Build a padded patch so print just outside the ROI is excluded as well.
    y0, y1, x0, x1 = roi[0].start, roi[0].stop, roi[1].start, roi[1].stop
    height, width = reference.shape
    margin = PARAMETERS["print_exclusion_radius_reference_px"]
    a, b = max(0, y0 - margin), max(0, x0 - margin)
    ink = (
        reference[a : min(height, y1 + margin), b : min(width, x1 + margin)]
        < PARAMETERS["printed_ink_cutoff"]
    ).astype(np.uint8)
    printed = cv2.dilate(
        ink, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * margin + 1, 2 * margin + 1))
    )
    printed = printed[y0 - a : y1 - a, x0 - b : x1 - b] > 0
    mask = interior & ~printed
    count = int(mask.sum())
    evidence = {
        "choice": choice,
        "sampling_pixels": count,
        "interior_fraction": float(count / max(int(interior.sum()), 1)),
        "usable": False,
    }
    if (
        count < PARAMETERS["minimum_sampling_pixels"]
        or evidence["interior_fraction"] < PARAMETERS["minimum_interior_fraction"]
    ):
        return dict(evidence, reason="insufficient_unprinted_interior"), mask
    if not np.all(valid[roi][mask] > 250):
        return dict(evidence, reason="cropped_bubble"), mask
    rx, ry = section.bubble_radius
    cx, cy = section.center(question, choice)
    a, b = max(0, int(cy - 1.6 * ry)), max(0, int(cx - 1.6 * rx))
    patch = (
        slice(a, min(height, int(cy + 1.6 * ry) + 1)),
        slice(b, min(width, int(cx + 1.6 * rx) + 1)),
    )
    yy, xx = np.mgrid[patch[0], patch[1]]
    radius = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
    paper = (
        (radius >= 1.2**2) & (radius <= 1.6**2) & (reference[patch] > 220) & (valid[patch] > 250)
    )
    if paper.sum() < 12:
        return dict(evidence, reason="insufficient_local_paper"), mask
    local_paper = float(np.percentile(gray[patch][paper], 90))
    residual = np.maximum(reference[roi].astype(float) - gray[roi], 0)
    contrast = np.maximum(local_paper - gray[roi].astype(float), 0)
    # Require darkness both against the reference and against nearby paper.
    signal = np.minimum(residual, contrast)
    dark = mask & (signal >= PARAMETERS["dark_delta"])
    # The full-page paper estimate can brighten a faint competing trace to white.
    # A second, local raw-image path can require review, never erase other evidence.
    raw_ref_patch = cv2.cvtColor(reference_color[patch], cv2.COLOR_BGR2GRAY)
    ref_paper = float(np.percentile(raw_ref_patch[paper], 90))
    sample_paper = float(np.percentile(raw_gray[patch][paper], 90))
    raw_ref = cv2.cvtColor(reference_color[roi], cv2.COLOR_BGR2GRAY).astype(float)
    raw_contrast = (sample_paper - raw_gray[roi].astype(float)) * 255 / max(sample_paper, 40)
    ref_contrast = (ref_paper - raw_ref) * 255 / max(ref_paper, 40)
    raw_signal = np.maximum(raw_contrast - ref_contrast, 0)
    trace = mask & (np.maximum(signal, raw_signal) >= PARAMETERS["trace_delta"])
    _, _, stats, _ = cv2.connectedComponentsWithStats(dark.astype(np.uint8), 8)
    component_fraction, span = 0.0, 0.0
    if len(stats) > 1:
        component = stats[1:][np.argmax(stats[1:, cv2.CC_STAT_AREA])]
        component_fraction = float(component[cv2.CC_STAT_AREA] / count)
        span = float(
            max(component[cv2.CC_STAT_WIDTH] / (2 * rx), component[cv2.CC_STAT_HEIGHT] / (2 * ry))
        )
    return dict(
        evidence,
        usable=True,
        reason=None,
        local_paper=local_paper,
        mean_signal=float(signal[mask].mean()),
        mean_raw_local_signal=float(raw_signal[mask].mean()),
        dark_coverage=float(dark.sum() / count),
        trace_coverage=float(trace.sum() / count),
        component_fraction=component_fraction,
        component_span=span,
    ), mask


def decide_question(section: str, question: int, scores: list[dict]) -> dict:
    """Independent per-choice evidence first; competing marks are never erased by argmax.

    Thresholds are fixed exploratory heuristics, not calibrated probabilities. Weak
    or contradictory evidence abstains. Source/geometry checks are applied by the caller.
    """
    failures = sorted({s["reason"] for s in scores if not s["usable"]})
    if failures:
        return dict(Engine.unreadable(section, question, ",".join(failures)), scores=scores)
    strong, traces = [], []
    for score in scores:
        if (
            score["dark_coverage"] >= PARAMETERS["strong_coverage"]
            and score["component_fraction"] >= PARAMETERS["strong_component_fraction"]
            and score["component_span"] >= PARAMETERS["strong_component_span"]
        ):
            strong.append(score["choice"])
        if score["trace_coverage"] >= PARAMETERS["trace_coverage"]:
            traces.append(score["choice"])
    margin = None
    answer = None
    if len(strong) > 1:
        status, reason = "multiple", "multiple_supported_marks"
    elif len(strong) == 1:
        selected = next(s for s in scores if s["choice"] == strong[0])
        margin = selected["dark_coverage"] - max(
            s["dark_coverage"] for s in scores if s["choice"] != strong[0]
        )
        if set(traces) - set(strong) or margin < PARAMETERS["minimum_single_margin"]:
            status, reason = "uncertain", "competing_trace_or_small_margin"
        else:
            status, reason, answer = "single", "one_supported_mark", strong[0]
    elif traces:
        status, reason = "uncertain", "weak_or_fragmented_ink"
    else:
        status, reason = "blank", "no_supported_ink"
    return {
        "section": section,
        "question": question,
        "status": status,
        "answer": answer,
        "candidates": sorted(set(strong + traces)),
        "reason": reason,
        "scores": scores,
        "dark_coverage_margin": margin,
    }


def read_classic_question(
    engine: Engine,
    gray: np.ndarray,
    valid: np.ndarray,
    edges: np.ndarray,
    section: Section,
    question: int,
    quality: dict,
    raw_gray: np.ndarray,
) -> tuple[dict, list[np.ndarray]]:
    """Keep section, source-resolution and historical per-bubble blur/visibility guards."""
    if quality["issues"]:
        return engine.unreadable(section.id, question, ",".join(quality["issues"])), []
    guard = engine.read_question(gray, valid, edges, section, question)
    if guard["status"] == "unreadable":
        return guard, []
    measurements = [
        choice_evidence(
            engine.gray_reference, gray, valid, section, question, c, raw_gray, engine.reference
        )
        for c in range(1, section.choices + 1)
    ]
    return decide_question(section.id, question, [m[0] for m in measurements]), [
        m[1] for m in measurements
    ]
