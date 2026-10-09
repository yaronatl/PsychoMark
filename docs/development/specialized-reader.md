# S06 — Prototype ML spécialisé hors ligne

[Plan hybride](../product/hybrid-omr-plan.md) · [ADR 0006](../architecture/decisions/0006-offline-cpu-ml.md)

## Ce qui est disponible

`ml_data.py` prépare les cases depuis un export S02 extrait ; `ml_reader.py` entraîne
un petit CNN et recharge ses poids sur CPU ; `ml_trial.py` expose les commandes.
Le moteur historique, les notes et le web ne changent pas. Ces outils ne constituent
pas un nouveau bouton dans l’application et n’apprennent pas automatiquement des saisies.

Le lecteur partage les mêmes poids entre tous les choix. Les quatre sorties désignent
**vide, marquée, ambiguë, inexploitable**, pas les réponses 1/2/3/4. Les modèles de feuille
conservent 2 à 10 choix. Aucun corrigé n’entre dans la préparation ou l’entraînement.

## Environnement optionnel

Commandes de référence pour le développeur, exécutées par Codex lors de la session :

```bash
UV_CACHE_DIR=/workspace/.cache/uv uv sync --frozen --extra dev --extra browser --extra ml
.venv/bin/python -m pytest -q tests/test_ml_data.py tests/test_ml_reader.py
```

L’extra `ml` n’est nécessaire que pour entraîner/exécuter le CNN. La préparation et
le moteur existant ne l’importent pas. Conserver `--extra browser` si les outils
navigateur sont utilisés ; une nouvelle synchronisation peut retirer les extras omis.
Le job CI `ml` installe explicitement cet extra. Sans lui, pytest ignore le module de
tests du lecteur ML et teste quand même la préparation ; cela ne valide pas l’entraînement.

## Préparer un export réel

```bash
.venv/bin/python -m psychomark.ml_trial prepare \
  artifacts/private/annotated-export-90/manifest.json \
  --output artifacts/private/ml/regions-nouveau-lot
```

L’export extrait doit contenir `manifest.json`, `source.png`, `template.json` et sa
référence. Les empreintes, dimensions, sections, choix et annotations sont vérifiés.
Le recalage global normalisé de S03 est essayé en premier. S'il est refusé, le recalage
historique sur gris brut est essayé avec ses contrôles inchangés. Les deux tentatives,
le motif de repli et la méthode acceptée sont conservés dans la provenance. Ce repli
évite qu'une normalisation défavorable bloque une copie lisible géométriquement par
le moteur historique. Si les deux méthodes échouent, aucune région n'est inventée.
La transformation acceptée précède une projection unique de l'image couleur originale.
Les marques humaines ne participent pas au recalage. Un recalage accepté ne garantit
pas la précision des régions proposées : la revue reste nécessaire.

Chaque sortie exige un dossier neuf. Elle conserve :

- `dataset.json` : provenance, groupes, partition, labels, positions et empreintes ;
- les PNG de chaque case brute, de sa référence et du contexte de question ;
- `review.html` : galerie privée des propositions, sans validation implicite ;
- `geometry-review.json` : toutes les décisions réelles initialement `pending`.

La revue des coordonnées est distincte de l’annotation des marques. Un réviseur
technique inspecte que la découpe contient la bonne case, puis inscrit pour les
échantillons vérifiés `status: "confirmed"` et son alias `reviewer` dans ce fichier.
Une mauvaise découpe reçoit `rejected`. Ce fichier est lié à l’empreinte exacte du jeu :
modifier le jeu impose une nouvelle revue. **Les réponses déjà annotées ne sont pas
à ressaisir.** Il n’existe pas encore d’éditeur web de cette revue par case.

Le drapeau historique `case_coordinates_validated` ne suffit jamais. Le chargeur
exige la revue séparée pour les données réelles. Les garde-fous connus persistent :
fraction visible < 0,99, diamètre source minimal < 6 pixels, géométrie de question
non confirmée ou centre hors du cadre humain. Le seuil 6 est un plancher d’échantillonnage
expérimental, pas une limite de lecture validée ni le remplacement des contrôles web.

Le prétraitement `bubble-gray-letterbox32-v1` convertit en gris, conserve le rapport
de forme, redimensionne et complète en blanc jusqu’à 32×32. La copie brute est conservée :
pas de soustraction de référence ni de normalisation locale d’une petite case. La
référence devient un second canal uniquement pour la variante appariée. Les tailles
source restent enregistrées ; le contexte question est disponible pour contrôle mais
n’entre pas dans ce CNN initial.

## Entraîner et comparer les deux entrées

