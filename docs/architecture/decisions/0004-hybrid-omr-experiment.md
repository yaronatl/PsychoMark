# ADR 0004 — Expérimenter un lecteur OMR hybride

Date : 2026-10-08. État : **proposé** ; orientation expérimentale soutenue par
l’utilisateur, architecture détaillée et activation encore à valider par les mesures.

## Contexte

Le moteur classique sait calibrer et aligner des feuilles, mais le premier diagnostic
photographique réel reste refusé ou incertain. Une réussite synthétique ne démontre
pas la fiabilité terrain. La même feuille peut présenter des différences de rendu
après impression, photographie et compression.

## Options et proposition

- Renforcer uniquement le classique : explicable et peu coûteux, mais les règles
  peuvent rester fragiles devant la diversité des traces.
- Confier la page entière à un modèle généraliste : contexte visuel large, mais
  association exacte question/choix, reproductibilité et abstention restent à démontrer.
- Expérimenter un lecteur hybride local : Python conserve la géométrie ; un petit
  modèle spécialisé interprète les marques, comparé au lecteur classique amélioré.

Retenir la troisième option comme programme d’expérimentation, décrit dans le
[plan détaillé](../../product/hybrid-omr-plan.md). Elle ne préjuge pas que la combinaison
des lecteurs sera meilleure que chacun séparément. Le corrigé demeure exclusivement
dans la notation. Les ambiguïtés et les défauts géométriques autorisent l’abstention.

## Conséquences et vérification

Définir les contrats de régions et observations avant de paralléliser les travaux.
Constituer des annotations humaines privées, séparer les données par feuille physique
et évaluer les erreurs automatiques avec la couverture et le temps de revue.
Versionner prétraitement, poids, politique de décision et provenance des extractions.
Préserver les anciens modèles de feuille et les instantanés des copies.

Le candidat fonctionne d’abord en observation, sans effet sur les notes. L’activation
sur un périmètre limité exige une évaluation indépendante et un retour arrière testé.
PyTorch est proposé pour l’entraînement ; ONNX reste une option selon les mesures.
Aucune dépendance ML ni migration de stockage n’est introduite par cet ADR.

## Réexamen

Revoir cette proposition si le modèle n’améliore pas le compromis erreur/revue,
si les données ne permettent pas de l’évaluer, ou si ses coûts dépassent le bénéfice.
L’absence de preuve conduit à conserver le moteur courant et la vérification humaine.
