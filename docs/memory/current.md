# État actuel

Mis à jour le 2026-10-07. Cette page décrit le dépôt, pas un état garanti de déploiement.

## Disponible

- Moteur OMR Python/OpenCV sur modèles configurés, CLI et interface FastAPI en français.
- Examen à sections/questions choisies, corrigé, import, vérification humaine, note et exports.
- SQLite et instantanés par copie ; Codespaces avec actualisation de développement.
- Documentation organisée, règles de contribution, ADR, mémoire et commandes de qualité.
- CI GitHub configurée pour Python 3.11/3.12 et parcours Chromium ; exécution distante
  à vérifier dans GitHub Actions après publication.
- Six [skills de design](../development/design-tools.md) installés pour Codex dans le dépôt,
  avec sources et empreintes. Recherche UI/UX Pro Max et moteur Impeccable vérifiés.

## Limites et décisions en attente

- Validation sur données synthétiques uniquement ; aucune précision réelle annoncée.
- Les feuilles NITE/Adar montrées dans la conversation ne sont pas des modèles calibrés.
- Pas de SaaS public : ni comptes, ni isolation par entreprise, ni migrations SQL.
- Le framework frontend, la bibliothèque UI et la direction visuelle restent à choisir
  par l'utilisateur. Ne pas interpréter le prototype comme une décision de design system.
- Pas encore de typage complet, de lint frontend ou d'outil de mesure de corpus réel.
- Be UI : configurations Codex/VS Code préparées, connexion refusée par le proxy réseau.
  Domaine ajouté au brouillon réseau, non activé dans cette session ; outils MCP non testés.
  La commande d'ajout globale échoue aussi car la configuration Codex est en lecture seule.

## Prochaine reprise

Attendre les inspirations visuelles de l'utilisateur avant de lancer la refonte. Les
skills installés ne choisissent pas la stack ou la direction graphique à sa place.
Vérifier la publication et la synchronisation uniquement si elles sont nécessaires au
prochain essai de l'utilisateur. Ensuite préparer une feuille vierge et quelques
copies réelles autorisées pour un premier modèle pilote et la vérité de référence.
Suivre les [priorités](../product/roadmap.md) et le [workflow](../development/workflow.md).

Dernière session : [skills de design et Be UI](sessions/2026-10-07-02-design-skills.md).
Les preuves de validation et les contrôles non exécutés y sont consignés.
