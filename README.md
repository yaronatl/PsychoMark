# PsychoMark

Correction de QCM à partir de scans ou de photos : un moteur optique Python/OpenCV,
une interface web en français, un corrigé configurable et une vérification des cas ambigus.
La lecture des cases reste indépendante des bonnes réponses.

**MVP testé sur données synthétiques. Les feuilles réelles NITE et Adar ne sont pas
encore calibrées ni validées. Aucun taux de précision réel n'est établi.**
L'application actuelle sert un opérateur ; elle n'est pas encore un SaaS multi-entreprises.

## Essayer dans le cloud

Dans GitHub, ouvrir **Code → Codespaces → Create codespace on main**.
L'installation et le démarrage sont automatiques. Ouvrir le port **8000** dans
l'onglet **Ports**, garder sa visibilité **Private**, puis cliquer sur
**Essayer la démonstration**.

[Guide Codespaces et synchronisation des changements](docs/guides/codespaces.md)
· [Utiliser l'interface et corriger un examen](docs/guides/web.md)
· [Ajouter une feuille sans scripts](docs/guides/sheets.md)

## Développer

Python 3.12 est la version de développement ; Python 3.11 reste supporté.
Installer [uv](https://docs.astral.sh/uv/) 0.12.19, puis, depuis la racine du dépôt :

```bash
uv sync --frozen --extra dev
.venv/bin/python scripts/dev.py check
.venv/bin/python scripts/dev.py serve
```

SQLite est fourni avec Python ; la base est créée au démarrage. Aucun serveur de
base de données, compte cloud ou secret applicatif n'est requis pour ce MVP.
Les données locales et les scans sont sous `artifacts/`, exclus de Git.

## Se repérer

| Besoin | Document de référence |
|---|---|
| Vue d'ensemble de la documentation | [Index](docs/README.md) |
| Reprendre le travail | [État actuel](docs/memory/current.md), puis [contribution](CONTRIBUTING.md) |
| Comprendre les modules et les données | [Architecture](docs/architecture/overview.md) |
| Savoir quels outils utiliser | [Stack et prérequis](docs/development/stack.md) |
| Développer, tester et livrer | [Workflow](docs/development/workflow.md) |
| Calibrer une feuille et lire les résultats | [Guide du moteur](docs/guides/cli.md) |
| Comprendre les décisions techniques | [Registre des décisions](docs/architecture/decisions/README.md) |
| Orienter les prochaines étapes et l'interface | [Feuille de route](docs/product/roadmap.md), [cadre UI](docs/product/ui.md) |
| Consignes aux assistants de développement | [AGENTS.md](AGENTS.md) |

Les versions exactes des bibliothèques sont dans [uv.lock](uv.lock).
Les procédures, décisions et journaux sont rangés dans `docs/` ; le README reste
un point d'entrée. Une mémoire de session conserve les faits et les vérifications,
pas les conversations complètes ni les données d'élèves.
