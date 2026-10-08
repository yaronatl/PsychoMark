# Session — Plan de renforcement OMR et expérimentation ML

Date : 2026-10-08 (Asia/Jerusalem). Branche : `docs/hybrid-omr-plan`.
Commit de départ : `82332b9`.

## Demande et résultat

L’utilisateur demande un plan complet avant implémentation, avec sessions et agents
Codex. Le [plan](../../product/hybrid-omr-plan.md) décrit dix lots, leurs dépendances,
les livrables, la collecte/annotation, l’évaluation et l’activation progressive.
[ADR 0004](../../architecture/decisions/0004-hybrid-omr-experiment.md) conserve la
proposition d’architecture. Stack, priorités et mémoire renvoient à ce plan unique.

Deux revues spécialisées en lecture seule ont examiné les frontières d’architecture
et le protocole d’évaluation. Elles recommandent des contrats avant parallélisme,
des groupes par feuille physique, une mesure conjointe erreur/couverture et une
phase d’observation sans effet sur les notes. L’intégrateur reste responsable des
dépendances, de Git et des fichiers partagés. Aucun agent n’a annoté de données réelles.

La mémoire corrige l’hypothèse antérieure de variante imprimée : l’utilisateur confirme
la même feuille, photographiée. Le diagnostic connu permet de commencer ; sa référence
humaine est encore à établir et il ne constitue pas un test indépendant.

## Portée et reprise

Livraison documentaire uniquement. Aucun algorithme, seuil, dépendance, poids ML,
schéma de stockage ou écran modifié. Le modèle spécialisé reste à entraîner et à
évaluer. Le plan ne promet ni taux de précision ni délai de livraison artificiel.

Prochain lot : S01, rejouer et mesurer le moteur historique, fixer les contrats,
préparer les régions pour annotation humaine. Puis S02 et S03 peuvent être répartis
entre agents avec fichiers distincts. Le diagnostic privé doit être retrouvé dans
l’environnement de reprise ; son chemin local ne garantit pas sa disponibilité ailleurs.

## Validation et publication

`.venv/bin/python scripts/dev.py check` : Ruff et format réussis, 44 documents
vérifiés sans lien local cassé, 66 tests réussis. Un avertissement existant signale
la dépréciation de l’usage httpx dans Starlette TestClient. `git diff --check` réussi.
Aucun parcours navigateur ni entraînement/évaluation ML exécuté : cette livraison
ne change que la documentation. Ces tests ne prouvent pas la précision sur les photos.

La livraison vise la branche `docs/hybrid-omr-plan`. Une publication Git ne signifie
ni fusion dans `main`, ni synchronisation du Codespace de l’utilisateur.
