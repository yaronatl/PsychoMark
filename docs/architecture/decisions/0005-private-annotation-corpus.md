# 0005 — Corpus privé et observations humaines séparées

État : adopté pour S02. Date : 2026-10-08.

## Contexte

Les refus actuels doivent pouvoir être examinés même sans alignement exploitable.
Les exemples de développement ne doivent ni modifier les corrections existantes,
ni être présentés comme un jeu indépendant de mesure de précision.

## Décision

Ajouter `corpus.py` et un espace HTML/JS natif **Annotations**. Une acquisition garde
une source décodée, une référence et un modèle figés, les régions S01 disponibles,
les empreintes et les annotations humaines. La lecture automatique est rejouée sans
corrigé ; elle sert à proposer des zones, jamais à préremplir les observations.

Stocker les acquisitions dans le dossier privé de données. Un remplacement atomique
du JSON de métadonnées sous le verrou OMR conserve observations et historique ensemble.
Chaque modification exige la révision courante. Les annotations ne changent aucune
extraction ni aucun corrigé dans SQLite ; aucune migration SQL n’est nécessaire.

Identifier séparément acquisition, papier physique et groupe. Un papier conserve
son groupe ; un groupe conserve son usage. Refuser les duplications de pixels décodés.
Les diagnostics déjà examinés restent en développement. L’autorisation d’apprentissage
est fausse par défaut. Ces règles limitent les fuites, sans établir l’indépendance
statistique du corpus ni détecter toutes les photos proches.

Sans alignement, conserver les labels sur source et permettre un rectangle manuel
par question. Ne pas fabriquer d’homographie ou de coordonnées validées par case.
Les exports réunissent les observations et leur provenance ; ils excluent les
prédictions et le corrigé. La géométrie automatique historique reste distincte du
cadre manuel courant dans le manifeste.

## Conséquences et réexamen

Le stockage reprend le modèle de fichiers du MVP, sans nouvelle dépendance. SQLite
pour le corpus et un stockage distant seraient prématurés pour cet atelier mono-worker.
Une recherche volumineuse, plusieurs workers, les transferts d’usage, la suppression
et la gestion d’accès devront amener une évolution explicite et testée.

Les images décodées sont conservées sans métadonnées de fichier d’origine ; leur
contenu peut néanmoins contenir des informations personnelles. Les ZIP restent
privés, comme les sauvegardes. Une annotation complète n’est pas un modèle entraîné.

Voir [le guide](../../guides/annotations.md) et [l’API](../api.md).
