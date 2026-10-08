# Contrats S01 — Régions, observations et provenance

[Architecture](overview.md) · [Utilisation baseline](../development/omr-baseline.md)

## Frontière actuelle

`Engine.analyze(image, exam)` reste inchangé. `Exam` contient la sélection des questions,
aucune bonne réponse. `baseline.py` appelle le moteur une fois, exporte son résultat
intact et produit un contrat géométrique séparé, validé par les modèles de `regions.py`.
Les seuils et instantanés historiques ne sont pas enrichis implicitement.

## Régions version 1, implémentées

- Origine en haut à gauche, axes x vers la droite et y vers le bas, unités pixels.
- Source : tableau décodé/orienté ; référence : dimensions du modèle de feuille.
- Rectangles `[x0,y0,x1,y1)` à bornes entières, coin supérieur gauche inclus et inférieur
  droit exclu. Les quadrilatères projettent les **centres** des quatre pixels d’angle.
- Matrices source→référence et inverse exportées. La matrice provient du résultat
  observé ; aucun second recalage indépendant. Le redressement emploie l’interpolation
  historique, et le masque valide l’interpolation au plus proche voisin.
- Pour chaque question : section, numéro, rectangle de contexte en référence,
  quadrilatère et rectangle source tronqué aux dimensions réelles, fraction visible,
  choix ordonnés et chemins relatifs d’assets. Les questions suivent l’ordre du résultat.
- Pour chaque choix : identifiant 1–10, centre source/référence, ROI identique à
  `bubble_roi`, quadrilatère source, diamètres source horizontal/vertical et fraction visible.
- Les diamètres source précèdent tout agrandissement ; une fraction visible n’est
  pas une confiance de lecture. Les coordonnées hors source restent dans le quadrilatère.
- Un alignement impossible donne des matrices nulles et zéro région ; les réponses
  refusées et la liste des annotations à prévoir restent complètes.

Trois masques distincts accompagnent chaque question : `valid` indique les pixels
disponibles, `interior` l’intérieur elliptique, `sampling` les pixels intérieurs dont
la référence normalisée est supérieure à 200, selon la règle historique. Ce dernier
est le masque de mesure **potentiel** ; un refus préalable peut empêcher le lecteur
de l’utiliser. Il n’est pas intersecté avec `valid`, car le moteur teste justement
la présence de pixels invalides dedans. Les rectangles obliques qui se recouvrent
sont fusionnés par union, sans effacer les pixels d’une autre case.

`copy` est la couleur brute recalée ; `normalized_copy` et `normalized_reference`
proviennent de la normalisation de la page entière **avant** recadrage. Normaliser
un petit extrait isolé produirait un autre prétraitement. `overlay` est uniquement
un repère visuel, jamais une entrée de lecture. Un extrait source totalement hors
image est absent ; un masque nul n’est pas une réponse blanche.

Le contrat historique conserve `local_alignment=null`. S03 ajoute un
[rapport expérimental séparé](../development/local-registration.md) avec les matrices
composées par grille et des `QuestionRegion` v1 calculées avec leur inverse. Il ne
réécrit pas les régions S01 ni les extractions web ; aucun lecteur actif ne consomme
encore ces corrections.

## Observations historiques, implémentées

Les champs `section`, `question`, `status`, `answer`, `candidates`, `reason`, `scores`
conservent leur sens actuel. Les scores mesurent encre et contraste ; aucune probabilité
calibrée n’est produite. Les décisions sont indépendantes des labels humains et du corrigé.
`report.json` associe cette extraction à sa version, ses empreintes et son prétraitement.

| Consommateur actuel | Contrat à préserver |
|---|---|
| `cli.py` | JSON, réponses CSV et compteurs |
| `grading.py` | Association section/question, états et réponses ; notation séparée |
| `store.py` | Extraction complète conservée comme instantané |
| `web.py` | Résultats et matrice pour l’image recalée |
| `readability.py` | Motifs, contrôles locaux et diagnostic global |
| `sheets.py`, `static/sheets.js` | Essai enregistré, explications et ZIP de diagnostic |

## Extension ML, prototype S06 et décision S07 future

Un lecteur recevra identifiants, extraits, contexte/référence éventuels, masques,
mesures de qualité et version du prétraitement. Sa sortie distinguera observations
visuelles, scores bruts, probabilités calibrées éventuelles et provenance du modèle.
Une politique séparée produira les cinq états publics historiques. Géométrie invalide
et ambiguïté restent des motifs d’abstention, même avec un score élevé.

S06 fournit désormais [un jeu de cases versionné, un CNN CPU et ses observations](../development/specialized-reader.md).
Les découpes utilisent `ChoiceRegion` ; leur revue est séparée des cadres de question
S02 et liée à l’empreinte du jeu. Les logits et softmax restent non calibrés ; toutes
les observations demandent une revue. La politique de décision S07 n’est pas implémentée.
Le contrat optique ne contient ni corrigé, ni note, ni identité d’élève.

## Annotation préparée, non validée

`annotations.pending.json` propose pour chaque question `geometry_valid`, `status`,
`choices`, `reviewer`, `notes`. Les premiers champs sont nuls : « pas encore annoté »
est distinct de « aucune réponse visible ». S02 fixera la validation, le réviseur,
les ambiguïtés et l’identité de feuille physique avant l’entraînement. Aucun label
humain ni identifiant de groupe d’apprentissage n’est déduit automatiquement en S01.