Circuit technique synthétique, sans valeur de précision terrain :

```bash
.venv/bin/python -m psychomark.ml_trial synthetic --groups 16 \
  --output artifacts/private/ml/exemples-techniques
.venv/bin/python -m psychomark.ml_trial train \
  artifacts/private/ml/exemples-techniques/dataset.json --epochs 16 \
  --output artifacts/private/ml/modele-case
.venv/bin/python -m psychomark.ml_trial train \
  artifacts/private/ml/exemples-techniques/dataset.json --epochs 16 --paired-reference \
  --output artifacts/private/ml/modele-reference
```

Un CNN (~17 000 paramètres), Adam, lots de 32, graine fixée, deux threads CPU et
algorithmes déterministes. Les poids de classes sont calculés uniquement sur `train`.
Les quatre classes doivent y être présentes. La partition développement ne modifie
ni gradients, ni poids de classes, ni nombre d’époques ; pas d’arrêt anticipé ou de
sélection automatique par son score. Les pertes sont enregistrées à chaque époque.
La reproductibilité est testée dans le même environnement, pas garantie bit à bit
entre matériels ou versions de bibliothèques.

Les exemples artificiels représentent ovales/chiffres, remplissages/coches, traits
pâles et zones brouillées, avec un bruit léger. Les identités synthétiques séparent
les groupes avant l’entraînement, mais ne représentent pas des personnes ou appareils
indépendants. Aucune augmentation dégradante ne conserve artificiellement un label certain.
Ces exemples ne simulent pas toute la diversité de l’impression et de la photo.

Pour plusieurs exports, passer plusieurs `dataset.json` au même entraînement.
Le chargeur refuse les mêmes acquisitions/questions/choix dupliqués ainsi qu’un
groupe, une feuille ou une empreinte d’acquisition traversant les partitions.
Les données réelles doivent être autorisées et explicitement affectées à `train` ;
la commande ne transforme pas une copie de développement en entraînement.
Les partitions `test`/`calibration` sont réservées et refusées ici.

`model.json` contient la configuration, les empreintes des jeux/revues/code/verrou,
les versions, les groupes utilisés, les pertes et les matrices de confusion.
`weights.npz` contient uniquement les tenseurs numériques. Le chargement vérifie
le prétraitement, les classes, les formes et l’empreinte, sans exécution de pickle.

## Observer les sorties

```bash
.venv/bin/python -m psychomark.ml_trial predict \
  artifacts/private/ml/regions-nouveau-lot/dataset.json \
  --model artifacts/private/ml/modele-reference \
  --output artifacts/private/ml/observations-nouveau-lot
```

`predictions.json` fournit logits, softmax non calibré, classe visuelle proposée et
motifs de revue par case. **Tous les cas restent en revue**, même si un score est élevé.
Un modèle entraîné seulement sur synthétique est identifié comme tel sur les données
réelles. Une géométrie non validée interdit le calcul d’une précision par case.
Le rapport signale les groupes déjà vus à l’entraînement. Il ne constitue jamais
un test indépendant, n’émet pas de réponse publique et ne modifie aucune note.

Les temps d’inférence excluent préparation, chargement et écriture ; ce ne sont pas
des latences de correction complètes. Les scores ne doivent pas être présentés comme
une probabilité de réponse correcte. Le nombre de décisions automatiques reste zéro
par conception jusqu’à une politique de décision évaluée séparément en S07.

## Limites et suite

Le premier circuit et les deux entrées sont exécutables. L’essai réel avec les poids
synthétiques échoue à distinguer les marques : voir [la session](../memory/sessions/2026-10-09-05-s06-prototype.md).
Ce résultat ne démontre ni une amélioration face à S05 ni l’impossibilité du ML.

La suite de S06 est de vérifier les régions réelles, compléter les classes rares,
constituer plusieurs groupes de copies, puis entraîner et comparer sur un développement
distinct. Le contexte complet de question et une meilleure normalisation des entrées
pourront être testés après cette base. S07 n’est pas une activation automatique après
la réussite des tests synthétiques.

Le [premier lot réel d'entraînement](../memory/sessions/2026-10-09-06-corpus-240.md)
est maintenant préparé à partir d'un nouvel export de 240 questions. L'export original
de développement est conservé, et une version dérivée est explicitement affectée à
`train` avec trace de transition ; elle ne constitue plus une évaluation indépendante.
La revue technique assistée par Codex des régions est identifiée comme telle, distincte
d'une seconde annotation humaine. L'entraînement sur une seule copie réelle apprend
cette copie mais échoue encore sur la photo sombre de développement ; aucune activation.
