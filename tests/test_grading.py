import pytest

from psychomark.grading import Assessment, Review, grade


def assessment(sheet, key=None):
    return Assessment(
        name="Examen",
        template_id=sheet["layout"].template_id,
        sections={"1": [1, 2, 3, 4]},
        answer_key={"1": key or {"1": 2, "2": 3, "3": 1, "4": 2}},
    )


def test_grade_separates_known_errors_blanks_and_unresolved_answers(sheet):
    result = grade(
        assessment(sheet),
        {
            "answers": [
                {"section": "1", "question": 1, "status": "single", "answer": 2},
                {"section": "1", "question": 2, "status": "single", "answer": 1},
                {"section": "1", "question": 3, "status": "blank", "answer": None},
                {"section": "1", "question": 4, "status": "multiple", "answer": None},
            ]
        },
        {},
    )
    assert result["status"] == "provisional"
    assert (result["correct"], result["incorrect"], result["blank"], result["pending"]) == (
        1,
        1,
        1,
        1,
    )
    assert result["points"] is None and result["out_of_20"] is None and result["percentage"] is None
    assert (result["min_points"], result["max_possible_points"], result["total"]) == (1, 2, 4)


def test_missing_extraction_is_pending_not_automatically_wrong(sheet):
    result = grade(assessment(sheet), {"answers": []}, {})
    assert result["pending"] == 4
    assert result["out_of_20"] is None


def test_human_decisions_finalize_score_without_modifying_extraction(sheet):
    original = {
        "answers": [
            {"section": "1", "question": q, "status": "uncertain", "answer": None}
            for q in range(1, 5)
        ]
    }
    reviews = {
        "1:1": {"decision": "choice", "answer": 2},
        "1:2": {"decision": "choice", "answer": 4},
        "1:3": {"decision": "multiple", "answer": None},
        "1:4": {"decision": "blank", "answer": None},
    }
    result = grade(assessment(sheet), original, reviews)
    assert result["status"] == "final"
    assert (result["points"], result["percentage"], result["out_of_20"]) == (1, 25, 5)
    assert result["incorrect"] == 2 and result["blank"] == 1
    assert all(a["answer"] is None for a in original["answers"])


@pytest.mark.parametrize(
    "key", [{"1": 2}, {"1": 2, "2": 3, "3": 1, "4": 5}, {"01": 2, "2": 3, "3": 1, "4": 2}]
)
def test_incomplete_or_out_of_range_keys_are_rejected(sheet, key):
    with pytest.raises(ValueError):
        assessment(sheet, key).validate_for(sheet["layout"])


def test_review_validation_covers_selected_question_and_choice_limit(sheet):
    exam = assessment(sheet)
    with pytest.raises(ValueError):
        Review(
            expected_revision=1, section="1", question=30, decision="choice", answer=1
        ).validate_for(exam, sheet["layout"])
    with pytest.raises(ValueError):
        Review(
            expected_revision=1, section="1", question=1, decision="choice", answer=5
        ).validate_for(exam, sheet["layout"])
    with pytest.raises(ValueError):
        Review(expected_revision=1, section="1", question=1, decision="blank", answer=2)
