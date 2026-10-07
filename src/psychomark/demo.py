"""Reproducible synthetic fixtures; not evidence of real-world accuracy."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from .calibration import calibrate
from .config import Exam, Layout, Section, write_json
from .images import save_image


def make_layout(vertical: bool = False) -> Layout:
    if vertical:
        sections = [Section(id=str(i+1), questions=12, choices=5, bounds=(100+i*550, 300, 420, 700),
                            first_center=(150+i*550, 365), question_step=(0, 53),
                            choice_step=(70, 0), bubble_radius=(12, 12)) for i in range(3)]
        identifier = "demo_vertical_v1"
    else:
        sections = []
        for i in range(8):
            x = 80 if i < 5 else 930
            y = 280 + i*190 if i < 5 else 660 + (i-5)*190
            sections.append(Section(id=str(i+1), questions=30, choices=4, bounds=(x, y, 795, 158),
                                    first_center=(x+14, y+40), question_step=(26.5, 0),
                                    choice_step=(0, 30), bubble_radius=(8, 11)))
        identifier = "demo_eight_sections_v1"
    return Layout(template_id=identifier, width=1800, height=1320, sections=sections)


def render_blank(layout: Layout) -> np.ndarray:
    image = np.full((layout.height, layout.width, 3), 255, np.uint8)
    cv2.putText(image, "PSYCHOMARK / SYNTHETIC REFERENCE", (80, 85), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (50,)*3, 2, cv2.LINE_AA)
    cv2.putText(image, "No real students. Demo layout only.", (80, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (90,)*3, 2, cv2.LINE_AA)
    cv2.putText(image, "Template: " + layout.template_id, (80, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (60,)*3, 1, cv2.LINE_AA)
    if len(layout.sections) == 8:
        cv2.putText(image, "OMR", (1030, 395), cv2.FONT_HERSHEY_COMPLEX, 3, (75,)*3, 4, cv2.LINE_AA)
        cv2.putText(image, "REFERENCE MODEL 01", (1000, 465), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (65,)*3, 2, cv2.LINE_AA)
    for section in layout.sections:
        x, y, w, h = (round(v) for v in section.bounds)
        cv2.rectangle(image, (x, y), (x+w, y+h), (85,)*3, 2)
        cv2.putText(image, f"SECTION {section.id}", (x, y-12), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (70,)*3, 1, cv2.LINE_AA)
        for q in range(1, section.questions+1):
            cx, cy = section.center(q, 1)
            vertical = section.question_step[1] != 0
            origin = (round(cx)-40, round(cy)+5) if vertical else (round(cx)-6, y+17)
            cv2.putText(image, str(q), origin, cv2.FONT_HERSHEY_SIMPLEX, 0.3, (110,)*3, 1, cv2.LINE_AA)
            for c in range(1, section.choices+1):
                center = tuple(round(v) for v in section.center(q, c))
                axes = tuple(round(v) for v in section.bubble_radius)
                cv2.ellipse(image, center, axes, 0, 0, 360, (145,)*3, 1, cv2.LINE_AA)
                cv2.putText(image, str(c), (center[0]-2, center[1]+3), cv2.FONT_HERSHEY_SIMPLEX, 0.23, (155,)*3, 1, cv2.LINE_AA)
    cv2.putText(image, "PsychoMark - local OMR - generated test sheet - version 1", (120, 1270), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (65,)*3, 2, cv2.LINE_AA)
    return image


def draw_mark(image, section, question, choice, kind="fill"):
    x, y = (round(v) for v in section.center(question, choice))
    rx, ry = (max(2, round(v*0.7)) for v in section.bubble_radius)
    color = (185,)*3 if kind == "erase" else (35,)*3
    if kind in {"fill", "erase"}:
        cv2.ellipse(image, (x, y), (rx, ry), 0, 0, 360, color, -1, cv2.LINE_AA)
    elif kind == "cross":
        cv2.line(image, (x-rx, y-ry), (x+rx, y+ry), color, 3, cv2.LINE_AA)
        cv2.line(image, (x-rx, y+ry), (x+rx, y-ry), color, 3, cv2.LINE_AA)
    elif kind == "tick":
        cv2.polylines(image, [np.int32([[x-rx, y], [x-1, y+ry], [x+rx, y-ry]])], False, color, 3, cv2.LINE_AA)
    else:
        raise ValueError(f"Unknown mark style: {kind}")


def render_filled(blank, layout):
    image = blank.copy()
    truth = []
    for index, section in enumerate(layout.sections):
        for q in range(1, section.questions+1):
            answer = (q+index) % section.choices + 1
            status = "single"
            if q == 3:
                draw_mark(image, section, q, 1)
                draw_mark(image, section, q, 3)
                status, answer = "multiple", None
            elif q == 4:
                draw_mark(image, section, q, 2)
                draw_mark(image, section, q, 4, "erase")
                status, answer = "uncertain", None
            elif q == 5:
                status, answer = "blank", None
            elif q == 7:
                draw_mark(image, section, q, 1, "erase")
                status, answer = "uncertain", None
            else:
                kind = "cross" if q == 2 else "tick" if q == 6 else "fill"
                draw_mark(image, section, q, answer, kind)
            truth.append({"section": section.id, "question": q, "status": status, "answer": answer})
    return image, truth


def perspective(image):
    h, w = image.shape[:2]
    corners = np.float32([[0, 0], [w-1, 0], [w-1, h-1], [0, h-1]])
    target = np.float32([[65, 55], [w-95, 10], [w-20, h-60], [25, h-15]])
    transform = cv2.getPerspectiveTransform(corners, target)
    warped = cv2.warpPerspective(image, transform, (w, h), borderValue=(225,)*3)
    # Moderate lighting variation and deterministic sensor noise.
    lighting = np.linspace(0.76, 1.0, w)[None, :, None]
    noise = np.random.default_rng(42).normal(0, 1.3, warped.shape)
    return np.clip(warped.astype(float)*lighting+noise, 0, 255).astype(np.uint8)


def create_demo(output: Path, vertical: bool = False):
    if output.exists() and any(output.iterdir()):
        raise ValueError("Demo output directory must be empty")
    output.mkdir(parents=True, exist_ok=True)
    layout = make_layout(vertical)
    blank = render_blank(layout)
    filled, truth = render_filled(blank, layout)
    save_image(output / "blank.png", blank)
    save_image(output / "copy.png", filled)
    save_image(output / "copy-perspective.jpg", perspective(filled))
    save_image(output / "copy-rotated.png", cv2.rotate(filled, cv2.ROTATE_180))
    save_image(output / "copy-blurred.png", cv2.GaussianBlur(filled, (0, 0), 7))
    write_json(output / "layout.json", layout.model_dump())
    calibrate(blank, layout, output / "template.json")
    exam = Exam(name="Short practice exam (synthetic)", template_id=layout.template_id,
                sections={layout.sections[0].id: list(range(1, 13)), layout.sections[-1].id: list(range(1, 9))})
    write_json(output / "exam.json", exam.model_dump())
    write_json(output / "ground-truth.json", truth)
    write_json(output / "provenance.json", {"synthetic": True,
               "warning": "Generated test data, not calibrated to NITE or Adar sheets; not a real-world accuracy benchmark."})
