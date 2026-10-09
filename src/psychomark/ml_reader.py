"""Optional CPU CNN experiment. No answer key, grade or automatic decision policy."""

from __future__ import annotations

import json
import platform
import time
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from torch import nn

from .baseline import digest
from .config import write_json
from .ml_data import CLASSES, PREPROCESSING, dataset_summary, load_dataset, validate_groups

ARCHITECTURE = "bubble-cnn-v1"


class BubbleCNN(nn.Module):
    """Shared 4-class reader: 32px grayscale bubble, optionally paired blank reference."""

    def __init__(self, channels: int = 1) -> None:
        super().__init__()
        if channels not in (1, 2):
            raise ValueError("Use one source channel or source plus reference")
        self.channels = channels
        self.network = nn.Sequential(
            nn.Conv2d(channels, 8, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(8, 16, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 24, 3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4)),
            nn.Flatten(),
            nn.Linear(24 * 4 * 4, 32),
            nn.ReLU(),
            nn.Linear(32, len(CLASSES)),
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return self.network(inputs)


def _deterministic(seed: int) -> None:
    torch.set_num_threads(2)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)


def _logits(model: BubbleCNN, inputs: np.ndarray) -> np.ndarray:
    model.eval()
    with torch.inference_mode():
        return np.concatenate(
            [
                model(torch.from_numpy(inputs[start : start + 128, : model.channels])).numpy()
                for start in range(0, len(inputs), 128)
            ]
        )


def _metrics(logits: np.ndarray, rows: list[dict]) -> dict:
    matrix = np.zeros((len(CLASSES), len(CLASSES)), dtype=int)
    for actual, predicted in zip(rows, logits.argmax(axis=1), strict=True):
        matrix[CLASSES.index(actual["label"]), predicted] += 1
    return {
        "samples": len(rows),
        "confusion_actual_rows_predicted_columns": matrix.tolist(),
        "class_order": list(CLASSES),
        "argmax_agreement": float(matrix.trace() / matrix.sum()) if matrix.sum() else None,
        "calibrated": False,
        "independent_test": False,
    }


def train_model(
    datasets: list[Path],
    output: Path,
    *,
    epochs: int = 8,
    seed: int = 17,
    paired_reference: bool = False,
) -> dict:
    """Train only explicitly allowed train rows with verified geometry and group separation.

    Development labels are used once for descriptive metrics after the fixed run,
    never for gradients, early stopping, class weights or an automatic policy.
    """
    if output.exists() or not 1 <= epochs <= 1000:
        raise ValueError("Use a new output and 1–1000 epochs")
    rows, arrays, provenance = [], [], []
    for path in datasets:
        _, items, inputs = load_dataset(path)
        rows.extend(items)
        arrays.append(inputs)
        review = path.parent / "geometry-review.json"
        provenance.append(
            {
                "dataset_sha256": digest(path),
                "geometry_review_sha256": digest(review) if review.exists() else None,
            }
        )
    validate_groups(rows)
    eligible = [r["geometry_validated"] and not r["quality_issues"] for r in rows]
    train_indices = [i for i, r in enumerate(rows) if r["split"] == "train" and eligible[i]]
    if any(not r["training_allowed"] for r in rows if r["split"] == "train"):
        raise ValueError("Training permission missing on a train acquisition")
    if not train_indices:
        raise ValueError("No eligible train samples; do not relabel development data implicitly")
    counts = Counter(rows[i]["label"] for i in train_indices)
    if set(counts) != set(CLASSES):
        raise ValueError("All four visual classes need train examples")
    dev_indices = [i for i, r in enumerate(rows) if r["split"] == "development" and eligible[i]]
    _deterministic(seed)
    inputs = np.concatenate(arrays)
    channels = 2 if paired_reference else 1
    model = BubbleCNN(channels)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    weights = torch.tensor([len(train_indices) / (len(CLASSES) * counts[c]) for c in CLASSES])
    criterion = nn.CrossEntropyLoss(weight=weights)
    x = torch.from_numpy(inputs[train_indices, :channels])
    y = torch.tensor([CLASSES.index(rows[i]["label"]) for i in train_indices])
    generator = torch.Generator().manual_seed(seed)
    losses = []
    started = time.perf_counter()
    for _ in range(epochs):
        model.train()
        order = torch.randperm(len(x), generator=generator)
        for indices in order.split(32):
            optimizer.zero_grad()
            loss = criterion(model(x[indices]), y[indices])
            loss.backward()
            optimizer.step()
        model.eval()
        with torch.inference_mode():
            # Keep epoch measurement bounded as the corpus grows, just like training.
            total_loss, total_weight = 0.0, 0.0
            for start in range(0, len(x), 128):
                target = y[start : start + 128]
                weight = float(weights[target].sum())
                total_loss += float(criterion(model(x[start : start + 128]), target)) * weight
                total_weight += weight
            losses.append(total_loss / total_weight)
    elapsed = time.perf_counter() - started
    if not np.isfinite(losses).all():
        raise ValueError("Non-finite training loss")
    output.mkdir(parents=True)
    # Plain named numeric arrays, no pickle or remotely downloaded checkpoint.
    np.savez(
        output / "weights.npz", **{k: v.detach().numpy() for k, v in model.state_dict().items()}
    )
    train_rows = [rows[i] for i in train_indices]
    report = {
        "schema_version": 1,
        "architecture": ARCHITECTURE,
        "channels": channels,
        "preprocessing": PREPROCESSING,
        "classes": list(CLASSES),
        "weights_sha256": digest(output / "weights.npz"),
        "code_sha256": {
            n: digest(Path(__file__).with_name(n)) for n in ("ml_reader.py", "ml_data.py")
        },
        "lock_sha256": digest(Path(__file__).parents[2] / "uv.lock")
        if (Path(__file__).parents[2] / "uv.lock").exists()
        else None,
        "versions": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "numpy": np.__version__,
        },
        "config": {
            "epochs": epochs,
            "seed": seed,
            "batch_size": 32,
            "optimizer": "Adam",
            "lr": 0.001,
            "threads": 2,
            "device": "cpu",
            "augmentation": "none",
        },
        "datasets": provenance,
        "train": dataset_summary(train_rows),
        "train_identities": {
            k: sorted({r[k] for r in train_rows})
            for k in ("group_id", "physical_sheet_id", "acquisition_sha256")
        },
        "train_kinds": sorted({r["dataset_kind"] for r in train_rows}),
        "excluded_geometry_or_quality": len(rows) - sum(eligible),
        "train_loss": losses,
        "training_seconds": elapsed,
        "parameter_count": sum(p.numel() for p in model.parameters()),
        "train_metrics": _metrics(_logits(model, inputs[train_indices]), train_rows),
        "development_metrics": _metrics(
            _logits(model, inputs[dev_indices]), [rows[i] for i in dev_indices]
        )
        if dev_indices
        else None,
        "calibrated": False,
        "automatic_decisions_enabled": False,
        "independent_test": False,
    }
    write_json(output / "model.json", report)
    return report


