# Stack et prérequis

[Documentation](../README.md) · [Manifeste](../../pyproject.toml) · [Verrou](../../uv.lock)

## Stack installée et utilisée

| Besoin | Choix actuel | Installation ou configuration |
|---|---|---|
| Runtime | Python 3.12, compatibilité déclarée dès 3.11 | `.python-version` et conteneur Codespaces |
| Dépendances | uv 0.12.19 | Verrou unique `uv.lock` ; installation `--frozen` |
| Vision | OpenCV headless, NumPy | Dépendances Python, sans GPU |
| Fichiers | Pillow, pypdfium2 | Images, orientation EXIF et rendu PDF |
| Validation | Pydantic 2 | Schémas et invariants côté serveur |
| HTTP | FastAPI, Uvicorn, python-multipart | API et interface servies ensemble |
| Persistance | SQLite de Python + fichiers locaux | Base créée au démarrage sous `artifacts/web/` |
| Interface provisoire | HTML, CSS, modules JavaScript natifs + Torph | Assets locaux ; aucune requête CDN |
| Dépendances navigateur | npm, Node 22 pour le développement | `package-lock.json`, `npm ci --ignore-scripts`, `npm run build` |
| Qualité Python | Ruff, pytest, httpx | Extra `dev` |
| Parcours navigateur | Playwright + Chromium | Extra `browser`, installation du navigateur séparée |
| Prototype ML hors ligne | PyTorch CPU | Extra optionnel `ml`, poids privés ; [S06](specialized-reader.md) |
| Développement cloud | GitHub Codespaces | `.devcontainer/`, port 8000 privé |
| Intégration continue | GitHub Actions | Workflow `Checks`, Python 3.11 et 3.12 |

Les versions exactes des paquets sont dans le verrou, pas dupliquées dans ce tableau.
Les assets Torph générés sont conservés dans Git : le serveur Python peut les servir
sans Node au runtime. Node est nécessaire pour installer/mettre à jour les dépendances
frontend et vérifier leur reproductibilité. Voir [les outils visuels](design-tools.md).
Le conteneur utilise une image Microsoft Python étiquetée, pas une image figée par digest.
La CI est configurée dans le dépôt ; sa présence ne prouve pas une exécution réussie sur GitHub.

## Installer et vérifier

Depuis la racine, sur une machine avec Python et uv :

```bash
uv sync --frozen --extra dev
.venv/bin/python scripts/dev.py check
.venv/bin/python scripts/dev.py serve
```

Codespaces installe automatiquement l'extra `dev` et démarre le serveur. Il ne lance
pas les tests ni n'installe le navigateur à chaque ouverture. Pour les parcours web :

```bash
uv sync --frozen --extra dev --extra browser
.venv/bin/python -m playwright install chromium
.venv/bin/python scripts/dev.py browser
```

Sur Linux minimal, Playwright peut nécessiter `install --with-deps chromium`, avec
les droits d'installation système. Les scripts réutilisent Chromium système s'il existe.
Une nouvelle commande `uv sync` sans `--extra browser` peut retirer cet extra.

Les commandes documentées ciblent Linux/Codespaces. Aucun fichier `.env` n'est requis.
`--data-dir`, `--template`, `--host` et `--port` configurent le serveur. En rechargement,
`PSYCHOMARK_WEB_CONFIG` est produit par le lanceur : ne pas le maintenir manuellement.
Codespaces fournit ses propres variables d'origine ; ne pas y substituer un domaine arbitraire.

## Choix futurs, non installés

Le [prototype S06](specialized-reader.md) utilise maintenant PyTorch CPU dans l’extra
`ml` (`uv sync --frozen --extra dev --extra ml`). Les premiers poids sont entraînés
sur des exemples synthétiques et ne sont pas installés dans l’application. La version
CPU Linux/Windows vient d’un index explicite ; aucun paquet CUDA n’est requis.
ONNX Runtime reste une option à mesurer, sans GPU ni service distant obligatoire.

PostgreSQL, stockage objet, files de tâches, authentification, paiement et hébergement
de production nécessiteront une décision lorsque leurs besoins seront cadrés.
SQLite couvre le MVP actuel ; cela ne décide pas du stockage du futur SaaS.
Il n'y a ni ORM, ni Redis, ni Docker Compose, ni SDK d'IA à utiliser implicitement.
Les ajouter exige un besoin concret, une procédure de démarrage et des tests.

Le framework frontend, la bibliothèque de composants et le design system restent
**à choisir par l'utilisateur**. Voir [le cadre UI](../product/ui.md).
