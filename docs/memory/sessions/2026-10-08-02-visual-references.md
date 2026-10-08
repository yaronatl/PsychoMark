# Session 2026-10-08-02 — Inspirations et direction visuelle

- Date utilisateur : 2026-10-08, Asia/Jerusalem (7 octobre UTC au début).
- Départ : `chore/design-skills`, commit `6479b43`.
- Branche : `docs/visual-direction`.
- Demande : examiner les inspirations, avec préférence explicite pour `HEg1RfvbwAIpjJa`.

## Réalisé

Téléchargement et inspection des deux AVIF ; ils correspondent à Renance (préférence
principale) et Taskk. Vidéo Energy inspectée via son premier cadre et cinq images
échantillonnées sur 40,53 secondes. Les captures Incredible et Athera intégrées au
message sont aussi prises en compte, sans les confondre avec le fichier préféré.

Les trois originaux téléchargeables sont conservés dans `docs/product/references/`,
avec tailles et SHA-256. Les conversions de consultation restent dans `artifacts/`.
Application du skill frontend-design à l'analyse, sans implémentation de nouvelle UI.

Ajout de [la direction visuelle](../../product/visual-direction.md), hiérarchie des
références, rôles landing/dashboard, palette/polices proposées, invariants de fidélité.
AGENTS.md et les points d'entrée documentaires renvoient à cette direction pour la reprise.

## Confirmé / proposé / à préciser

- Confirmé : Renance est la référence préférée. La direction appartient à l'utilisateur.
- Proposé : crème/noir, grands titres serif, interface calme, aperçu réel des corrections.
- Question adressée : reprendre aussi fresques/marbre, ou surtout sobriété et typographie ?
  Pas de réponse reçue au moment de rédaction ; ne pas transformer cette absence en accord.
- À préciser : framework/bibliothèque frontend, images et polices définitives.
- Aucun changement applicatif, installation de composants ou promesse commerciale ajoutée.

## Vérification

Originaux comparés par SHA-256 et dimensions inspectées. La vidéo a été échantillonnée,
pas analysée image par image ; aucune courbe d'animation exacte n'est inférée.
`.venv/bin/python scripts/dev.py check` : Ruff et format réussis, 31 documents vérifiés
sans lien local cassé, 56 tests réussis en 28,49 s (avertissement Starlette/httpx existant).
Les trois fichiers archivés sont identiques octet par octet aux pièces téléchargées.

## Reprise

Présenter l'interprétation des références, intégrer la précision éventuelle de l'utilisateur,
puis passer à une première maquette ciblée. Conserver les références originales et le
statut de chaque proposition plutôt que de choisir une direction différente à la session suivante.
