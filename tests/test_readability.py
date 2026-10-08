"""Presentation must distinguish failed alignment from local reading controls."""

from psychomark.readability import with_readability


def test_aligned_partial_refusal_groups_questions_without_changing_readings():
    result = {
        "status": "needs_review",
        "diagnostics": {"registration": {"method": "orb_ransac"}},
        "answers": [
            {
                "section": "1",
                "question": 1,
                "status": "unreadable",
                "reason": "frame_mismatch,blurred_section",
            },
            {"section": "1", "question": 2, "status": "unreadable", "reason": "blurred_section"},
            {"section": "2", "question": 1, "status": "unreadable", "reason": "blurred_section"},
            {"section": "3", "question": 1, "status": "single", "answer": 2},
        ],
    }
    presented = with_readability(result)
    report = presented["readability"]
    assert report["alignment"] == "succeeded"
    issues = {i["code"]: i for i in report["issues"]}
    assert issues["blurred_section"]["sections"] == ["1", "2"]
    assert issues["blurred_section"]["question_count"] == 3
    assert issues["frame_mismatch"]["question_count"] == 1
    assert "PDF" in issues["blurred_section"]["advice"]
    assert presented["answers"] == result["answers"]
    assert "readability" not in result


def test_unknown_alignment_failure_preserves_technical_reason_without_inventing_blur():
    result = {"diagnostics": {"error": "Future registration failure"}, "answers": []}
    report = with_readability(result)["readability"]
    assert report["alignment"] == "failed"
    assert report["issues"][0]["detail"] == "Future registration failure"
    assert report["issues"][0]["code"] == "registration_failed"


def test_multiple_marks_are_not_a_readability_failure():
    result = {
        "diagnostics": {"registration": {}},
        "answers": [
            {"section": "1", "question": 1, "status": "multiple", "reason": "multiple_dark_marks"}
        ],
    }
    report = with_readability(result)["readability"]
    assert report["alignment"] == "succeeded"
    assert report["issues"] == []
