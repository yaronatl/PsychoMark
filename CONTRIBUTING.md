# Contribuer à PsychoMark

1. Lire [l'état actuel](docs/memory/current.md) et [l'architecture](docs/architecture/overview.md).
2. Installer les [prérequis verrouillés](docs/development/stack.md), ou ouvrir un Codespace.
3. Suivre le [workflow](docs/development/workflow.md) pour cadrer, coder, vérifier et livrer.
4. Mettre à jour la documentation concernée et la [mémoire](docs/memory/README.md).

Les règles s'appliquent aux humains comme aux assistants. La documentation est en
français ; les identifiants Python/JavaScript sont en anglais. Préférer des changements
limités, relisibles et testables. Une refonte technique ou un nouveau service nécessite
une décision motivée ; une correction ordinaire n'a pas besoin d'un document supplémentaire.

```bash
uv sync --frozen --extra dev
.venv/bin/python scripts/dev.py check
```

Le fichier [AGENTS.md](AGENTS.md) rassemble les invariants et les consignes de reprise.
Le contrôle automatique ne remplace ni la revue du code ni la validation sur copies réelles.
