"""Reference registration based on ORB descriptors and checked RANSAC geometry."""

from __future__ import annotations

import cv2
import numpy as np

from .config import Layout, Section


class RegistrationError(ValueError):
    pass


def feature_mask(layout: Layout) -> np.ndarray:
    mask = np.full((layout.height, layout.width), 255, np.uint8)
    # Do not use the student's answer marks as reference landmarks.
    for section in layout.sections:
        axes = tuple(int(np.ceil(r * 1.3)) for r in section.bubble_radius)
        for question in range(1, section.questions + 1):
            for choice in range(1, section.choices + 1):
                center = tuple(round(v) for v in section.center(question, choice))
                cv2.ellipse(mask, center, axes, 0, 0, 360, 0, -1)
    return mask


def frame_mask(section: Section, shape: tuple[int, int]) -> np.ndarray:
    x, y, w, h = (round(v) for v in section.bounds)
    mask = np.zeros(shape, np.uint8)
    cv2.rectangle(mask, (x, y), (x + w, y + h), 255, 7)
    return mask


class Registrar:
    def __init__(self, reference: np.ndarray, layout: Layout):
        self.layout = layout
        self.orb = cv2.ORB_create(nfeatures=6000, fastThreshold=7, edgeThreshold=15)
        self.keypoints, self.descriptors = self.orb.detectAndCompute(reference, feature_mask(layout))
        if self.descriptors is None or len(self.keypoints) < 20:
            raise ValueError("Reference has too few stable landmarks; use a clearer or more distinctive sheet")

    def align(self, image: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Bound matching cost while retaining the homography in original input coordinates.
        scale = min(1.0, 2400 / max(gray.shape))
        working = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1 else gray
        points, descriptors = self.orb.detectAndCompute(working, None)
        if descriptors is None or len(points) < 20:
            raise RegistrationError("Too few recognizable landmarks")
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
        pairs = matcher.knnMatch(descriptors, self.descriptors, k=2)
        matches = sorted((a for pair in pairs if len(pair) == 2 for a, b in [pair]
                          if a.distance < 0.72 * b.distance), key=lambda m: m.distance)
        # A reference landmark may support at most one source landmark.
        unique = {}
        for match in matches:
            unique.setdefault(match.trainIdx, match)
        matches = list(unique.values())
        if len(matches) < 20:
            raise RegistrationError("Insufficient matches to the selected template")
        source = np.float32([points[m.queryIdx].pt for m in matches]) / scale
        target = np.float32([self.keypoints[m.trainIdx].pt for m in matches])
        cv2.setRNGSeed(0)
        transform, inlier_mask = cv2.findHomography(source, target, cv2.RANSAC, 2.5, maxIters=5000, confidence=0.999)
        if transform is None or inlier_mask is None or not np.isfinite(transform).all():
            raise RegistrationError("Could not estimate a stable page alignment")
        inliers = inlier_mask.ravel().astype(bool)
        count = int(inliers.sum())
        fraction = count / len(matches)
        coverage = cv2.contourArea(cv2.convexHull(target[inliers])) / (self.layout.width * self.layout.height)
        if count < 20 or fraction < 0.35 or coverage < 0.12:
            raise RegistrationError("Alignment landmarks are insufficiently consistent or distributed")
        projected = cv2.perspectiveTransform(source[inliers, None, :], transform)[:, 0, :]
        median_error = float(np.median(np.linalg.norm(projected - target[inliers], axis=1)))
        if median_error > 1.5:
            raise RegistrationError("Alignment error is too large for bubble reading")
        try:
            inverse = np.linalg.inv(transform)
        except np.linalg.LinAlgError as exc:
            raise RegistrationError("Singular alignment") from exc
        corners = np.float32([[0, 0], [self.layout.width - 1, 0],
                              [self.layout.width - 1, self.layout.height - 1], [0, self.layout.height - 1]])
        original_corners = cv2.perspectiveTransform(corners[None], inverse)[0]
        area = cv2.contourArea(original_corners, oriented=True)
        if not np.isfinite(original_corners).all() or not cv2.isContourConvex(original_corners) or \
           not 0.15 <= area / (image.shape[0] * image.shape[1]) <= 4:
            raise RegistrationError("Implausible or mirrored page geometry")
        dimensions = (self.layout.width, self.layout.height)
        aligned = cv2.warpPerspective(image, transform, dimensions, borderValue=(255, 255, 255))
        valid = cv2.warpPerspective(np.full(gray.shape, 255, np.uint8), transform, dimensions, flags=cv2.INTER_NEAREST)
        return aligned, valid, inverse, {
            "method": "orb_ransac", "matches": len(matches), "inliers": count,
            "inlier_fraction": round(fraction, 4), "reference_coverage": round(coverage, 4),
            "median_error_px": round(median_error, 4), "input_to_reference": transform.tolist(),
        }
