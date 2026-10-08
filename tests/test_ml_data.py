import copy
import json

import numpy as np
import pytest

from psychomark.baseline import digest
from psychomark.calibration import calibrate
from psychomark.config import write_json
from psychomark.images import save_image
from psychomark.ml_data import (
    letterbox,
    load_dataset,
    prepare_dataset,
    synthetic_dataset,
    validate_groups,
)


@pytest.fixture
def toy_data(tmp_path):
    root = tmp_path / "toy"
    synthetic_dataset(root, groups=3)
    return root / "dataset.json"


def rewrite_dataset(path, change):
    data = json.loads(path.read_text())
    change(data)
    write_json(path, data)
    review_path = path.parent / "geometry-review.json"
    review = json.loads(review_path.read_text())
    review["dataset_sha256"] = digest(path)
    write_json(review_path, review)


def test_letterbox_preserves_aspect_and_does_not_stretch():
    image = np.zeros((8, 16), np.uint8)
    output = letterbox(image)
    assert output.shape == (32, 32)
    assert (output[:8] == 255).all() and (output[24:] == 255).all()
    assert (output[8:24] == 0).all()
    with pytest.raises(ValueError):
        letterbox(np.zeros((0, 4), np.uint8))


@pytest.mark.parametrize("identity", ["group_id", "physical_sheet_id", "acquisition_sha256"])
def test_groups_cannot_leak_even_if_other_ids_are_changed(toy_data, identity):
    _, rows, _ = load_dataset(toy_data)
    validate_groups(rows)
    changed = copy.deepcopy(rows)
    changed[-1][identity] = changed[0][identity]
    with pytest.raises(ValueError, match="leakage"):
        validate_groups(changed)
    with pytest.raises(ValueError, match="Duplicate"):
        validate_groups(rows + [rows[0]])


def test_real_regions_need_explicit_hash_bound_review(toy_data):
    rewrite_dataset(toy_data, lambda d: d.update(kind="real"))
    _, rows, _ = load_dataset(toy_data)
    assert not any(r["geometry_validated"] for r in rows)
    review_path = toy_data.parent / "geometry-review.json"
    review = json.loads(review_path.read_text())
    review["decisions"][0].update(status="confirmed", reviewer="synthetic-reviewer")
    write_json(review_path, review)
    _, rows, _ = load_dataset(toy_data)
    assert sum(r["geometry_validated"] for r in rows) == 1
    # A new crop configuration invalidates the old review, even if IDs remain equal.
    m = json.loads(toy_data.read_text())
    m["samples"][0]["reference_bounds"] = [0, 0, 10, 10]
    write_json(toy_data, m)
    with pytest.raises(ValueError, match="Stale"):
        load_dataset(toy_data)


def test_assets_are_checked_and_cannot_escape_directory(toy_data):
    m, _, _ = load_dataset(toy_data)
    asset = toy_data.parent / m["samples"][0]["copy"]["path"]
    asset.write_bytes(b"different")
    with pytest.raises(ValueError, match="checksum"):
        load_dataset(toy_data)
    rewrite_dataset(toy_data, lambda d: d["samples"][0]["copy"].update(path="../../outside.png"))
    with pytest.raises(ValueError, match="directory"):
        load_dataset(toy_data)


@pytest.mark.parametrize("split", ["calibration", "test"])
def test_reserved_splits_rejected(toy_data, split):
    rewrite_dataset(toy_data, lambda d: d["samples"][0].update(split=split))
    with pytest.raises(ValueError, match="reserved"):
        load_dataset(toy_data)


def test_quality_metadata_cannot_silently_hide_low_resolution(toy_data):
    rewrite_dataset(toy_data, lambda d: d["samples"][0].update(source_diameters_px=[2, 3]))
    _, rows, _ = load_dataset(toy_data)
    assert rows[0]["quality_issues"] == ["low_source_resolution"]


def test_preparation_preserves_labels_but_does_not_validate_bubble_geometry(tmp_path, sheet):
    root = tmp_path / "export"
    root.mkdir()
    template_path = root / "template.json"
    template = calibrate(sheet["blank"], sheet["layout"], template_path)
    save_image(root / "source.png", sheet["filled"])
    s = template.sections[0]
    marks = ["empty"] * (s.choices - 1) + ["marked"]
    m = {
        "schema_version": 1,
        "split": "development",
        "training_allowed": True,
        "group_id": "fixture",
        "physical_sheet_id": "fixture",
        "source_size": [template.width, template.height],
        "provenance": {"snapshot_template_sha256": digest(template_path)},
        "images": {
            "source": {"sha256": digest(root / "source.png")},
            "reference": {"sha256": template.reference_sha256},
        },
        "questions": [
            {
                "section": s.id,
                "question": 1,
                "choices": s.choices,
                "annotation": {
                    "geometry": "confirmed",
                    "marks": marks,
                    "choices": [s.choices],
                    "status": "single",
                },
            }
        ],
    }
    manifest = root / "manifest.json"
    write_json(manifest, m)
    output = tmp_path / "prepared"
    prepare_dataset(manifest, output)
    data, rows, pixels = load_dataset(output / "dataset.json")
    assert [r["label"] for r in rows] == marks
    assert [r["choice"] for r in rows] == list(range(1, s.choices + 1))
    assert pixels.shape == (s.choices, 2, 32, 32)
    assert not any(r["geometry_validated"] for r in rows)
    m["questions"][0]["annotation"].update(marks=["empty"] * s.choices, choices=[], status="blank")
    write_json(manifest, m)
    other = tmp_path / "relabeled"
    second = prepare_dataset(manifest, other)
    assert data["provenance"]["registration"] == second["provenance"]["registration"]
    np.testing.assert_array_equal(pixels, load_dataset(other / "dataset.json")[2])
    m["images"]["source"]["sha256"] = "incorrect"
    write_json(manifest, m)
    with pytest.raises(ValueError, match="fingerprint"):
        prepare_dataset(manifest, tmp_path / "bad")
