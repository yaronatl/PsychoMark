"""Answer extraction only: deliberately has no access to an answer key."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

from . import __version__
from .config import Exam, Section, Template, read_config
from .images import normalized_gray, read_image
from .registration import Registrar, RegistrationError, frame_mask

COLORS = {"single": (40, 155, 30), "blank": (155, 155, 155), "multiple": (0, 80, 230),
          "uncertain": (0, 175, 240), "unreadable": (0, 0, 230)}


def edge_energy(gray):
    # A smoothed first derivative is less sensitive to pixel phase / ordinary
    # perspective resampling than an unsmoothed second derivative on tiny rings.
    smoothed = cv2.GaussianBlur(gray, (0, 0), 1)
    return cv2.Sobel(smoothed, cv2.CV_32F, 1, 0)**2 + cv2.Sobel(smoothed, cv2.CV_32F, 0, 1)**2


def bubble_roi(section: Section, question: int, choice: int):
    cx, cy = section.center(question, choice)
    rx, ry = section.bubble_radius
    x0, y0 = int(np.floor(cx - rx)), int(np.floor(cy - ry))
    x1, y1 = int(np.ceil(cx + rx)) + 1, int(np.ceil(cy + ry)) + 1
    yy, xx = np.mgrid[y0:y1, x0:x1]
    interior = ((xx - cx) / (rx * 0.78)) ** 2 + ((yy - cy) / (ry * 0.78)) ** 2 <= 1
    return (slice(y0, y1), slice(x0, x1)), interior


def validate_reference(reference: np.ndarray, template: Template):
    if reference.shape[:2] != (template.height, template.width):
        raise ValueError("Reference dimensions do not match the template")
    gray = normalized_gray(reference)
    for section in template.sections:
        frame = frame_mask(section, gray.shape) > 0
        if int(np.count_nonzero(frame & (gray < 150))) < 80:
            raise ValueError(f"No usable printed frame at section {section.id}; check bounds")
        for q in range(1, section.questions + 1):
            for c in range(1, section.choices + 1):
                roi, interior = bubble_roi(section, q, c)
                paper = interior & (gray[roi] > 200)
                if paper.sum() < 12 or paper.sum() < interior.sum() * 0.45:
                    raise ValueError(f"Reference bubble {section.id}/{q}/{c} is too small, marked or misconfigured")


class Engine:
    def __init__(self, template: Template, reference: np.ndarray):
        validate_reference(reference, template)
        self.template = template
        self.reference = reference
        self.gray_reference = normalized_gray(reference)
        self.reference_edge_energy = edge_energy(self.gray_reference)
        self.registrar = Registrar(cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY), template)
        self.template_digest = hashlib.sha256(json.dumps(template.model_dump(), sort_keys=True).encode()).hexdigest()

    @classmethod
    def from_file(cls, path: Path):
        template = read_config(path, Template)
        reference_path = path.parent / template.reference
        if hashlib.sha256(reference_path.read_bytes()).hexdigest() != template.reference_sha256:
            raise ValueError("Reference checksum mismatch; recalibrate rather than editing a template reference")
        return cls(template, read_image(reference_path))

    def analyze(self, image: np.ndarray, exam: Exam | None = None) -> tuple[dict, np.ndarray]:
        template = self.template
        if exam is None:
            exam = Exam(template_id=template.template_id, sections={s.id: list(range(1, s.questions + 1)) for s in template.sections})
        exam.validate_for(template)
        result = {
            "schema_version": 1, "engine_version": __version__, "template_id": template.template_id,
            "template_sha256": self.template_digest, "reference_sha256": template.reference_sha256,
            "exam": exam.model_dump(), "status": "complete", "diagnostics": {}, "answers": [],
        }
        try:
            aligned, valid, inverse, diagnostic = self.registrar.align(image)
            result["diagnostics"]["registration"] = diagnostic
        except RegistrationError as exc:
            result["status"] = "unreadable"
            result["diagnostics"]["error"] = str(exc)
            for section in template.sections:
                for question in exam.sections.get(section.id, []):
                    result["answers"].append(self.unreadable(section.id, question, "registration_failed"))
            preview = image.copy()
            cv2.putText(preview, "UNREADABLE: alignment failed", (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLORS["unreadable"], 2)
            return result, preview

        gray = normalized_gray(aligned)
        edges = edge_energy(gray)
        preview = aligned.copy()
        result["diagnostics"]["sections"] = {}
        for section in template.sections:
            questions = exam.sections.get(section.id)
            if not questions:
                continue
            quality = self.section_quality(gray, valid, inverse, section)
            result["diagnostics"]["sections"][section.id] = quality
            for question in questions:
                if quality["issues"]:
                    answer = self.unreadable(section.id, question, ",".join(quality["issues"]))
                else:
                    answer = self.read_question(gray, valid, edges, section, question)
                result["answers"].append(answer)
                self.annotate(preview, section, answer)
        statuses = [a["status"] for a in result["answers"]]
        if all(s == "unreadable" for s in statuses):
            result["status"] = "unreadable"
        elif any(s in {"unreadable", "multiple", "uncertain"} for s in statuses):
            result["status"] = "needs_review"
        return result, preview

    @staticmethod
    def unreadable(section: str, question: int, reason: str) -> dict:
        return {"section": section, "question": question, "status": "unreadable", "answer": None,
                "candidates": [], "reason": reason, "scores": []}

    def section_quality(self, gray, valid, inverse, section):
        thresholds = self.template.thresholds
        x, y, w, h = (round(v) for v in section.bounds)
        frame = frame_mask(section, gray.shape) > 0
        printed = frame & (self.gray_reference < 150)
        nearest_ink = cv2.distanceTransform((gray >= 170).astype(np.uint8), cv2.DIST_L2, 3)
        support = float(np.mean(nearest_ink[printed] <= 2))
        ref_edges = cv2.Laplacian(self.gray_reference, cv2.CV_32F)[frame]
        sample_edges = cv2.Laplacian(gray, cv2.CV_32F)[frame]
        sharpness = float(np.mean(sample_edges ** 2) / max(float(np.mean(ref_edges ** 2)), 1))
        visible = float(np.mean(valid[y:y+h, x:x+w] > 250))
        rx, ry = section.bubble_radius
        diameters = []
        for q in (1, section.questions):
            for c in (1, section.choices):
                cx, cy = section.center(q, c)
                p = np.float32([[cx-rx, cy], [cx+rx, cy], [cx, cy-ry], [cx, cy+ry]])
                p = cv2.perspectiveTransform(p[None], inverse)[0]
                diameters.extend([float(np.linalg.norm(p[0]-p[1])), float(np.linalg.norm(p[2]-p[3]))])
        issues = []
        if visible < 0.995:
            issues.append("cropped_section")
        if min(diameters) < thresholds.min_source_bubble_diameter:
            issues.append("insufficient_resolution")
        if support < thresholds.min_frame_support:
            issues.append("frame_mismatch")
        if sharpness < thresholds.min_sharpness_ratio:
            issues.append("blurred_section")
        return {"frame_support": round(support, 4), "sharpness_ratio": round(sharpness, 4),
                "visible_fraction": round(visible, 4), "min_source_bubble_diameter": round(min(diameters), 3), "issues": issues}

    def read_question(self, gray, valid, edges, section, question):
        thresholds = self.template.thresholds
        scores = []
        for choice in range(1, section.choices + 1):
            roi, interior = bubble_roi(section, question, choice)
            # A crisp frame can surround locally blurred answers. Check the printed
            # bubble rings too, rather than interpreting lost marks as blanks.
            cx, cy = section.center(question, choice)
            rx, ry = section.bubble_radius
            yy, xx = np.mgrid[roi[0], roi[1]]
            radius = ((xx-cx)/rx)**2 + ((yy-cy)/ry)**2
            ring = (radius >= 0.82**2) & (radius <= 1.15**2)
            reference_energy = float(np.mean(self.reference_edge_energy[roi][ring]))
            sample_energy = float(np.mean(edges[roi][ring]))
            if sample_energy / max(reference_energy, 1) < thresholds.min_bubble_edge_ratio:
                return self.unreadable(section.id, question, "blurred_bubbles")
            mask = interior & (self.gray_reference[roi] > 200)
            if not np.all(valid[roi][mask] > 250):
                return self.unreadable(section.id, question, "cropped_bubble")
            delta = self.gray_reference[roi].astype(np.float32) - gray[roi].astype(np.float32)
            values = delta[mask]
            scores.append({"choice": choice,
                           "dark_coverage": round(float(np.mean(values >= thresholds.dark_delta)), 4),
                           "trace_coverage": round(float(np.mean(values >= thresholds.trace_delta)), 4),
                           "mean_delta": round(float(np.clip(values, 0, 255).mean()), 2)})
        strong = [s["choice"] for s in scores if s["dark_coverage"] >= thresholds.marked_coverage]
        traces = [s["choice"] for s in scores if s["trace_coverage"] >= thresholds.trace_coverage]
        answer = None
        if len(strong) > 1:
            status, reason, candidates = "multiple", "multiple_dark_marks", sorted(set(strong + traces))
        elif len(strong) == 1 and not set(traces) - set(strong):
            status, reason, candidates, answer = "single", "one_clear_mark", strong, strong[0]
        elif traces or strong:
            status, reason, candidates = "uncertain", "weak_or_competing_marks", sorted(set(strong + traces))
        else:
            status, reason, candidates = "blank", "no_detectable_mark", []
        return {"section": section.id, "question": question, "status": status, "answer": answer,
                "candidates": candidates, "reason": reason, "scores": scores}

    @staticmethod
    def annotate(preview, section, answer):
        color = COLORS[answer["status"]]
        question = answer["question"]
        for choice in range(1, section.choices + 1):
            center = tuple(round(v) for v in section.center(question, choice))
            axes = tuple(round(v) for v in section.bubble_radius)
            selected = choice == answer["answer"] or choice in answer["candidates"]
            cv2.ellipse(preview, center, axes, 0, 0, 360, color, 2 if selected else 1)
        first = section.center(question, 1)
        cv2.putText(preview, str(question), (round(first[0])-5, round(first[1]-section.bubble_radius[1])-4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
