# État actuel

Mis à jour le 2026-10-08 (Asia/Jerusalem). Cette page décrit le dépôt, pas un état garanti de déploiement.

## Disponible

- Moteur OMR Python/OpenCV sur modèles configurés, CLI et interface FastAPI en français.
- Examen à sections/questions choisies, corrigé, import, vérification humaine, note et exports.
- SQLite et instantanés par copie ; Codespaces avec actualisation de développement.
- Documentation organisée, règles de contribution, ADR, mémoire et commandes de qualité.
- CI GitHub configurée pour Python 3.11/3.12 et parcours Chromium ; exécution distante
  à vérifier dans GitHub Actions après publication.
- Six [skills de design](../development/design-tools.md) installés pour Codex dans le dépôt,
  avec sources et empreintes. Recherche UI/UX Pro Max et moteur Impeccable vérifiés.
- Be UI accessible via `scripts/beui.py`, qui lit la configuration du projet :
  connexion MCP, outils, recherche, détail d'un composant et commande d'installation vérifiés.
- Inspirations originales archivées ; Renance (`HEg1RfvbwAIpjJa`) préféré explicitement.
  [Direction visuelle](../product/visual-direction.md) rédigée, traduction proposée.

## Limites et décisions en attente

- Validation sur données synthétiques uniquement ; aucune précision réelle annoncée.
- Les feuilles NITE/Adar montrées dans la conversation ne sont pas des modèles calibrés.
- Pas de SaaS public : ni comptes, ni isolation par entreprise, ni migrations SQL.
- Framework et bibliothèque UI restent à confirmer ; Renance est la référence visuelle
  principale. Palette/polices proposées et place des fresques/marbre restent à préciser.
  Ne pas interpréter le prototype comme une décision de design system.
- Pas encore de typage complet, de lint frontend ou d'outil de mesure de corpus réel.
- La configuration globale Codex reste en lecture seule. Be UI fonctionne via le client
  du projet, sans cette écriture. L'ajout natif à une conversation déjà ouverte reste
  sous le contrôle du client hôte ; une commande CLI avec `-c` ne modifie pas ce chat.

## Prochaine reprise

Reprendre la lecture des inspirations avec l'utilisateur, préciser la place de l'univers
artistique, puis préparer une maquette de landing et un écran de correction représentatif.
Les skills installés ne choisissent pas la stack ou la direction graphique à sa place.
Vérifier la publication et la synchronisation uniquement si elles sont nécessaires au
prochain essai de l'utilisateur. Ensuite préparer une feuille vierge et quelques
copies réelles autorisées pour un premier modèle pilote et la vérité de référence.
Suivre les [priorités](../product/roadmap.md) et le [workflow](../development/workflow.md).

Dernière session : [inspirations et direction visuelle](sessions/2026-10-08-02-visual-references.md).
Les preuves de validation et les contrôles non exécutés y sont consignés.
