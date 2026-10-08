"""Experimental, bounded frame alignment. No answer labels enter this module."""

from __future__ import annotations

import cv2
import numpy as np

from .config import Section


def _correlation(reference: np.ndarray, sample: np.ndarray, mask: np.ndarray) -> float:
    a, b = reference[mask].astype(float), sample[mask].astype(float)
    if min(a.std(), b.std()) < 1:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def refine_section(
    reference: np.ndarray, aligned: np.ndarray, valid: np.ndarray, section: Section
) -> dict:
    """Return reference->globally-aligned affine geometry and acceptance diagnostics.

    Inputs are page-sized grayscale images in reference coordinates. Search uses only
    printed frame bands with an expanded exclusion around every answer bubble. A
    correction cannot move any section corner by more than 0.3 of the smallest grid
    pitch (and never more than 10 reference pixels). This is not a page-registration
    fallback and must only follow a checked global homography.
    """
    if reference.ndim != 2 or reference.shape != aligned.shape or valid.shape != aligned.shape:
        raise ValueError("Expected matching page-sized grayscale images and valid mask")
    pitch = min(np.linalg.norm(section.question_step), np.linalg.norm(section.choice_step))
    limit = min(10.0, 0.3 * float(pitch))
    x, y, w, h = section.bounds
    pad = int(np.ceil(limit)) + 8
    x0, y0 = max(0, int(x) - pad), max(0, int(y) - pad)
    x1, y1 = (
        min(reference.shape[1], int(np.ceil(x + w)) + pad),
        min(reference.shape[0], int(np.ceil(y + h)) + pad),
    )
    ref, sample = reference[y0:y1, x0:x1], aligned[y0:y1, x0:x1]
    yy, xx = np.mgrid[y0:y1, x0:x1]
    bands = [
        (np.abs(yy - y) <= 4) & (xx >= x) & (xx <= x + w),
        (np.abs(yy - (y + h)) <= 4) & (xx >= x) & (xx <= x + w),
        (np.abs(xx - x) <= 4) & (yy >= y) & (yy <= y + h),
        (np.abs(xx - (x + w)) <= 4) & (yy >= y) & (yy <= y + h),
    ]
    exclusion = np.zeros(ref.shape, np.uint8)
    rx, ry = section.bubble_radius
    for question in range(1, section.questions + 1):
        for choice in range(1, section.choices + 1):
            cx, cy = section.center(question, choice)
            cv2.ellipse(
                exclusion,
                (round(cx - x0), round(cy - y0)),
                (int(np.ceil(rx * 1.3 + limit)), int(np.ceil(ry * 1.3 + limit))),
                0,
                0,
                360,
                255,
                -1,
            )
    stable = np.logical_or.reduce(bands) & (exclusion == 0)
    ink = stable & (ref < 170)
    side_ink = [band & ink for band in bands]
    result = {
        "method": "frame_ecc_affine_v1",
        "status": "rejected",
        "reason": None,
        "max_allowed_displacement_px": limit,
        "reference_to_global": None,
        "stable_pixels": int(stable.sum()),
        "side_ink_pixels": [int(mask.sum()) for mask in side_ink],
    }
    if stable.sum() < 150 or any(mask.sum() < 20 for mask in side_ink):
        result["reason"] = "insufficient_printed_frame"
        return result
    if np.mean(valid[y0:y1, x0:x1][stable] > 250) < 0.995:
        result["reason"] = "cropped_frame"
        return result

    # Mask both inputs before smoothing so student marks cannot drive ECC indirectly.
    search = cv2.dilate(stable.astype(np.uint8), np.ones((pad, pad), np.uint8)) > 0
    search &= exclusion == 0
    ref_input = np.where(search, ref, 255).astype(np.uint8)
    sample_input = np.where(search, sample, 255).astype(np.uint8)
    # A small exhaustive translation seed avoids ECC's narrow convergence basin.
    # Samples come only from the same printed-frame mask, never from the answer grid.
    sy, sx = np.nonzero(stable)
    sy, sx = sy[::3], sx[::3]
    expected = ref_input[sy, sx].astype(float)
    expected -= expected.mean()
    expected_norm = np.linalg.norm(expected)
    best, seed = -1.0, (0, 0)
    radius = int(np.floor(limit))
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy > limit * limit:
                continue
            ty, tx = sy + dy, sx + dx
            if (
                ty.min() < 0
                or tx.min() < 0
                or ty.max() >= sample.shape[0]
                or tx.max() >= sample.shape[1]
            ):
                continue
            values = sample_input[ty, tx].astype(float)
            values -= values.mean()
            score = float(np.dot(expected, values) / max(expected_norm * np.linalg.norm(values), 1))
            if score > best:
                best, seed = score, (dx, dy)
    result["translation_seed_px"] = list(seed)
    initial = np.array([[1, 0, seed[0]], [0, 1, seed[1]]], dtype=np.float32)
    try:
        ecc, warp = cv2.findTransformECC(
            ref_input,
            sample_input,
            initial,
            cv2.MOTION_AFFINE,
            (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 1e-5),
            inputMask=stable.astype(np.uint8) * 255,
            gaussFiltSize=5,
        )
    except cv2.error:
        result["reason"] = "ecc_failed"
        return result
    result["ecc"] = float(ecc)
    if not np.isfinite(warp).all() or not np.isfinite(ecc):
        result["reason"] = "nonfinite_transform"
        return result
    origin = np.array([[1, 0, x0], [0, 1, y0], [0, 0, 1]], dtype=float)
    local = origin @ np.vstack([warp, [0, 0, 1]]) @ np.linalg.inv(origin)
    corners = np.array([[[x, y], [x + w, y], [x + w, y + h], [x, y + h]]], float)
    displacement = float(
        np.linalg.norm(cv2.perspectiveTransform(corners, local) - corners, axis=2).max()
    )
    result["max_displacement_px"] = displacement
    scales = np.linalg.svd(warp[:, :2], compute_uv=False)
    if displacement > limit or np.linalg.det(warp[:, :2]) <= 0 or np.max(np.abs(scales - 1)) > 0.04:
        result["reason"] = "excessive_transform"
        return result
    corrected = cv2.warpAffine(
        sample,
        warp,
        (ref.shape[1], ref.shape[0]),
        flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
        borderValue=255,
    )
    corrected_valid = cv2.warpAffine(
        valid[y0:y1, x0:x1],
        warp,
        (ref.shape[1], ref.shape[0]),
        flags=cv2.INTER_NEAREST | cv2.WARP_INVERSE_MAP,
        borderValue=0,
    )
    if np.mean(corrected_valid[stable] > 250) < 0.995:
        result["reason"] = "cropped_corrected_frame"
        return result

    def support(gray: np.ndarray) -> list[float]:
        distances = cv2.distanceTransform((gray >= 170).astype(np.uint8), cv2.DIST_L2, 3)
        return [float(np.mean(distances[mask] <= 1.5)) for mask in side_ink]

    before, after = support(sample), support(corrected)
    correlation_before = _correlation(ref, sample, stable)
    correlation_after = _correlation(ref, corrected, stable)
    result.update(
        side_support_before=before,
        side_support_after=after,
        correlation_before=correlation_before,
        correlation_after=correlation_after,
    )
    if min(after) < 0.8 or correlation_after < 0.8 or ecc < 0.8:
        result["reason"] = "insufficient_frame_agreement"
        return result
    if any(a < b - 0.02 for b, a in zip(before, after, strict=True)):
        result["reason"] = "side_regression"
        return result
    if correlation_after < correlation_before + 0.01:
        # Keep global geometry only if its own frame checks pass; no claimed local gain.
        if min(before) >= 0.8 and correlation_before >= 0.8:
            result.update(
                status="unchanged",
                reason="no_measured_gain",
                reference_to_global=np.eye(3).tolist(),
            )
        else:
            result["reason"] = "no_measured_gain"
        return result
    result.update(
        status="accepted", reason="frame_agreement_improved", reference_to_global=local.tolist()
    )
    return result
