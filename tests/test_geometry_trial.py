import json
from pathlib import Path

import numpy as np
import pytest

from psychomark.baseline import digest
from psychomark.config import Exam
from psychomark.geometry_trial import compare_geometry, geometry_observations, run_geometry_trial
from psychomark.images import save_image
from psychomark.regions import project_points


def manifest_for(sheet, source: Path, path: Path) -> dict:
    template = sheet["engine"].template
    manifest = {
        "schema_version": 1,
        "split": "development",
        "source_size": [template.width, template.height],
        "provenance": {"snapshot_template_sha256": digest(sheet["template_path"])},
        "images": {
            "source": {"sha256": digest(source)},
            "reference": {"sha256": template.reference_sha256},
        },
        "questions": [
            {
                "section": "1",
                "question": 1,
                "choices": 4,
                "annotation": {"geometry": "confirmed", "manual_bounds": [82, 306, 107, 425]},
            }
        ],
    }
    path.write_text(json.dumps(manifest))
    return manifest


def test_trial_composes_geometry_and_preserves_historical_engine(sheet, tmp_path):
    source = tmp_path / "source.png"
    save_image(source, sheet["filled"])
    manifest = tmp_path / "manifest.json"
    manifest_for(sheet, source, manifest)
    output = tmp_path / "trial"
    report = run_geometry_trial(sheet["template_path"], source, output, manifest)
    exam = Exam(
        template_id=sheet["engine"].template.template_id,
        sections={s.id: list(range(1, s.questions + 1)) for s in sheet["layout"].sections},
    )
    expected, _ = sheet["engine"].analyze(sheet["filled"], exam)
    assert json.loads((output / "historical-result.json").read_text()) == expected
    assert report["complete"] and report["corpus"]["confirmed_manual_rectangles"] == 1
    for data in report["variants"].values():
        assert data["global_comparison"]["all_choice_centers_inside"] == 1
        assert data["global_comparison"]["answer_accuracy"] is None
        H = np.array(data["registration"]["input_to_reference"])
        for entry in data["sections"].values():
            if entry["refinement"]["status"] == "rejected":
                continue
            assert entry["round_trip_error_px"] < 1e-6
            L = np.array(entry["refinement"]["reference_to_global"])
            assert np.allclose(entry["source_to_reference"], np.linalg.inv(L) @ H)
            assert np.allclose(entry["reference_to_source"], np.linalg.inv(H) @ L)
        for region in data["local_regions"]:
            inverse = np.array(data["sections"][region["section"]]["reference_to_source"])
            for choice in region["choices"]:
                assert np.allclose(
                    project_points([choice["reference_center"]], inverse)[0],
                    choice["source_center"],
                )
    assert report["variants"]["raw"]["local_regions"], "Exercise composition, not just rejection"
    assert all(digest(output / name) == value for name, value in report["artifact_sha256"].items())
    with pytest.raises(ValueError, match="new directory"):
        run_geometry_trial(sheet["template_path"], source, output)


def test_missing_registration_keeps_annotated_denominator(sheet, tmp_path):
    source = tmp_path / "empty.png"
    save_image(source, np.full_like(sheet["filled"], 255))
    manifest = tmp_path / "manifest.json"
    manifest_for(sheet, source, manifest)
    report = run_geometry_trial(sheet["template_path"], source, tmp_path / "trial", manifest)
    for data in report["variants"].values():
        assert data["registration"] is None
        assert data["global_regions"] == data["local_regions"] == []
        metrics = data["global_comparison"]
        assert metrics["human_rectangles"] == 1 and metrics["located"] == 0
        assert metrics["median_center_distance_source_px"] is None
        assert metrics["answer_accuracy"] is None


@pytest.mark.parametrize(
    "problem", ["source", "reference", "template", "split", "bounds", "duplicate"]
)
def test_incompatible_corpus_rejected_before_trial(sheet, tmp_path, problem):
    source = tmp_path / "source.png"
    save_image(source, sheet["filled"])
    path = tmp_path / "manifest.json"
    m = manifest_for(sheet, source, path)
    if problem in {"source", "reference"}:
        m["images"][problem]["sha256"] = "0" * 64
    elif problem == "template":
        m["provenance"]["snapshot_template_sha256"] = "0" * 64
    elif problem == "split":
        m["split"] = "test"
    elif problem == "bounds":
        m["questions"][0]["annotation"]["manual_bounds"] = [0, 0, 999999, 10]
    else:
        m["questions"].append(m["questions"][0])
    path.write_text(json.dumps(m))
    with pytest.raises(ValueError):
        geometry_observations(path, sheet["template_path"], source, sheet["filled"].shape[:2])


def test_question_rectangles_are_not_claimed_as_case_accuracy():
    boxes = {("1", 1): [0, 0, 20, 50], ("1", 2): [30, 0, 50, 50]}
    regions = [
        {
            "section": "1",
            "question": 1,
            "choices": [{"source_center": [10, 10]}, {"source_center": [21, 40]}],
        }
    ]
    metric = compare_geometry(regions, boxes)
    assert metric["human_rectangles"] == 2 and metric["located"] == 1
    assert metric["all_choice_centers_inside"] == 0 and metric["answer_accuracy"] is None
