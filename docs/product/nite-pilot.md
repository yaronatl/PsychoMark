# Modèle NITE prioritaire

[Priorités](roadmap.md) · [Calibration existante](../guides/cli.md)

## Décision produit

Le 8 octobre 2026, l’utilisateur précise que la feuille NITE montrée est celle des
examens officiels et la plus courante dans son usage. Elle devient le premier modèle
réel à prendre en charge. La demande suivante de l’utilisateur donne toutefois
priorité à l’[assistant de création](../guides/sheets.md), désormais implémenté,
pour qu’il puisse importer et configurer lui-même ses feuilles dans l’application.
Cette indication d’usage vient de l’utilisateur ; aucune mesure indépendante de
fréquence ni vérification de toutes les éditions officielles n’est revendiquée.

Objectif : fournir un modèle NITE préconfiguré, réutilisable par les enseignants.
Ils choisissent leurs sections, questions et corrigés sans redécrire la géométrie.
Les autres feuilles restent possibles via des modèles distincts.

## Périmètre de la feuille montrée

L’image visible présente huit blocs de réponses : cinq à gauche, trois à droite,
trente emplacements de questions par bloc et quatre choix par question. Ces capacités
physiques ne déterminent ni le nombre de questions d’un examen ni les sections à noter.
Les zones d’identité, l’exemple et les repères d’impression ne sont pas des réponses.

Calibrer sur les pixels du fichier source réel, sans recopier les coordonnées du
modèle synthétique. Ne pas supposer qu’une variante d’impression ou d’édition possède
exactement les mêmes dimensions. Identifier/versionner la référence effectivement prise
en charge ; les scans et photos devront pouvoir se recaler sur cette référence.

## Travail à réaliser

1. Récupérer la feuille vierge originale, vérifier netteté, cadrage et résolution.
2. Décrire ses cadres et cases ; produire la prévisualisation de calibration.
3. Vérifier tous les emplacements et l’alignement. Tester la feuille vierge sans
   interpréter l’impression rouge, les chiffres ou les repères comme des réponses.
4. Ajouter des marques contrôlées pour diagnostiquer la lecture et les transformations
   géométriques. Ces essais artificiels ne prouvent pas la précision sur papier réel.
5. Comparer des scans/photos de feuilles remplies à leur annotation manuelle : marques
   nettes, absences, coches, traces faibles, doubles marques et effacements. Les images
   ayant servi aux réglages sont séparées du jeu de validation.
6. Mesurer les erreurs acceptées automatiquement, les réponses correctement lues,
   les demandes de vérification et les refus de page. Ne pas déduire l’intention quand
   l’image ne permet pas de trancher. Définir le niveau acceptable pour le pilote.
7. Charger le modèle dans l’application, vérifier sélection de sections/questions,
   import, décisions humaines, note et exports. Distinguer expérimental et validé.

Il s’agit d’une calibration de géométrie et de lecture optique, pas d’un entraînement
de réseau neuronal. Une grande base n’est pas nécessaire pour commencer la calibration ;
des copies réelles restent nécessaires pour mesurer la fiabilité.

## État au cadrage

Le fichier `SCR-20261007-lowy.png` est visible dans la conversation, mais aucun fichier
source accessible au programme n’a été retrouvé dans le checkout ou les pièces
disponibles de cet environnement. Le chemin `/Users/yaronattal/Desktop/…` désigne le
poste de l’utilisateur. Aucune calibration NITE n’a été exécutée ; aucun faux modèle
de remplacement ni activation NITE dans l’interface n’a été créé.

Le PNG ou le PDF original peut maintenant être importé directement dans
**Mes feuilles → Ajouter une feuille**, sans passer par les pièces jointes du chat.
Les copies remplies serviront ensuite aux essais réels. Conserver les données d’élèves
dans un emplacement privé, hors Git.
