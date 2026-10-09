import json
import subprocess
import sys

import numpy as np
import pytest

torch = pytest.importorskip("torch", reason="optional ml extra; dedicated CI job installs it")

from psychomark.baseline import digest  # noqa: E402
from psychomark.config import write_json  # noqa: E402
from psychomark.ml_data import synthetic_dataset  # noqa: E402
from psychomark.ml_reader import load_model, predict_dataset, train_model  # noqa: E402


@pytest.fixture(scope="module")
def experiment(tmp_path_factory):
    root = tmp_path_factory.mktemp("ml")
    synthetic_dataset(root / "data", groups=6)
    data = root / "data" / "dataset.json"
    report = train_model([data], root / "model", epochs=16)
    return root, data, report


def rewrite(path, mutate):
    m = json.loads(path.read_text())
    mutate(m)
    write_json(path, m)
    review_path = path.parent / "geometry-review.json"
    review = json.loads(review_path.read_text())
    review["dataset_sha256"] = digest(path)
    write_json(review_path, review)


def test_training_learns_and_is_reproducible_after_export(experiment):
    root, data, report = experiment
    assert report["train_loss"][-1] < report["train_loss"][0] * 0.8
    again = train_model([data], root / "repeat", epochs=16)
    assert report["train_loss"] == again["train_loss"]
    model, _ = load_model(root / "model")
    repeated, _ = load_model(root / "repeat")
    for key, value in model.state_dict().items():
        assert torch.equal(value, repeated.state_dict()[key])
    predicted = predict_dataset(root / "model", data, root / "inference")
    assert len(predicted["observations"]) == 192
    assert all(r["requires_review"] for r in predicted["observations"])
    assert predicted["automatic_decisions"] == 0
    assert predicted["overlaps_training"] and not predicted["independent_test"]
    assert sum(report["development_metrics"]["confusion_actual_rows_predicted_columns"][0]) == 8


def test_training_refuses_missing_permission_unvalidated_and_development(tmp_path):
    synthetic_dataset(tmp_path / "data", groups=2)
    path = tmp_path / "data" / "dataset.json"
    rewrite(path, lambda m: [r.update(training_allowed=False) for r in m["samples"]])
    with pytest.raises(ValueError, match="permission"):
        train_model([path], tmp_path / "denied")
    rewrite(
        path,
        lambda m: (m.update(kind="real"), [r.update(training_allowed=True) for r in m["samples"]]),
    )
    with pytest.raises(ValueError, match="eligible"):
        train_model([path], tmp_path / "unvalidated")
    rewrite(
        path,
        lambda m: (
            m.update(kind="synthetic"),
            [r.update(split="development") for r in m["samples"]],
        ),
    )
    with pytest.raises(ValueError, match="eligible"):
        train_model([path], tmp_path / "development")


def test_prediction_does_not_depend_on_human_labels_and_preserves_review(tmp_path, experiment):
    root, _, _ = experiment
    synthetic_dataset(tmp_path / "data", groups=2)
    path = tmp_path / "data" / "dataset.json"
    rewrite(path, lambda m: m.update(kind="real"))
    first = predict_dataset(root / "model", path, tmp_path / "first")
    rewrite(path, lambda m: [r.update(label="empty") for r in m["samples"]])
    second = predict_dataset(root / "model", path, tmp_path / "second")
    assert first["observations"] == second["observations"]
    assert second["metrics_on_geometry_confirmed_only"] is None
    assert all("bubble_geometry_unconfirmed" in r["review_reasons"] for r in second["observations"])
    assert all("synthetic_only_training" in r["review_reasons"] for r in second["observations"])


def test_development_labels_never_change_weights(tmp_path, experiment):
    root, _, _ = experiment
    synthetic_dataset(tmp_path / "data", groups=6)
    path = tmp_path / "data" / "dataset.json"
    rewrite(
        path,
        lambda m: [
            r.update(label="unreadable") for r in m["samples"] if r["split"] == "development"
        ],
    )
    train_model([path], tmp_path / "model", epochs=16)
    original, _ = load_model(root / "model")
    changed, _ = load_model(tmp_path / "model")
    for key, value in original.state_dict().items():
        assert torch.equal(value, changed.state_dict()[key])


def test_model_tampering_and_incompatible_preprocessing_fail(tmp_path, experiment):
    root, _, _ = experiment
    for name in ("model.json", "weights.npz"):
        (tmp_path / name).write_bytes((root / "model" / name).read_bytes())
    m = json.loads((tmp_path / "model.json").read_text())
    m["preprocessing"] = "unknown"
    write_json(tmp_path / "model.json", m)
    with pytest.raises(ValueError, match="Incompatible"):
        load_model(tmp_path)
    (tmp_path / "model.json").write_bytes((root / "model" / "model.json").read_bytes())
    np.savez(tmp_path / "weights.npz", invalid=np.array([1.0]))
    with pytest.raises(ValueError, match="checksum"):
        load_model(tmp_path)
    m = json.loads((tmp_path / "model.json").read_text())
    m["weights_sha256"] = digest(tmp_path / "weights.npz")
    write_json(tmp_path / "model.json", m)
    with pytest.raises(ValueError, match="tensors"):
        load_model(tmp_path)


def test_paired_reference_model_runs_local_cpu(tmp_path):
    synthetic_dataset(tmp_path / "data", groups=2)
    path = tmp_path / "data" / "dataset.json"
    report = train_model([path], tmp_path / "model", epochs=1, paired_reference=True)
    model, _ = load_model(tmp_path / "model")
    assert report["channels"] == 2
    assert next(model.parameters()).device.type == "cpu"
    result = predict_dataset(tmp_path / "model", path, tmp_path / "predictions")
    assert np.isclose(sum(result["observations"][0]["softmax_uncalibrated"]), 1.0)


def test_regular_engine_and_preparation_do_not_import_torch():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import psychomark.engine; import psychomark.ml_trial; assert 'torch' not in sys.modules",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
