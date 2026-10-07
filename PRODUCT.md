<!-- impeccable:product-schema 1 -->
# PsychoMark

## Produit et utilisateurs

Atelier web de correction des QCM d’entraînement aux psychométriques, destiné aux
enseignants et aux organismes de préparation. L’objectif est de réduire le travail
répétitif tout en permettant la vérification des réponses ambiguës.

Plateforme actuelle : web, interface française, utilisable sur ordinateur et mobile.
Le service fonctionne dans un espace de travail privé, notamment GitHub Codespaces.

## Parcours disponible

Créer un examen, sélectionner un modèle de feuille et les questions utilisées,
renseigner le corrigé, importer des images ou PDF, vérifier les réponses incertaines,
consulter la note brute et exporter le détail. Plusieurs sections peuvent être ignorées.
Le moteur optique ne voit pas le corrigé. Les décisions humaines restent historisées.

## Vérité du prototype

Les essais portent sur des feuilles synthétiques. Les modèles NITE et Adar ne sont pas
calibrés. Aucun taux de précision sur scans réels, gain de temps chiffré, client ou prix
n’est établi. La note n’est pas le score psychométrique officiel. Il n’y a ni comptes
utilisateurs, ni isolation par entreprise, ni abonnement commercial.

## Direction exprimée par l’utilisateur

Calme, chaleureuse, douce et claire ; typographie serif soignée ; intelligence et
élégance ; association du papier, du stylo et de l’encre à un outil moderne.
Renance est l’inspiration principale fournie ; reMarkable est une référence d’ambiance
citée par l’utilisateur. La première proposition graphique reste à apprécier ensemble.

## Références du projet

- [Périmètre et priorités](docs/product/roadmap.md)
- [Direction visuelle et statut des choix](docs/product/visual-direction.md)
- [Cadre de l’interface](docs/product/ui.md)
- [Architecture et invariants](docs/architecture/overview.md)

Torph a été demandé explicitement et anime les libellés d’analyse. Le comportement du
Button Be UI est adapté en natif ; son composant React n’est pas installé.

La bibliothèque UI future appartient au choix de l’utilisateur. Cette proposition
conserve le HTML/CSS/JavaScript existant ; installer des skills ne décide pas d’une
migration de framework.
