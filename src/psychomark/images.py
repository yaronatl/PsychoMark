"""Bounded local image/PDF input. No OCR, network requests or remote services."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

from .config import MAX_PIXELS

MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_PDF_PAGES = 100
SUPPORTED = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".pdf"}


@dataclass
class Page:
    number: int
    image: np.ndarray | None = None
    error: str | None = None


def check_file(path: Path):
    if not path.is_file():
        raise ValueError(f"File does not exist: {path}")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("File exceeds 64 MiB")


def to_bgr(image: Image.Image) -> np.ndarray:
    if image.width * image.height > MAX_PIXELS:
        raise ValueError("Image exceeds 20 megapixels")
    image = ImageOps.exif_transpose(image)
    if "A" in image.getbands() or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, "white")
        image = Image.alpha_composite(background, rgba)
    return cv2.cvtColor(np.asarray(image.convert("RGB")), cv2.COLOR_RGB2BGR)


def read_image(path: Path) -> np.ndarray:
    check_file(path)
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(path) as image:
            if getattr(image, "n_frames", 1) > 1:
                raise ValueError("Multipage image unsupported: convert it to PDF first")
            return to_bgr(image)


def iter_pages(path: Path, dpi: int = 200):
    try:
        check_file(path)
        if path.suffix.lower() not in SUPPORTED:
            raise ValueError("Unsupported format; use PNG, JPEG, TIFF or PDF")
        if path.suffix.lower() != ".pdf":
            yield Page(1, read_image(path))
            return
        import pypdfium2 as pdfium

        with pdfium.PdfDocument(str(path)) as document:
            if not 1 <= len(document) <= MAX_PDF_PAGES:
                raise ValueError("PDF must contain between 1 and 100 pages")
            for index in range(len(document)):
                try:
                    page = document[index]
                    try:
                        w, h = page.get_size()
                        if int(w * dpi / 72 + 1) * int(h * dpi / 72 + 1) > MAX_PIXELS:
                            raise ValueError("Rendered PDF page exceeds 20 megapixels")
                        bitmap = page.render(scale=dpi / 72)
                        try:
                            data = to_bgr(bitmap.to_pil())
                        finally:
                            bitmap.close()
                    finally:
                        page.close()
                    yield Page(index + 1, data)
                except Exception as exc:
                    yield Page(index + 1, error=str(exc))
    except Exception as exc:
        yield Page(1, error=str(exc))


def normalized_gray(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Local paper estimate corrects moderate smooth shadows, without binarizing marks.
    paper = cv2.GaussianBlur(gray, (0, 0), sigmaX=25)
    return np.clip(gray.astype(np.float32) * 255 / np.maximum(paper, 40), 0, 255).astype(np.uint8)


def save_image(path: Path, image: np.ndarray):
    if not cv2.imwrite(str(path), image):
        raise OSError(f"Could not write image: {path}")
