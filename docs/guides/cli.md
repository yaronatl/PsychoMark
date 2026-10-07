# Utiliser le moteur et calibrer une feuille

[Documentation](../README.md)

## Essayer immédiatement

```bash
# Créer une feuille vierge, des copies synthétiques et leur vérité de référence.
.venv/bin/python -m psychomark demo --output artifacts/demo

# Lire 20 questions réparties sur deux sections non consécutives.
.venv/bin/python -m psychomark analyze artifacts/demo/copy.png \
  --template artifacts/demo/template.json \
  --exam artifacts/demo/exam.json \
  --output artifacts/results
```

Résultat attendu pour cet examen court : **12 réponses uniques, 2 absences de
marque, 2 réponses multiples et 4 réponses incertaines**. Les cas ambigus sont
introduits volontairement dans la démonstration.

Le dossier de sortie contient :

```text
001-copy-page001.json           # Réponses, mesures et contrôles de qualité
001-copy-page001.csv            # Une ligne par question active
001-copy-page001.annotated.png  # Zones lues, dans les coordonnées du modèle
summary.json                   # État de chaque page du lot
```

Pour lire les 240 questions du modèle, omettre `--exam`. Pour refaire une commande,
choisir un nouveau dossier de sortie : **les résultats existants ne sont jamais
écrasés**. Les fichiers sous `artifacts/` sont exclus de Git.

Autres essais :

```bash
.venv/bin/python -m psychomark analyze \
  artifacts/demo/copy-perspective.jpg artifacts/demo/copy-rotated.png \
  --template artifacts/demo/template.json --output artifacts/transformed

# Autre géométrie : questions verticales, cinq choix, trois sections.
.venv/bin/python -m psychomark demo --vertical --output artifacts/vertical
.venv/bin/python -m psychomark analyze artifacts/vertical/copy.png \
  --template artifacts/vertical/template.json --output artifacts/vertical-results
```

`copy-blurred.png` est volontairement dégradée. Son analyse doit signaler une
page illisible, et retourner le code de sortie 1, plutôt que des réponses vides.


## Adapter un examen court ou complet

La feuille décrit où se trouvent les bulles. L'examen choisit les questions à
analyser. Le fichier d'examen ne contient **pas** de corrigé :

```json
{
  "name": "Entraînement de deux sections",
  "template_id": "demo_eight_sections_v1",
  "sections": {
    "1": [1, 2, 3, 4, 5],
    "6": [1, 2, 3]
  }
}
```

Les identifiants de section correspondent aux blocs physiques du modèle. Les
questions et les choix sont numérotés à partir de 1. Les questions inutilisées
sont absentes du résultat ; elles ne deviennent pas des réponses manquantes.
Les sélections vides, doublons, questions hors limites et mauvais identifiants
de modèle sont refusés. Le nombre de sections n'est jamais déduit des marques.


## Ajouter une vraie feuille

1. Obtenir une image **vierge**, complète et nette de la feuille (PNG/JPEG/TIFF).
   Un scan proche de 300 dpi est un bon point de départ. Ne pas agrandir une
   petite image pour prétendre gagner en résolution.
2. Décrire sa géométrie dans un fichier `layout.json`, en pixels de cette image.
   Utiliser [layout-eight-sections.json](../../examples/layout-eight-sections.json) pour comprendre le format,
   **pas comme coordonnées d'une feuille NITE ou Adar**.
3. Calibrer puis vérifier visuellement la prévisualisation.
4. Valider le modèle sur des copies remplies et annotées manuellement avant
   d'utiliser les résultats pour attribuer des notes.

```bash
.venv/bin/python -m psychomark calibrate artifacts/private/blank.png \
  --layout artifacts/private/layout.json \
  --output artifacts/private/school-v1.json

.venv/bin/python -m psychomark analyze artifacts/private/student.jpg \
  --template artifacts/private/school-v1.json \
  --exam artifacts/private/exam.json \
  --output artifacts/private/results
```

La calibration crée `school-v1.json`, `school-v1.reference.png` et
`school-v1.preview.png`. Conserver ces fichiers ensemble. Les centres rouges
et les ellipses vertes de la prévisualisation doivent tomber dans **toutes** les
bulles. Cette vérification reste manuelle dans le MVP. Une image marquée peut
être refusée comme référence ; cette vérification ne prouve pas qu'une référence
est réellement vierge.

