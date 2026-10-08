"""Explain existing OMR refusals without changing optical decisions or thresholds."""

from __future__ import annotations

REGISTRATION_REASONS = {
    "Too few recognizable landmarks": (
        "Trop peu de repères reconnaissables dans la photo",
        "Reprenez la page entière, bien éclairée et nette, avec ses textes et ses marges.",
    ),
    "Insufficient matches to the selected template": (
        "La photo ne retrouve pas assez de repères de la feuille vierge",
        "Vérifiez la version de la feuille et gardez toute la page dans la photo. "
        "Une différence d’impression ou de résolution peut aussi gêner le rapprochement.",
    ),
    "Alignment landmarks are insufficiently consistent or distributed": (
        "Les repères retrouvés ne suffisent pas à aligner toute la page",
        "Photographiez la feuille entière, à plat, en conservant les marges. "
        "Des grilles très répétitives peuvent également tromper le repérage.",
    ),
    "Alignment error is too large for bubble reading": (
        "L’alignement manque de précision pour lire les petites cases",
        "Reprenez la photo plus près et aussi de face que possible, avec une feuille bien à plat.",
    ),
    "Implausible or mirrored page geometry": (
        "La transformation trouvée déforme trop la page ou inverse l’image",
        "Vérifiez que la photo n’est pas en miroir et que le modèle correspond à la feuille. "
        "Reprenez une photo de face si la perspective est importante.",
    ),
}

READING_REASONS = {
    "frame_mismatch": (
        "Le contour des grilles ne correspond pas assez à la référence",
        "Vérifiez que les coins du modèle sont sur le cadre imprimé exact. "
        "Comparez aussi la mise en page et l’impression ; un alignement imparfait peut provoquer ce refus.",
    ),
    "blurred_section": (
        "Le contour des grilles paraît moins net que sur la référence",
        "Ce contrôle compare la photo à la feuille vierge. Un PDF très net et une feuille "
        "imprimée puis photographiée peuvent présenter un grand écart. Essayez une photo nette "
        "ou un scan pour comparer ; le diagnostic permet aussi d’examiner si le contrôle est trop strict.",
    ),
    "blurred_bubbles": (
        "Le contour de certaines cases paraît moins net que sur la référence",
        "Vérifiez la mise au point et la taille des ellipses du modèle. Une différence "
        "entre le PDF et son impression peut aussi déclencher ce contrôle.",
    ),
    "insufficient_resolution": (
        "Les cases sont trop petites dans la photo d’origine",
        "Envoyez le fichier original en pleine résolution ou rapprochez l’appareil. "
        "Agrandir après coup une petite image ne restitue pas les détails.",
    ),
    "cropped_section": (
        "Une partie de la grille tombe hors de la photo après alignement",
        "Gardez toute la feuille dans le cadre, avec une petite marge. "
        "Si elle est déjà entière, vérifiez l’alignement et les limites de la grille.",
    ),
    "cropped_bubble": (
        "Une partie des cases tombe hors de la photo après alignement",
        "Vérifiez le cadrage de la page et la position des cases dans le modèle.",
    ),
}


def readability_report(extraction: dict) -> dict:
    """Report measured refusal conditions; advice is a hypothesis, not a diagnosis of the camera."""
    diagnostics = extraction.get("diagnostics", {})
    answers = extraction.get("answers", [])
    if "registration" not in diagnostics:
        raw = diagnostics.get("error", "")
        title, advice = REGISTRATION_REASONS.get(
            raw,
            (
                "L’alignement de la photo sur la feuille vierge n’a pas abouti",
                "Comparez le modèle et la page photographiée. Le diagnostic contient "
                "les fichiers nécessaires pour examiner ce blocage.",
            ),
        )
        return {
            "alignment": "failed" if raw or answers else "unknown",
            "summary": "La photo n’a pas pu être alignée de façon fiable. Les cases ne sont pas lues.",
            "issues": [
                {
                    "code": "registration_failed",
                    "title": title,
                    "advice": advice,
                    "sections": [],
                    "question_count": len(answers),
                    "detail": raw,
                }
            ],
        }
    groups: dict[str, list[dict]] = {}
    for answer in answers:
        if answer.get("status") != "unreadable":
            continue
        for code in set(answer.get("reason", "unknown").split(",")):
            groups.setdefault(code, []).append(answer)
    issues = []
    for code, affected in sorted(groups.items()):
        title, advice = READING_REASONS.get(
            code,
            (
                "Un contrôle de lecture a refusé cette zone",
                "Consultez le détail technique du diagnostic.",
            ),
        )
        issues.append(
            {
                "code": code,
                "title": title,
                "advice": advice,
                "sections": sorted({a["section"] for a in affected}),
                "question_count": len(affected),
                "detail": code,
            }
        )
    return {
        "alignment": "succeeded",
        "summary": (
            "La photo a été alignée, mais des contrôles de lisibilité empêchent la lecture de certaines zones."
            if issues
            else "La photo a été alignée et les contrôles de lisibilité ont été acceptés. "
            "Cela ne garantit pas l’exactitude de chaque réponse."
        ),
        "issues": issues,
    }


def with_readability(extraction: dict) -> dict:
    """Decorate an HTTP result while leaving the stored optical extraction intact."""
    return {**extraction, "readability": readability_report(extraction)}
