# 0003 — Bibliothèque de modèles calibrés depuis le navigateur

État : adopté pour le MVP. Date : 2026-10-08.

## Contexte

L’utilisateur demande de créer de nouveaux modèles sans écrire de JSON ni exécuter
les scripts. Le moteur dispose déjà d’une calibration sur référence vierge et d’une
lecture indépendante du corrigé. Les copies existantes doivent conserver leur sens.

## Décision

Ajouter un assistant HTML/JS natif qui recueille cinq repères par grille régulière.
La géométrie reste validée par les schémas Python et `calibrate`, sans heuristique
optique supplémentaire ni changement des seuils. L’essai appelle le même moteur que
les imports de copies, mais ne crée ni examen ni note.

Stocker chaque brouillon sous un identifiant aléatoire dans le dossier privé de
l’application. Les calibrations sont des ensembles de fichiers immuables ; un
remplacement atomique des métadonnées active une version réussie. La révision attendue
protège les sauvegardes concurrentes. Une erreur garde la dernière version utilisable.

L’enregistrement final rend le modèle disponible et fige sa géométrie. L’application
recharge les modèles enregistrés au démarrage. Aucun schéma SQLite existant ne change.
Les brouillons ne sont pas proposés dans les examens. Les essais n’affirment pas
la précision et la confirmation de l’aperçu n’est pas une certification.

## Conséquences et réexamen

Le stockage de fichiers correspond déjà aux références du moteur et évite d’introduire
une migration SQL pour ce besoin. Il faut sauvegarder le dossier complet. Les anciennes
calibrations et essais sont conservés ; un nettoyage et une politique de rétention
restent à prévoir. Les repères non vérifiés vivent dans la page et ne sont pas autosauvés.

Le verrou de processus et le registre en mémoire supposent un seul worker, comme
le MVP existant. Une exploitation multi-worker ou SaaS nécessitera un stockage et
une synchronisation adaptés. Les feuilles sans cadre ou à géométrie irrégulière
nécessitent un travail du moteur distinct de cet assistant.

Voir [le guide](../../guides/sheets.md) et [le contrat HTTP](../api.md).
