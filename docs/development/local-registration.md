# S03 — Comparaison expérimentale de géométrie

[Plan hybride](../product/hybrid-omr-plan.md) · [Contrat de régions](../architecture/regions.md)

## Statut

Le module `local_registration.py` et la commande `geometry_trial.py` expérimentent un
recalage affine **par grille**, après une homographie globale contrôlée. Ils ne sont
pas appelés par le moteur actif, la notation ou l’interface web. Aucun entraînement,
aucune migration et aucune modification des annotations existantes.

L’expérience sépare quatre variantes : repérage global brut, brut + local, global
normalisé, normalisé + local. La normalisation est celle déjà disponible dans
`images.normalized_gray`, appliquée ici **avant ORB** à la source et à la référence.
C’est une piste de préparation photographique S04, isolée du gain éventuel de S03.
Les contrôles de distribution, d’inliers, d’erreur et de plausibilité du `Registrar`
historique sont conservés. Les versions normalisées servent uniquement au repérage ;
les extraits couleur proviennent de la source originale avec une seule projection.

## Exécution par l’agent

Depuis un export de corpus extrait dans un dossier privé :

```bash
.venv/bin/python -m psychomark.geometry_trial \
  artifacts/private/annotated-export-40/source.png \
  --template artifacts/private/annotated-export-40/template.json \
  --manifest artifacts/private/annotated-export-40/manifest.json \
  --output artifacts/private/baselines/nouvel-essai-s03
```

Le manifeste est facultatif pour un diagnostic sans annotations. Le dossier de sortie
doit être nouveau. Un rapport terminé, y compris avec tous les candidats refusés,
renvoie 0 ; une erreur d’exécution renvoie 2. `report.json` est écrit en dernier avec
`complete=true`. Un dossier partiel ne constitue pas un résultat complet.

Les sources, modèles, références, exports humains et rapports restent hors Git.
Le code et les tests synthétiques peuvent être publiés. Conserver les fichiers d’entrée
avec le rapport pour reproduire l’essai ; celui-ci conserve leurs empreintes, pas une
copie de tous les originaux. Aucune commande à exécuter par l’enseignant pour ce lot.

## Recalage local contrôlé

1. Construire quatre bandes autour du cadre de la grille, en coordonnées de référence.
2. Exclure les cases avec une marge couvrant la recherche et vérifier qu’il reste de
   l’encre imprimée sur **chaque côté** et des pixels source disponibles.
3. Chercher une petite translation initiale sur ces repères, puis ajuster une affine
   par corrélation ECC. Les zones exclues sont blanchies avant le lissage de cet essai.
4. Refuser toute inversion, variation d’échelle/cisaillement excessive ou déplacement
   supérieur à 30 % du plus petit pas de grille, avec un plafond de 10 pixels référence.
   Ce plafond empêche de rechercher librement une question voisine.
5. Vérifier séparément le support des quatre côtés et la corrélation. Une correction
   acceptée doit améliorer la corrélation sans dégrader sensiblement un côté. Sans gain,
   conserver l’identité seulement si les contrôles du cadre global passent déjà.

Les seuils sont des garde-fous expérimentaux documentés dans le code, pas une validation
statistique. Un cadre trop proche des cases peut ne plus fournir quatre côtés exploitables
après exclusion : le résultat est alors refusé. Le traitement ne suppose ni couleur
rouge, ni quatre choix, ni questions disposées horizontalement. Il ne corrige pas encore
les courbures internes d’une grille ou une homographie globale refusée.

## Transformations et sorties

Soit `H` la projection source→référence globale et `L` l’affine calculée par ECC,
qui va de la référence finale vers l’image déjà recalée globalement :

- source→référence locale : `inverse(L) @ H` ;
- référence locale→source : `inverse(H) @ L`.

Les images finales sont projetées directement depuis la source. Les masques de présence
sont projetés au plus proche voisin depuis un masque source blanc, avec bord nul.
Les diamètres de cases restent mesurés dans la source via la transformation inverse.
Les régions réutilisent le contrat `QuestionRegion` v1 avec cette inverse composée.

`report.json` est un contrat expérimental séparé du JSON d’extraction : il conserve
les matrices, diagnostics, raisons de refus, régions globales/locales, contrôle aller-retour,
versions du code/OpenCV/NumPy et empreintes des artefacts. Une section refusée n’a pas
de matrice locale ni de régions locales ; ses régions globales restent distinguées.
`historical-result.json` conserve le rejeu du moteur inchangé. Les contrôles de qualité
avant/après restent des diagnostics, pas une autorisation de lecture automatique.

`summary.md` et `review.html` proposent les extraits référence/global/local. Les photos
ne sont jamais transmises à un service externe. L’ancien contrat S01 et les instantanés
stockés ne sont pas réécrits.

## Utiliser les 40 annotations

Le manifeste doit être en **développement** et ses empreintes source, référence et
instantané du modèle doivent correspondre. Les données de test réservé ne sont pas
acceptées par cet outil d’expérimentation. Les annotations partielles sont utilisables :
seuls les cadres manuels confirmés, avec coordonnées valides et identifiants cohérents,
entrent dans la comparaison. Les questions sans annotation ne deviennent pas des blancs.

Le repérage ne reçoit pas les cadres humains ou les choix marqués. La comparaison a lieu
**après** le calcul des candidats : nombre de questions localisées, centres de tous les
choix contenus dans le cadre humain, distance entre le centre de ces choix et celui du
cadre. Les pages refusées restent dans le dénominateur des cadres humains disponibles.

Ces mesures ne valident ni le contour exact de chaque case, ni la bonne lecture de sa
marque, ni l’identification sur des photos inédites. `answer_accuracy` reste `null`.
Une grande boîte humaine peut contenir plusieurs colonnes : l’inspection reste utile.

## Résultats et limites actuels

Les résultats privés et leur portée sont consignés dans la
[session S03](../memory/sessions/2026-10-08-14-s03-geometry.md). La prochaine étape est
S04 : confirmer et comparer le gain de préparation des photos sur davantage de cas,
puis S05 pour la lecture des marques. La normalisation seule ne suffit pas à annoncer
une lecture correcte. L’activation dans l’application reste un lot distinct.
