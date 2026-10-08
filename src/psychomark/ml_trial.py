"""S06 private data preparation and optional CPU model experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2

from .ml_data import dataset_summary, prepare_dataset, synthetic_dataset


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser(
        "prepare", help="Prepare proposed case crops from an extracted S02 export"
    )
    prepare.add_argument("manifest", type=Path)
    synthetic = sub.add_parser(
        "synthetic", help="Generate technical test examples, not real validation"
    )
    synthetic.add_argument("--seed", type=int, default=17)
    synthetic.add_argument("--groups", type=int, default=8)
    train = sub.add_parser("train", help="Train on authorized, verified train groups only")
    train.add_argument("datasets", nargs="+", type=Path)
    train.add_argument("--epochs", type=int, default=8)
    train.add_argument("--seed", type=int, default=17)
    train.add_argument("--paired-reference", action="store_true")
    predict = sub.add_parser("predict", help="Diagnostic observations only; no automatic answers")
    predict.add_argument("dataset", type=Path)
    predict.add_argument("--model", type=Path, required=True)
    for command in (prepare, synthetic, train, predict):
        command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            report = prepare_dataset(args.manifest, args.output)
            result = dataset_summary(report["samples"])
        elif args.command == "synthetic":
            report = synthetic_dataset(args.output, args.seed, args.groups)
            result = dataset_summary(report["samples"])
        else:
            try:
                from .ml_reader import predict_dataset, train_model
            except ModuleNotFoundError as exc:
                if exc.name != "torch":
                    raise
                raise ValueError(
                    "S06 training/inference requires the optional ml extra: uv sync --frozen --extra dev --extra ml"
                ) from exc
            if args.command == "train":
                report = train_model(
                    args.datasets,
                    args.output,
                    epochs=args.epochs,
                    seed=args.seed,
                    paired_reference=args.paired_reference,
                )
                result = {
                    "train": report["train"],
                    "development_metrics": report["development_metrics"],
                    "automatic_decisions_enabled": False,
                }
            else:
                report = predict_dataset(args.model, args.dataset, args.output)
                result = {"dataset": report["dataset"], "automatic_decisions": 0}
    except (ValueError, OSError, KeyError, TypeError, cv2.error) as exc:
        parser.exit(2, f"S06 failed: {exc}\n")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
