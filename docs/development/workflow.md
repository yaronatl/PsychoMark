# Workflow de développement

[Documentation](../README.md) · [Contribution](../../CONTRIBUTING.md)

## 1. Reprendre et cadrer

Lire l'état actuel, vérifier Git et les dernières modifications. Définir le problème,
le comportement attendu et les critères observables d'acceptation. Pour un changement
important, inscrire la priorité dans la feuille de route. Pour un choix durable de
stack, contrat ou stockage, créer un [ADR](../templates/decision.md).

## 2. Préparer un changement limité

Pour les contributions suivantes, travailler sur une branche `feat/...`, `fix/...`
ou `docs/...`, puis ouvrir une PR vers `main`. Un changement d'organisation ne justifie
pas une réécriture du moteur. Ne pas mélanger calibration de seuils, nouveau frontend
et changement de base de données dans une même livraison.

Les dépôts de travail de Codex et Codespaces sont distincts. Après publication sur
GitHub, utiliser `git pull --ff-only` dans le Codespace si l'arbre de travail le permet.
Ne pas écraser des modifications locales pour forcer la synchronisation.

## 3. Implémenter avec les bonnes frontières

- Garder le moteur indépendant de HTTP, de SQLite et du corrigé.
- Réutiliser les schémas et services existants ; éviter les règles métier dupliquées en JS.
- Documenter les unités, conventions de coordonnées, cas limites et motifs de rejet.
- Annoter les signatures Python nouvelles ou remaniées et limiter les responsabilités
  par fonction. Le typage complet historique reste une amélioration future.
- Écrire des tests de comportement pour une règle métier ou un défaut significatif.
  Ne pas ajouter des tests qui ne font que répéter l'implémentation ou vérifier de la prose.
- Utiliser des paramètres SQL et des révisions attendues ; prévoir une migration testée
  avant de changer le schéma persistant.
- Pour une dépendance : justifier son usage, changer `pyproject.toml`, exécuter `uv lock`,
  vérifier le diff du verrou puis réinstaller avec `--frozen`.

## 4. Vérifier

```bash
.venv/bin/python scripts/dev.py format
.venv/bin/python scripts/dev.py check
```

`format` trie les imports et formate Python ; `check` vérifie Ruff, le format Python,
les liens locaux de documentation puis pytest. Il ne modifie pas le code.
Le JavaScript/CSS n'a pas encore de formateur/linter dédié ; vérifier le navigateur
et garder le style cohérent en attendant les choix d'outillage frontend.

| Changement | Vérification complémentaire |
|---|---|
| Interface ou routes web | `scripts/dev.py browser` avec le Python du venv |
| Démarrage ou actualisation | `scripts/dev.py live` avec le Python du venv |
| Moteur ou seuils | Tests ciblés et comparaison sur corpus de référence disponible |
| Stockage | Persistance, concurrence, compatibilité/migration et restauration |
| Dépendances | Installation gelée et vérifications des usages concernés |

Les commandes détaillées et limites sont dans [validation](testing.md).

## 5. Documenter et livrer

Actualiser la documentation de référence, écrire la session et condenser l'état courant.
Relire le diff : fichiers privés exclus, pas de changement involontaire, tests pertinents
réellement exécutés. La PR décrit le résultat, les preuves et les limites avec
[le modèle du dépôt](../../.github/pull_request_template.md).

Un changement est terminé quand ses critères sont vérifiés, sa documentation concorde
avec le code et la reprise est possible. Les vérifications non exécutées sont nommées.
Une revue humaine est recommandée avant fusion ; en travail solo, relire le diff avec
ces mêmes critères. La protection de branche et les contrôles obligatoires GitHub ne
sont **pas configurés par ce document**. La CI ne publie ni ne déploie l'application.

Pour revenir sur du code publié, préférer un commit de revert. Ne pas supposer qu'un
revert restaure aussi une base transformée : appliquer la procédure de migration ou
de restauration explicitement testée pour le changement concerné.
