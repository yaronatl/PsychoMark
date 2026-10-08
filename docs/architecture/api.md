# Contrat HTTP du MVP

[Documentation](../README.md) · [Implémentation](../../src/psychomark/web.py)

Les schémas d'entrée sont définis par Pydantic dans `config.py`, `grading.py` et
`web.py`, `sheets.py` et `corpus.py`. FastAPI expose la description générée sur `/openapi.json` du serveur lancé.
La page Swagger `/docs` par défaut dépend de ressources externes que la politique
CSP actuelle bloque ; utiliser le JSON OpenAPI, pas cette page comme outil validé.
Cette page explique les invariants sans recopier tous les schémas.
Plusieurs sorties sont encore des dictionnaires sans modèle de réponse OpenAPI détaillé.

| Route | Usage |
|---|---|
| `GET /api/health` | Santé et présence du mode développement |
| `GET /api/templates` | Modèles chargés au démarrage ou enregistrés depuis l’assistant |
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

## Assistant de feuilles

| Route | Usage |
|---|---|
| `GET /api/sheets`, `POST /api/sheets` | Liste des brouillons/modèles ; import multipart `file` d’une feuille vierge |
| `GET /api/sheets/{id}` | Nom, dimensions, grilles, révision et état enregistré |
| `PUT /api/sheets/{id}/calibration` | `expected_revision`, `name`, `sections` : valider et sauvegarder le brouillon |
| `POST /api/sheets/{id}/test?revision=N` | Fichier multipart `file`, une seule page ; extraction optique, sans note |
| `GET /api/sheets/{id}/test` | Dernier essai associé à la calibration actuelle |
| `POST /api/sheets/{id}/publish` | `expected_revision`, `checked_overlay: true` : figer et rendre utilisable |
| `GET /api/sheets/{id}/image/{kind}` | `blank`, `preview`, `test` (annotée), `original` (copie essayée) |

Les coordonnées sont des pixels de l’image décodée, origine en haut à gauche.
La calibration utilise les mêmes `Section`/`Layout` que la CLI. Un brouillon ne fait
pas partie de `/api/templates`. Chaque calibration incrémente la révision et retire
l’essai courant ; une erreur conserve la calibration précédente. L’enregistrement
incrémente la révision et interdit les modifications de géométrie. Un essai conserve
la révision de géométrie et remplace le dernier essai affiché, sous le verrou OMR.

Les imports de modèles et les essais refusent les fichiers multipages. Leurs limites
de taille sont celles du moteur. Les fichiers privés ne sont accessibles que via les
identifiants et types d’images prévus ; aucun chemin du client n’est utilisé comme
chemin de stockage. La sérialisation des écritures suppose un serveur à un worker.

### Diagnostic d’un essai de feuille

Les extractions servies par `POST /api/sheets/{id}/test` et
`GET /api/sheets/{id}/test` incluent désormais `readability` : état d’alignement,
résumé et liste des contrôles refusés avec leur code, explication, pistes de
vérification et zones concernées. Cette présentation est calculée à la lecture
par `readability.py` ; les résultats optiques enregistrés restent inchangés et
les anciens essais bénéficient de la même présentation. Les ambiguïtés de marques
ne sont pas assimilées à un défaut de lisibilité.

`GET /api/sheets/{id}/diagnostic` télécharge un ZIP de reproduction de l’essai
courant : modèle, référence, aperçu des zones, copie décodée, annotation et
résultat brut. Le pointeur de calibration/essai est lu sous le verrou partagé,
puis seuls les fichiers immuables correspondants sont archivés. Le ZIP passe par
un fichier temporaire fermé après transmission ; aucun cache supplémentaire durable.
L’absence d’essai, notamment après recalibration, renvoie 404. Le paramètre
optionnel `expected_test` refuse par 409 un essai différent de celui affiché
par le navigateur. Cet export contient
les images privées de cet essai et reste soumis aux mêmes limites d’accès que
l’application locale, sans authentification applicative ajoutée.

## Corpus d’annotation S02

| Route | Usage |
|---|---|
| `GET /api/corpus` | Acquisitions avec progression, observations et historique |
| `POST /api/corpus` | Multipart `file`, `physical_sheet_id`, `group_id` optionnel, `split`, `training_allowed`, `template_id` pour image/PDF |
| `GET /api/corpus/export` | Manifeste JSON de toutes les acquisitions, sans images |
| `GET /api/corpus/{id}` | Détail pour annotation, sans prédictions ni corrigé |
| `PATCH /api/corpus/{id}/annotations` | Observation humaine avec révision attendue |
| `GET /api/corpus/{id}/image/{view}` | Source décodée ou référence : `source`, `reference` |
| `GET /api/corpus/{id}/crop/{section}/{question}?view=copy` | Extrait manuel prioritaire, sinon automatique ; `view=reference` pour le vierge |
| `GET /api/corpus/{id}/export` | ZIP privé autonome : images, labels, provenance, régions et masques disponibles |

`split` accepte `development` (défaut), `train`, `calibration`, `test`.
`training_allowed` vaut `false` par défaut. Le ZIP de diagnostic est borné à 150 Mio
décompressés, valide les chemins, le modèle, l’empreinte de référence et la sélection.
Il impose `development` et ignore les prédictions importées. Une image/PDF sélectionne
toutes les questions du modèle. L’image est décodée et les pixels identiques sont
refusés par **409**, indépendamment du conteneur de fichier. Papier, groupe et usage
sont cohérents entre acquisitions ; leurs métadonnées sont figées à l’import.

Le PATCH exige `expected_revision`, `section`, `question`, `reviewer`, `status`,
`choices`, `marks`, `geometry` ; `manual_bounds` et `notes` sont optionnels.
Les marques sont `empty`, `marked`, `ambiguous`, `unreadable` pour chaque choix.
`choices` énumère exactement les indices marqués à partir de 1 ; le statut dérivé
donne priorité à `unreadable`, puis `uncertain`, puis `multiple`/`single`/`blank`.
Les décisions incohérentes sont refusées, pas corrigées silencieusement.

`geometry` accepte `confirmed`, `source_only`, `incorrect`. Un cadre confirmé exige
un extrait disponible ou `manual_bounds: [x0,y0,x1,y1]` entier, inclus dans la source
décodée, bornes de droite/bas exclusives. Un cadre manuel ne transforme pas les
coordonnées automatiques de `regions.json` et ne certifie pas les positions des cases.
Les coordonnées automatiques et homographies sont absentes après échec d’alignement.
L’original et la référence restent accessibles. Chaque sauvegarde incrémente la révision
et conserve avant/après dans l’historique ; une révision périmée renvoie **409**.

Les manifestes version 1 incluent les empreintes, le code moteur, les observations,
les chemins d’assets et les indicateurs de préparation. `eligible_for_training` exige
`train`, l’autorisation et toutes les questions annotées avec position confirmée.
`ready_for_evaluation` décrit seulement cette complétude géométrique ;
`independent_evaluation_established` et `case_coordinates_validated` restent `false`.
Les alias de relecture ne sont pas des identités authentifiées. Aucun entraînement,
aucun changement de note, aucun arbitrage entre annotateurs n’est déclenché.