def load_model(directory: Path) -> tuple[BubbleCNN, dict]:
    """Verify version/shape/hash and load numeric tensors only; inference remains CPU-only."""
    m = json.loads((directory / "model.json").read_text())
    if (
        m.get("schema_version") != 1
        or m.get("architecture") != ARCHITECTURE
        or m.get("preprocessing") != PREPROCESSING
        or m.get("classes") != list(CLASSES)
        or type(m.get("channels")) is not int
        or m["channels"] not in (1, 2)
    ):
        raise ValueError("Incompatible model architecture/preprocessing/classes")
    weights = directory / "weights.npz"
    if weights.stat().st_size > 10 * 1024 * 1024 or digest(weights) != m["weights_sha256"]:
        raise ValueError("Model weights checksum/size mismatch")
    model = BubbleCNN(m["channels"])
    expected = model.state_dict()
    with np.load(weights, allow_pickle=False) as state:
        if set(state.files) != set(expected):
            raise ValueError("Unexpected model tensors")
        tensors = {}
        for key, template in expected.items():
            value = state[key]
            if (
                value.shape != tuple(template.shape)
                or value.dtype != np.float32
                or not np.isfinite(value).all()
            ):
                raise ValueError("Invalid model tensor")
            tensors[key] = torch.from_numpy(value.copy())
    model.load_state_dict(tensors, strict=True)
    model.eval()
    return model, m


def predict_dataset(model_dir: Path, dataset_path: Path, output: Path) -> dict:
    """Diagnostic logits/softmax per case, always requiring review; never a public answer."""
    if output.exists():
        raise ValueError("Output must be a new directory")
    _deterministic(0)
    model, metadata = load_model(model_dir)
    _, rows, inputs = load_dataset(dataset_path)
    validate_groups(rows)
    start = time.perf_counter()
    logits = _logits(model, inputs)
    if not np.isfinite(logits).all():
        raise ValueError("Non-finite inference logits")
    elapsed = time.perf_counter() - start
    probabilities = torch.softmax(torch.from_numpy(logits), dim=1).numpy()
    observations = []
    for r, scores, probs in zip(rows, logits, probabilities, strict=True):
        reasons = ["uncalibrated_experimental_model", *r["quality_issues"]]
        if not r["geometry_validated"]:
            reasons.append("bubble_geometry_unconfirmed")
        if metadata["train_kinds"] == ["synthetic"] and r["dataset_kind"] == "real":
            reasons.append("synthetic_only_training")
        observations.append(
            {
                "sample_id": r["id"],
                "section": r["section"],
                "question": r["question"],
                "choice": r["choice"],
                "logits": scores.tolist(),
                "softmax_uncalibrated": probs.tolist(),
                "suggested_visual_class": CLASSES[int(probs.argmax())],
                "requires_review": True,
                "review_reasons": reasons,
            }
        )
    eligible = [
        i for i, r in enumerate(rows) if r["geometry_validated"] and not r["quality_issues"]
    ]
    overlap = any(
        r[k] in metadata["train_identities"][k] for r in rows for k in metadata["train_identities"]
    )
    report = {
        "schema_version": 1,
        "purpose": "offline_visual_observations_only",
        "model_sha256": digest(model_dir / "model.json"),
        "dataset_sha256": digest(dataset_path),
        "geometry_review_sha256": digest(dataset_path.parent / "geometry-review.json")
        if (dataset_path.parent / "geometry-review.json").exists()
        else None,
        "weights_sha256": metadata["weights_sha256"],
        "inference_code_sha256": {
            name: digest(Path(__file__).with_name(name)) for name in ("ml_data.py", "ml_reader.py")
        },
        "preprocessing": PREPROCESSING,
        "classes": list(CLASSES),
        "calibrated": False,
        "automatic_decisions": 0,
        "independent_test": False,
        "overlaps_training": overlap,
        "dataset": dataset_summary(rows),
        "inference_seconds": elapsed,
        "metrics_on_geometry_confirmed_only": _metrics(
            logits[eligible], [rows[i] for i in eligible]
        )
        if eligible
        else None,
        "observations": observations,
    }
    output.mkdir(parents=True)
    write_json(output / "predictions.json", report)
    return report
