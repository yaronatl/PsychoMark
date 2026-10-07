# Moteur optique : fonctionnement et limites

[Documentation](../README.md)

## Fonctionnement et limites

L'alignement global utilise des points ORB, un appariement filtré et une
homographie RANSAC. Les bulles sont exclues des centres des repères de référence.
Le moteur vérifie la répartition des correspondances, leur erreur géométrique,
les cadres, les zones visibles et la taille des bulles dans l'image d'origine.
Une normalisation locale de l'éclairage précède la comparaison à la référence
vierge. Les pixels imprimés sombres et les contours sont exclus de la mesure
des marques ; les contours servent aussi à contrôler la netteté.

Ce n'est pas un lecteur universel. Restent notamment à éprouver sur données
réelles : différences d'imprimantes, gommes, crayons légers, lumière non uniforme,
photocopies et compression. Les reflets peuvent détruire l'information ; la
détection ne peut pas toujours s'en apercevoir. Les feuilles courbées, pliées ou
déformées localement ne sont pas corrigées par une simple homographie globale.
Une grille trop répétitive sans repères distinctifs peut échouer à l'alignement.

Il n'y a pas encore de reconnaissance de noms, de barèmes pondérés, de conversion
vers un score psychométrique officiel ou d'isolation multi-organismes.
Les annotations conservent le contenu
visible des documents : stocker les vrais scans dans un emplacement privé,
idéalement sous `artifacts/private/` pour éviter de les ajouter à Git.