Le fichier `layout.json` contient `schema_version: 1`, `template_id`, `width`,
`height` et une liste `sections`. Chaque section est décrite ainsi :

```json
{
  "id": "1",
  "questions": 30,
  "choices": 4,
  "bounds": [80, 280, 795, 158],
  "first_center": [94, 320],
  "question_step": [26.5, 0],
  "choice_step": [0, 30],
  "bubble_radius": [8, 11]
}
```

L'origine `(0, 0)` est le coin supérieur gauche. `bounds` vaut `[x, y, largeur,
hauteur]` et suit le **cadre imprimé** de la section. `first_center` est le centre
du choix 1 de la question 1. Les deux vecteurs `*_step` décrivent les déplacements
entre questions et entre choix ; ils permettent aussi les grilles verticales.
`bubble_radius` contient les deux rayons, pas les diamètres. Les données de cet
exemple sont celles de la démonstration uniquement.

Cette version exige des sections rectangulaires encadrées et des bulles
régulièrement espacées dans chaque section. Les mises en page irrégulières ou
sans cadre nécessitent une évolution du moteur. La calibration ne découvre pas
automatiquement les questions. Le modèle est choisi explicitement à l'analyse.


## Images, PDF et lots

```bash
.venv/bin/python -m psychomark analyze copies/ fichier.pdf \
  --template modeles/ecole-v1.json --exam examens/blanc.json \
  --dpi 200 --output artifacts/lot-001
```

Chaque page PDF est traitée comme une copie indépendante du même modèle et du
même examen. Les dossiers sont parcourus sans récursion. Les lots mélangeant
plusieurs modèles doivent être séparés au préalable. Les pages de couverture
ou d'autres documents sont signalées comme non lisibles avec ce modèle.

Limites : 64 MiB par fichier, 20 mégapixels par image/page rendue, 100 pages par
PDF ; rendu PDF de 100 à 400 dpi (200 par défaut). Les TIFF multipages sont
refusés : les convertir en PDF. Une erreur de lecture d'un fichier/page est
enregistrée et le lot continue. Aucun résultat final d'identité d'élève n'est
déduit du nom manuscrit : seul le nom du fichier et le numéro de page sont utilisés.


## Comprendre les résultats

| État d'une question | Interprétation |
|---|---|
| `single` | Une marque nette sans marque concurrente détectée ; `answer` contient le choix |
| `blank` | Aucune marque détectable dans une zone jugée lisible ; cela ne prouve pas l'absence d'un trait extrêmement faible |
| `multiple` | Plusieurs marques fortes ; aucune réponse finale choisie |
| `uncertain` | Marque faible ou marques concurrentes ; aucune réponse finale choisie |
| `unreadable` | Alignement, résolution, cadrage ou netteté insuffisants |

L'état de la copie est `complete`, `needs_review` ou `unreadable`. `input_error`
signale un fichier/page impossible à charger. **`complete` signifie extraction
terminée sans exception détectée, pas exactitude garantie ni note validée.**

Les mesures `dark_coverage`, `trace_coverage` et `mean_delta` expliquent la
détection ; ce ne sont **pas des probabilités de justesse**. Les seuils sont
versionnés avec le modèle et doivent être validés sur un corpus réel distinct
des images utilisées pour les régler. Une trace effacée peut conduire à une
vérification, même si l'autre choix paraît plus sombre.

Les JSON conservent les empreintes du fichier, du modèle et de sa référence,
la version du moteur, la sélection de questions, la transformation géométrique
et les motifs de rejet. La référence est vérifiée par SHA-256 au chargement.

Codes de sortie :

- `0` : rapports produits sans question illisible ; des `multiple`/`uncertain`
  peuvent encore nécessiter une vérification. Inspecter `summary.json`.
- `1` : au moins un fichier/page en erreur ou une question illisible ; les
  autres résultats sont conservés.
- `2` : configuration, arguments ou écriture invalides ; traitement interrompu.

L'image annotée utilise vert = réponse unique, gris = aucune marque,
orange = incertain, rouge = multiple/illisible. Pour un échec d'alignement, elle
montre l'image d'origine avec un avertissement plutôt qu'une grille inventée.
