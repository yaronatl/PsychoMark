"""Create a versioned template from a blank scan and explicit pixel geometry."""

from __future__ import annotations

import hashlib
from pathlib import Path

import cv2

from .config import Layout, Template, write_json
from .engine import Engine
from .images import save_image


def calibrate(reference, layout: Layout, output: Path) -> Template:
    reference_path = output.with_name(output.stem + ".reference.png")
    preview_path = output.with_name(output.stem + ".preview.png")
    for path in (output, reference_path, preview_path):
        if path.exists():
            raise ValueError(f"Refusing to overwrite {path}")
    ok, encoded = cv2.imencode(".png", reference)
    if not ok:
        raise ValueError("Could not encode reference")
    data = encoded.tobytes()
    template = Template(**layout.model_dump(), reference=reference_path.name,
                        reference_sha256=hashlib.sha256(data).hexdigest())
    Engine(template, reference)  # Fail before writing an unusable template.
    preview = reference.copy()
    for section in template.sections:
        x, y, w, h = (round(v) for v in section.bounds)
        cv2.rectangle(preview, (x, y), (x+w, y+h), (255, 100, 0), 2)
        for q in range(1, section.questions + 1):
            for c in range(1, section.choices + 1):
                center = tuple(round(v) for v in section.center(q, c))
                axes = tuple(round(v * 0.78) for v in section.bubble_radius)
                cv2.ellipse(preview, center, axes, 0, 0, 360, (0, 170, 0), 1)
                cv2.circle(preview, center, 1, (0, 0, 230), -1)
    output.parent.mkdir(parents=True, exist_ok=True)
    reference_path.write_bytes(data)
    save_image(preview_path, preview)
    write_json(output, template.model_dump())
    return template
