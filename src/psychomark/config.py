"""Versioned, strictly validated templates and explicit exam selections."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_PIXELS = 20_000_000
Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")]


class ConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Section(ConfigModel):
    id: Identifier
    questions: Annotated[int, Field(strict=True, ge=1, le=100)]
    choices: Annotated[int, Field(strict=True, ge=2, le=10)] = 4
    bounds: tuple[float, float, float, float]
    first_center: tuple[float, float]
    question_step: tuple[float, float]
    choice_step: tuple[float, float]
    bubble_radius: tuple[float, float]

    def center(self, question: int, choice: int) -> tuple[float, float]:
        return tuple(
            self.first_center[k]
            + (question - 1) * self.question_step[k]
            + (choice - 1) * self.choice_step[k]
            for k in (0, 1)
        )

    @model_validator(mode="after")
    def geometry(self):
        x, y, w, h = self.bounds
        rx, ry = self.bubble_radius
        if min(x, y) < 0 or min(w, h) <= 0 or not (2 <= min(rx, ry) <= max(rx, ry) <= 100):
            raise ValueError("Invalid section bounds or bubble radii")
        q, c = np.array(self.question_step), np.array(self.choice_step)
        if abs(q[0] * c[1] - q[1] * c[0]) < 1:
            raise ValueError("Question and choice axes must be distinct")
        centers = np.array([self.center(i, j) for i in range(1, self.questions + 1)
                            for j in range(1, self.choices + 1)])
        if np.any(centers[:, 0] - rx < x) or np.any(centers[:, 0] + rx > x + w) or \
           np.any(centers[:, 1] - ry < y) or np.any(centers[:, 1] + ry > y + h):
            raise ValueError("Every bubble must fit inside its section bounds")
        normalized = centers / np.array([rx, ry])
        distances = np.linalg.norm(normalized[:, None] - normalized[None, :], axis=2)
        np.fill_diagonal(distances, np.inf)
        if np.min(distances) < 2:
            raise ValueError("Bubble regions must not overlap")
        return self


class Thresholds(ConfigModel):
    # Heuristic scores, NOT calibrated probabilities.
    marked_coverage: float = Field(default=0.22, gt=0, le=1)
    trace_coverage: float = Field(default=0.08, gt=0, le=1)
    dark_delta: int = Field(default=75, ge=1, le=254)
    trace_delta: int = Field(default=28, ge=1, le=254)
    min_sharpness_ratio: float = Field(default=0.25, gt=0, le=1)
    min_bubble_edge_ratio: float = Field(default=0.15, gt=0, le=1)
    min_frame_support: float = Field(default=0.78, gt=0, le=1)
    min_source_bubble_diameter: float = Field(default=9, ge=4, le=100)

    @model_validator(mode="after")
    def order(self):
        if self.trace_coverage >= self.marked_coverage or self.trace_delta >= self.dark_delta:
            raise ValueError("Trace thresholds must be lower than marked thresholds")
        return self


class Layout(ConfigModel):
    schema_version: Literal[1] = 1
    template_id: Identifier
    width: Annotated[int, Field(strict=True, ge=128, le=10000)]
    height: Annotated[int, Field(strict=True, ge=128, le=10000)]
    sections: list[Section] = Field(min_length=1, max_length=50)
    thresholds: Thresholds = Field(default_factory=Thresholds)

    @model_validator(mode="after")
    def canvas(self):
        if self.width * self.height > MAX_PIXELS:
            raise ValueError("Reference image exceeds the 20 megapixel limit")
        if len({s.id for s in self.sections}) != len(self.sections):
            raise ValueError("Section identifiers must be unique")
        for s in self.sections:
            x, y, w, h = s.bounds
            if x + w >= self.width or y + h >= self.height:
                raise ValueError(f"Section {s.id} is outside the reference image")
        for i, a in enumerate(self.sections):
            ax, ay, aw, ah = a.bounds
            for b in self.sections[i + 1:]:
                bx, by, bw, bh = b.bounds
                if min(ax + aw, bx + bw) > max(ax, bx) and min(ay + ah, by + bh) > max(ay, by):
                    raise ValueError("Section bounds must not overlap")
        return self


class Template(Layout):
    reference: str = Field(min_length=1)
    reference_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class Exam(ConfigModel):
    name: str = Field(default="exam", min_length=1, max_length=200)
    template_id: Identifier
    sections: dict[str, list[Annotated[int, Field(strict=True, ge=1)]]] = Field(min_length=1)

    def validate_for(self, template: Layout) -> None:
        if self.template_id != template.template_id:
            raise ValueError("Exam and template identifiers do not match")
        sections = {s.id: s for s in template.sections}
        for sid, questions in self.sections.items():
            if sid not in sections:
                raise ValueError(f"Unknown section: {sid}")
            if not questions or len(set(questions)) != len(questions):
                raise ValueError(f"Section {sid} must select unique, nonempty questions")
            if max(questions) > sections[sid].questions:
                raise ValueError(f"Question outside section {sid}")


def read_config(path: Path, cls):
    return cls.model_validate_json(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict | list) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
