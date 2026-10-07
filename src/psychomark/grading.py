"""Marking is deliberately separate from optical recognition."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .config import ConfigModel, Exam, Layout


class Assessment(Exam):
    answer_key: dict[str, dict[str, Annotated[int, Field(strict=True, ge=1)]]]

    def validate_for(self, template: Layout) -> None:
        super().validate_for(template)
        if set(self.answer_key) != set(self.sections):
            raise ValueError("Le corrigé doit couvrir exactement les sections sélectionnées.")
        limits = {s.id: s.choices for s in template.sections}
        for sid, questions in self.sections.items():
            if set(self.answer_key[sid]) != {str(q) for q in questions}:
                raise ValueError(
                    f"Le corrigé de la section {sid} doit couvrir chaque question sélectionnée."
                )
            if any(choice > limits[sid] for choice in self.answer_key[sid].values()):
                raise ValueError(f"Choix hors limites dans la section {sid}.")

    def selection(self) -> Exam:
        return Exam.model_validate(self.model_dump(exclude={"answer_key"}))


class Review(ConfigModel):
    expected_revision: Annotated[int, Field(strict=True, ge=1)]
    section: str
    question: Annotated[int, Field(strict=True, ge=1)]
    decision: Literal["choice", "blank", "multiple", "automatic"]
    answer: Annotated[int, Field(strict=True, ge=1)] | None = None

    @model_validator(mode="after")
    def choice_value(self):
        if (self.decision == "choice") != (self.answer is not None):
            raise ValueError(
                "Une réponse est nécessaire uniquement pour une décision de type choice."
            )
        return self

    def validate_for(self, assessment: Assessment, layout: Layout):
        if self.question not in assessment.sections.get(self.section, []):
            raise ValueError("Question absente de cet examen.")
        limit = next(s.choices for s in layout.sections if s.id == self.section)
        if self.answer is not None and self.answer > limit:
            raise ValueError("Choix hors limites.")


def grade(assessment: Assessment, extraction: dict, reviews: dict) -> dict:
    detected = {(a["section"], a["question"]): a for a in extraction.get("answers", [])}
    rows = []
    for sid, questions in assessment.sections.items():
        for q in questions:
            original = detected.get(
                (sid, q), {"status": "unreadable", "answer": None, "reason": "missing_result"}
            )
            review = reviews.get(f"{sid}:{q}")
            answer = review["answer"] if review else original["answer"]
            status = review["decision"] if review else original["status"]
            expected = assessment.answer_key[sid][str(q)]
            if status in {"single", "choice"} and answer is not None:
                verdict = "correct" if answer == expected else "incorrect"
            elif status == "blank":
                verdict = "blank"
            elif status == "multiple" and review:
                verdict = "incorrect"
            else:
                verdict = "pending"
            rows.append(
                {
                    "section": sid,
                    "question": q,
                    "expected": expected,
                    "detected_status": original["status"],
                    "detected_answer": original["answer"],
                    "answer": answer if verdict != "pending" else None,
                    "verdict": verdict,
                    "reviewed": review is not None,
                    "decision": status,
                    "reason": original.get("reason"),
                    "candidates": original.get("candidates", []),
                }
            )
    total = len(rows)
    counts = {
        state: sum(row["verdict"] == state for row in rows)
        for state in ["correct", "incorrect", "blank", "pending"]
    }
    correct, pending = counts["correct"], counts["pending"]
    return {
        "status": "provisional" if pending else "final",
        "total": total,
        **counts,
        "points": None if pending else correct,
        "max_points": total,
        "percentage": None if pending else round(100 * correct / total, 2),
        "out_of_20": None if pending else round(20 * correct / total, 2),
        "min_points": correct,
        "max_possible_points": correct + pending,
        "rows": rows,
    }
