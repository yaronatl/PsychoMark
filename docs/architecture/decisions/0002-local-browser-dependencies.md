# ADR 0002 — Dépendance d’animation locale, sans migration frontend

- État : adopté pour la première proposition du prototype.
- Date : 2026-10-08 (Asia/Jerusalem).
- Contexte : l’utilisateur autorise une refonte papier/encre et demande Torph, en
  invitant à utiliser Be UI. L’interface existante est en JavaScript natif ; le choix
  d’un framework général reste ouvert.

## Décision

Utiliser l’API vanilla de Torph pour le changement de libellé pendant l’analyse.
Introduire un manifeste et verrou npm à la racine, avec une commande de publication
locale des assets. Conserver ces assets dans Git : le serveur Python les sert sans
Node en production ni CDN côté navigateur. Héberger aussi les polices localement.

Le bouton Be UI sert de référence de comportement, adaptée en CSS natif pour une
pression discrète. Ne pas installer React, Motion et Tailwind uniquement pour cette
interaction, ni présenter l’adaptation comme le composant React original.

Torph injecte un style : le build calcule l’empreinte de son contenu exact et le serveur
l’autorise dans CSP. Les scripts restent limités à la même origine et `unsafe-inline`
n’est pas ajouté. Respecter la réduction de mouvement, conserver un nom accessible
pendant l’analyse et nettoyer les ressources de l’animation après la requête.

## Options écartées et conséquences

- Copier une animation ressemblante à Torph n’aurait pas utilisé la bibliothèque
  explicitement demandée. L’API native le permet sans migration.
- Une réécriture React aurait un coût et une portée supérieurs à cette interaction.
- Un CDN ajouterait une dépendance réseau à l’usage ; les assets locaux l’évitent.

Node est nécessaire au développement des dépendances navigateur, pas au serveur.
La CI reconstruit et compare les assets versionnés. Une mise à jour de Torph demande
rebuild, redémarrage du serveur (nouvelle empreinte), puis essais navigateur incluant
CSP, mouvement normal/réduit et nettoyage. Les instructions sont dans
[les outils de design](../../development/design-tools.md).

Le dessin et la palette sont une proposition, pas une approbation implicite de
l’utilisateur. Réexaminer cet ADR lorsque le choix de framework/composants sera arrêté.
