"""A local CLI: no server, database or student account required."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
from pathlib import Path
import re
import sys

import cv2

from .calibration import calibrate
from .config import Exam, Layout, read_config, write_json
from .demo import create_demo
from .engine import Engine
from .images import SUPPORTED, iter_pages, read_image, save_image


def parser():
    root = argparse.ArgumentParser(description="PsychoMark — deterministic local OMR (no AI)")
    commands = root.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="Generate a synthetic sheet, marked examples and ground truth")
    demo.add_argument("--output", type=Path, required=True)
    demo.add_argument("--vertical", action="store_true", help="Generate a different 5-choice vertical layout")
    calibration = commands.add_parser("calibrate", help="Create a template from a blank IMAGE and a pixel layout")
    calibration.add_argument("reference", type=Path)
    calibration.add_argument("--layout", type=Path, required=True)
    calibration.add_argument("--output", type=Path, required=True, help="Destination template JSON")
    analysis = commands.add_parser("analyze", help="Analyze one or more images, PDFs or flat image directories")
    analysis.add_argument("inputs", nargs="+", type=Path)
    analysis.add_argument("--template", type=Path, required=True)
    analysis.add_argument("--exam", type=Path, help="Explicit section/question selection; default: all template questions")
    analysis.add_argument("--output", type=Path, required=True, help="New or empty output directory")
    analysis.add_argument("--dpi", type=int, default=200, choices=range(100, 401), metavar="100..400")
    return root


def expand_inputs(inputs):
    files = []
    for path in inputs:
        if path.is_dir():
            found = sorted(p for p in path.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED)
            if not found:
                raise ValueError(f"No supported input files in {path}")
            files.extend(found)
        else:
            files.append(path)
    # Stable deduplication; output is separate from input and never overwritten.
    return list(dict.fromkeys(p.resolve() for p in files))


def analyze(args):
    engine = Engine.from_file(args.template)
    exam = read_config(args.exam, Exam) if args.exam else None
    if exam:
        exam.validate_for(engine.template)
    files = expand_inputs(args.inputs)
    if args.output.exists() and (not args.output.is_dir() or any(args.output.iterdir())):
        raise ValueError("Output directory must be new or empty; existing results are never overwritten")
    args.output.mkdir(parents=True, exist_ok=True)
    report = {"schema_version": 1, "template_id": engine.template.template_id, "pages": []}
    failure = False
    for index, path in enumerate(files, 1):
        file_digest = None
        try:
            if path.is_file() and path.stat().st_size <= 64 * 1024 * 1024:
                file_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            pass  # iter_pages records inaccessible files without aborting the batch.
        for page in iter_pages(path, args.dpi):
            safe_name = re.sub(r"[^A-Za-z0-9_-]", "_", path.stem)[:60] or "file"
            stem = f"{index:03d}-{safe_name}-page{page.number:03d}"
            if page.error:
                result = {"schema_version": 1, "status": "input_error", "error": page.error, "answers": []}
                failure = True
            else:
                result, preview = engine.analyze(page.image, exam)
                save_image(args.output / (stem + ".annotated.png"), preview)
                failure |= any(a["status"] == "unreadable" for a in result["answers"])
            result.update({"file": path.name, "file_sha256": file_digest, "page": page.number})
            write_json(args.output / (stem + ".json"), result)
            with (args.output / (stem + ".csv")).open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["section", "question", "status", "answer", "candidates", "reason"])
                writer.writeheader()
                for answer in result["answers"]:
                    writer.writerow({key: ",".join(map(str, answer[key])) if key == "candidates" else answer[key]
                                     for key in writer.fieldnames})
            counts = dict(Counter(a["status"] for a in result["answers"]))
            report["pages"].append({"file": path.name, "page": page.number, "status": result["status"],
                                    "counts": counts, "result": stem + ".json"})
            print(f"{path.name} / page {page.number}: {result['status']} {counts}")
    report["has_failures"] = failure
    write_json(args.output / "summary.json", report)
    return 1 if failure else 0


def main(argv=None):
    args = parser().parse_args(argv)
    cv2.setNumThreads(2)
    try:
        if args.command == "demo":
            create_demo(args.output, args.vertical)
            print(f"Synthetic fixtures created in {args.output} (not real-world validation).")
        elif args.command == "calibrate":
            calibrate(read_image(args.reference), read_config(args.layout, Layout), args.output)
            print(f"Template saved: {args.output}. Inspect the .preview.png overlay before use.")
        else:
            return analyze(args)
        return 0
    except (ValueError, OSError, cv2.error) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
