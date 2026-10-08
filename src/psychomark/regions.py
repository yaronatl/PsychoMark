"""Diagnostic regions in reference pixels; never infer geometry from answer marks."""

from __future__ import annotations

import math
from typing import Literal

import cv2
import numpy as np
from pydantic import Field

from .config import ConfigModel, Identifier, Section
from .engine import bubble_roi


class ChoiceRegion(ConfigModel):
    choice: int = Field(ge=1, le=10)
    reference_center: tuple[float, float]
    source_center: tuple[float, float]
    reference_bounds: tuple[int, int, int, int]
    source_quad: list[tuple[float, float]] = Field(min_length=4, max_length=4)
    source_diameters_px: tuple[float, float]
    valid_fraction: float = Field(ge=0, le=1)


class QuestionRegion(ConfigModel):
    schema_version: Literal[1] = 1
    section: Identifier
    question: int = Field(ge=1)
    reference_bounds: tuple[int, int, int, int]
    source_quad: list[tuple[float, float]] = Field(min_length=4, max_length=4)
    source_bounds: tuple[int, int, int, int]
    valid_fraction: float = Field(ge=0, le=1)
    choices: list[ChoiceRegion] = Field(min_length=2, max_length=10)


def project_points(
    points: list[tuple[float, float]], transform: np.ndarray
) -> list[tuple[float, float]]:
    """Map pixel coordinates with a reference-to-source (or inverse) homography."""
    mapped = cv2.perspectiveTransform(np.asarray([points], dtype=np.float64), transform)[0]
    if not np.isfinite(mapped).all():
        raise ValueError("Non-finite region projection")
    return [tuple(map(float, point)) for point in mapped]


def corners(bounds: tuple[int, int, int, int]) -> list[tuple[float, float]]:
    """Pixel centers at the corners of an x0,y0,x1,y1 half-open crop."""
    x0, y0, x1, y1 = bounds
    return [(x0, y0), (x1 - 1, y0), (x1 - 1, y1 - 1), (x0, y1 - 1)]


def crop(image: np.ndarray, bounds: tuple[int, int, int, int]) -> np.ndarray:
    """Return an unscaled view; bounds must already be clipped to this image."""
    x0, y0, x1, y1 = bounds
    return image[y0:y1, x0:x1]


def question_region(
    section: Section,
    question: int,
    reference_to_source: np.ndarray,
    valid: np.ndarray,
    source_shape: tuple[int, int],
) -> QuestionRegion:
    """Describe the exact bubble ROI used by the historical reader, even on rejection.

    Coordinates refer to the decoded/oriented source, not EXIF storage coordinates.
    Source diameters are measured before resizing. Validity is coverage, not confidence.
    """
    if not 1 <= question <= section.questions:
        raise ValueError("Question outside section")
    choices = []
    for choice in range(1, section.choices + 1):
        roi, _ = bubble_roi(section, question, choice)
        bounds = (roi[1].start, roi[0].start, roi[1].stop, roi[0].stop)
        cx, cy = section.center(question, choice)
        rx, ry = section.bubble_radius
        ends = project_points(
            [(cx - rx, cy), (cx + rx, cy), (cx, cy - ry), (cx, cy + ry)],
            reference_to_source,
        )
        choices.append(
            ChoiceRegion(
                choice=choice,
                reference_center=(cx, cy),
                source_center=project_points([(cx, cy)], reference_to_source)[0],
                reference_bounds=bounds,
                source_quad=project_points(corners(bounds), reference_to_source),
                source_diameters_px=(math.dist(ends[0], ends[1]), math.dist(ends[2], ends[3])),
                valid_fraction=float(np.mean(valid[roi] > 250)),
            )
        )
    # Context is kept at native reference scale; overlays identify the intended options.
    height, width = valid.shape
    margin = 3
    bounds = (
        max(0, min(c.reference_bounds[0] for c in choices) - margin),
        max(0, min(c.reference_bounds[1] for c in choices) - margin),
        min(width, max(c.reference_bounds[2] for c in choices) + margin),
        min(height, max(c.reference_bounds[3] for c in choices) + margin),
    )
    quad = project_points(corners(bounds), reference_to_source)
    source_height, source_width = source_shape
    source_bounds = (
        max(0, min(source_width, math.floor(min(p[0] for p in quad)))),
        max(0, min(source_height, math.floor(min(p[1] for p in quad)))),
        max(0, min(source_width, math.ceil(max(p[0] for p in quad)) + 1)),
        max(0, min(source_height, math.ceil(max(p[1] for p in quad)) + 1)),
    )
    return QuestionRegion(
        section=section.id,
        question=question,
        reference_bounds=bounds,
        source_quad=quad,
        source_bounds=source_bounds,
        valid_fraction=float(np.mean(crop(valid, bounds) > 250)),
        choices=choices,
    )
