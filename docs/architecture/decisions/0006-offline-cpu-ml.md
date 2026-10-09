# ADR 0006 — Lecteur ML expérimental local et optionnel

Date : 2026-10-09 (Asia/Jerusalem). État : **adopté pour le prototype S06**,
sans activation ni validation de fiabilité terrain.

## Contexte et choix

S05 ne gagne aucune lecture automatique sur la première copie annotée. S06 doit
permettre d’entraîner et comparer un petit lecteur sans introduire de dépendance
ML dans le démarrage web, sans corrigé et sans transformer des scores en certitudes.

Retenir PyTorch CPU dans l’extra `ml`, verrouillé par uv ; index CPU explicite sous
Linux/Windows, PyPI sur les autres plateformes. Linux Python 3.12 est vérifié ici ;
les autres plateformes ne le sont pas. Aucun GPU, service distant ou poids préentraîné.
Un unique CNN partagé entre les cases distingue quatre observations visuelles.
Une variante à deux canaux permet la comparaison avec la référence vierge ; elle
ne décide pas d’un gagnant parmi les choix d’une question.

Le prétraitement conserve le rapport de forme dans un carré de 32 pixels. Les
dimensions source et les défauts de géométrie restent dans le manifeste. Agrandir
une image ne relève pas sa résolution native. Le premier essai ne prétend pas
résoudre les écarts d’impression, d’éclairage ou de flou.

## Données et reproductibilité

Un cadre de question confirmé ne valide pas les régions de ses cases. La préparation
S06 produit des régions proposées et une revue séparée liée à l’empreinte du jeu.
Une revue explicite par case peut autoriser sa géométrie, mais ne modifie jamais
les annotations S02. Les groupes, feuilles physiques et empreintes d’acquisition
ne traversent pas les partitions. Des quasi-doublons dont les identités ont été
mal renseignées ne sont pas détectés automatiquement.

Seules les données `train`, autorisées, sans défaut qualité connu et dont la géométrie
est validée alimentent les gradients. `development` sert aux mesures exploratoires.
`calibration` et `test` sont refusés par cet outil de développement. Aucun déplacement
implicite d’une partition à l’autre ni réentraînement déclenché par une annotation web.

Les poids sont des tableaux numériques NPZ, chargés sans pickle avec contrôle
d’empreinte, forme, type et valeurs finies. Un manifeste conserve données, revue,
classes, prétraitement, code, configuration, graine, versions et métriques. Les
poids, scans, annotations et rapports réels restent privés et hors Git.

## Conséquences

Le modèle fournit logits et softmax **non calibré**. Toutes les sorties demandent
une revue ; aucune décision publique ni note ne consomme ce prototype. S07 devra
introduire une politique évaluée séparément, en préservant les garde-fous optiques.
S06 livre l’outillage ; la généralisation demande des copies variées et réservées.
L’essai du contexte complet de question reste différé ; il est exporté pour contrôle.

Réexaminer ce choix si les exemples réels validés ne montrent pas de gain mesurable.
ONNX et accélération GPU restent des options, sans dépendance ni service ajouté.
Procédure et limites : [S06](../../development/specialized-reader.md).
