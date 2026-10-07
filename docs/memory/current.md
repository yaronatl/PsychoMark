# État actuel

Mis à jour le 2026-10-07. Cette page décrit le dépôt, pas un état garanti de déploiement.

## Disponible

- Moteur OMR Python/OpenCV sur modèles configurés, CLI et interface FastAPI en français.
- Examen à sections/questions choisies, corrigé, import, vérification humaine, note et exports.
- SQLite et instantanés par copie ; Codespaces avec actualisation de développement.
- Documentation organisée, règles de contribution, ADR, mémoire et commandes de qualité.
- CI GitHub configurée pour Python 3.11/3.12 et parcours Chromium ; exécution distante
  à vérifier dans GitHub Actions après publication.

## Limites et décisions en attente

- Validation sur données synthétiques uniquement ; aucune précision réelle annoncée.
- Les feuilles NITE/Adar montrées dans la conversation ne sont pas des modèles calibrés.
- Pas de SaaS public : ni comptes, ni isolation par entreprise, ni migrations SQL.
- Le framework frontend, la bibliothèque UI et la direction visuelle restent à choisir
  par l'utilisateur. Ne pas interpréter le prototype comme une décision de design system.
- Pas encore de typage complet, de lint frontend ou d'outil de mesure de corpus réel.

## Prochaine reprise

Récupérer les changements dans le Codespace, réinstaller les dépendances gelées et
consulter les vérifications GitHub. Ensuite préparer une feuille vierge et quelques
copies réelles autorisées pour un premier modèle pilote et la vérité de référence.
Suivre les [priorités](../product/roadmap.md) et le [workflow](../development/workflow.md).

Dernière session : [organisation et qualité](sessions/2026-10-07-01-project-foundation.md).
Les preuves de validation et les contrôles non exécutés y sont consignés.
