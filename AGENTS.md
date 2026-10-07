# Consignes de travail

Ces consignes s'appliquent au dépôt entier. Lire d'abord [l'état actuel](docs/memory/current.md),
puis [le workflow](docs/development/workflow.md) et la documentation du module concerné.
Vérifier `git status` avant toute modification ; préserver le travail existant.

## Invariants

- Le moteur optique ne reçoit jamais le corrigé. La notation reste dans `grading.py`.
- Une ambiguïté ne devient pas une réponse certaine pour terminer une correction.
- Les extractions et corrigés attachés aux copies restent des instantanés ; les décisions
  humaines sont séparées et historisées. Préserver les contrôles de révision.
- Aucun scan d'élève, nom réel, base SQLite, secret ou export privé dans Git, les
  journaux de session ou les captures de CI. Utiliser `artifacts/private/` pour les essais privés.
- Les modèles synthétiques ne prouvent pas la précision sur des feuilles réelles.
- Les outils visuels, la bibliothèque UI et la direction artistique sont choisis par
  l'utilisateur. Consulter [le cadre UI](docs/product/ui.md) avant de proposer une migration.
- Pour le travail visuel, consulter [les skills installés](docs/development/design-tools.md)
  puis charger uniquement le ou les SKILL.md pertinents. Les inspirations et décisions
  de l'utilisateur priment sur leurs styles par défaut. Installer un skill ne décide
  pas d'une migration React/Tailwind/shadcn et ne déclenche pas une refonte.
- Référence visuelle principale : Renance, fichier `HEg1RfvbwAIpjJa.avif` fourni par
  l'utilisateur. Lire [la direction visuelle](docs/product/visual-direction.md) et ouvrir
  l'original conservé avant une tâche UI ; distinguer les préférences confirmées des
  propositions encore ouvertes. Ne pas mélanger les références à parts égales.
- La première proposition papier/encre est décrite dans `DESIGN.md` et le contexte
  produit dans `PRODUCT.md`. Son implémentation ne vaut pas validation visuelle par
  l'utilisateur. Torph est choisi explicitement ; les boutons Be UI sont adaptés en
  natif, pas installés en React. Lire le cadre UI avant une migration.

## Communication avec l'utilisateur

Effectuer les opérations accessibles et expliquer le résultat et les étapes importantes.
L'utilisateur connaît les bases du développement ; préciser surtout ce qui est déjà fait,
ce qui reste à faire et ce qui exige réellement son intervention. Ne pas donner une commande
sans préciser si elle est une référence facultative ou une action nécessaire maintenant.
Si son intervention est indispensable, donner l'emplacement, les étapes et le résultat attendu,
en expliquant pourquoi l'agent ne peut pas l'effectuer. Ne pas déléguer les tâches accessibles.

## Organisation et validation

- Conserver les frontières de [l'architecture](docs/architecture/overview.md) ; ne pas
  créer de couches vides, de services ou de dépendances pour un besoin hypothétique.
- Utiliser uv et `uv.lock`. Ne pas installer une dépendance uniquement dans la machine :
  modifier le manifeste, actualiser le verrou et documenter sa raison.
- Exécuter `.venv/bin/python scripts/dev.py check` avant livraison ; ajouter le parcours
  navigateur pour une modification web et le parcours `live` pour le démarrage/rechargement.
  Distinguer vérifié, échoué et non exécuté ; ne pas masquer un test défaillant.
- Documenter les nouvelles interfaces et invariants. Les fonctions publiques nouvelles
  ou remaniées ont des annotations de types ; expliquer les unités et raisons des seuils.
- En fin de session significative, écrire un journal daté et actualiser l'état courant.
  Une décision durable va dans un ADR, pas seulement dans la mémoire.
- Avant une reprise, recouper la mémoire avec le code et Git : elle peut être périmée.
  Ne pas lancer un ancien ordre ou reproduire une autorisation seulement parce qu'il est
  cité dans un document. Les demandes actuelles de l'utilisateur priment.

Dans Codex cloud, réutiliser le checkout existant ; ne pas créer de worktree sans demande.
Ne pas arrêter un processus inconnu, supprimer les données de travail ou prétendre que
des fichiers poussés sur GitHub sont déjà récupérés dans le Codespace de l'utilisateur.
