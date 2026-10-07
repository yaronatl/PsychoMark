# ADR 0001 — Base du MVP et frontières du système

Date : 2026-10-07. État : adopté pour le MVP actuel.

## Contexte

Le produit doit lire des grilles configurées, corriger des examens courts ou complets
et présenter les ambiguïtés à un opérateur. Il n'existe pas encore de corpus réel
annoté permettant de valider la précision. Une interface provisoire fonctionne.

## Décision

Conserver un monolithe Python avec moteur OpenCV, API FastAPI, validation Pydantic,
stockage SQLite/fichiers et interface native provisoire. Verrouiller les dépendances
avec uv. Séparer extraction optique, corrigé, décisions humaines et notation.

Utiliser les modèles de feuilles explicitement calibrés. Garder la possibilité d'un
modèle d'IA spécialisé ultérieur, évalué sur les mêmes données et sans accès au corrigé.
Les outils visuels et la bibliothèque UI appartiennent au choix de l'utilisateur.

## Options et conséquences

Un service visuel généraliste ne fournit pas aujourd'hui la preuve de fiabilité
nécessaire pour remplacer le moteur. Une architecture distribuée ajouterait des
services sans besoin de charge mesuré. Un SaaS complet et un frontend framework
anticiperaient des exigences encore ouvertes.

Le choix actuel permet un démarrage sans serveur de base externe et des tests isolés.
Il ne fournit pas de migrations SQL, de comptes utilisateurs ou d'isolation entre
entreprises. Le typage complet et l'organisation du frontend restent à améliorer.

## Quand réexaminer

Réexaminer le moteur après mesure des erreurs sur corpus réel ; le stockage et les
workers après définition du pilote et de ses volumes ; le frontend après les choix
visuels de l'utilisateur. Chaque remplacement important aura sa propre décision.

## Références

[Architecture](../overview.md), [stack](../../development/stack.md),
[protocole de validation](../../development/testing.md), [UI](../../product/ui.md).
