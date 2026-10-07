# Contrat HTTP du MVP

[Documentation](../README.md) · [Implémentation](../../src/psychomark/web.py)

Les schémas d'entrée sont définis par Pydantic dans `config.py`, `grading.py` et
`web.py`. FastAPI expose la description générée sur `/openapi.json` du serveur lancé.
La page Swagger `/docs` par défaut dépend de ressources externes que la politique
CSP actuelle bloque ; utiliser le JSON OpenAPI, pas cette page comme outil validé.
Cette page explique les invariants sans recopier tous les schémas.
Plusieurs sorties sont encore des dictionnaires sans modèle de réponse OpenAPI détaillé.

| Route | Usage |
|---|---|
| `GET /api/health` | Santé et présence du mode développement |
| `GET /api/templates` | Modèles disponibles au démarrage |
| `GET /api/exams`, `POST /api/exams` | Liste et création d'examen corrigé |
| `GET /api/exams/{id}`, `PUT /api/exams/{id}` | Lecture et modification avec `expected_revision` |
| `POST /api/exams/{id}/copies` | Un fichier multipart `file`, plusieurs pages possibles |
| `GET /api/copies/{id}` | Extraction, notation et historique |
| `PATCH /api/copies/{id}/reviews` | Décision manuelle avec `expected_revision` |
| `GET /api/copies/{id}/image/{view}` | `original`, `aligned`, `annotated` |
| `GET /api/copies/{id}/crop/{section}/{question}` | Zone utile à la vérification |
| `GET /api/copies/{id}/export/{format}` | `csv` ou `json` |
| `POST /api/demo` | Création de données synthétiques |
| `GET /api/dev/revision` | Empreinte des sources, seulement en développement |

Les questions et choix commencent à **1**. Une réponse optique `blank` est différente
d'une zone `unreadable`. Une décision `automatic` retire la décision manuelle courante
sans supprimer l'événement historique. Une révision périmée produit **409** : relire
la ressource et présenter le conflit, sans écraser silencieusement une modification.

Les validations d'entrée produisent notamment **422**, les identifiants absents **404**.
Un import peut rendre des copies traitées et des erreurs de pages ; un succès HTTP ne
signifie donc pas que toutes les pages sont lisibles. Les statuts métier doivent être lus.

Une rupture de contrat doit expliciter les consommateurs touchés, la compatibilité
des données et les tests. Il n'y a pas de garantie d'API publique versionnée à ce stade.
Ne jamais exposer ce serveur comme API publique authentifiée : l'authentification
applicative n'est pas implémentée.
