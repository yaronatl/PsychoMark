# PsychoMark — moteur OMR et interface de correction

Un fichier de copie + un modèle de feuille + les questions à lire → réponses
JSON/CSV et image annotée. Python/OpenCV, sans IA, sans OCR et sans service distant.
Une interface web en français permet maintenant de gérer les examens, fournir
le corrigé, importer les copies et obtenir la correction question par question.
Le moteur de reconnaissance reste indépendant du corrigé ; un module séparé
calcule les notes. L'interface conserve ses données dans une base SQLite locale.

**État : prototype fonctionnel testé sur des données synthétiques. Les feuilles
réelles NITE et Adar vues dans la conversation ne sont pas encore calibrées ni
validées. Aucun taux de précision sur des copies réelles n'est annoncé.**

## Développer entièrement dans GitHub Codespaces

Le dépôt contient une configuration `.devcontainer/` pour travailler et tester
dans le navigateur, sans installer le projet sur un ordinateur personnel.

1. Dans le dépôt GitHub **yaronatl/PsychoMark**, ouvrir **Code → Codespaces →
   Create codespace on main**.
2. Attendre la construction du conteneur et l'installation automatique. Le
   serveur démarre automatiquement avec le rechargement de développement.
3. L'aperçu du port **8000** est configuré pour s'ouvrir dans le navigateur. S'il
   ne s'ouvre pas, utiliser l'onglet **Ports**, puis **Open in Browser** sur 8000.
4. Conserver la visibilité du port sur **Private**, valeur par défaut de
   Codespaces. L'application n'a pas de comptes utilisateurs propres.
5. Cliquer sur **Essayer la démonstration** dans PsychoMark.

Les sources, dépendances, examens et copies restent dans le Codespace. Les
modifications de Python redémarrent le serveur ; les modifications de l'interface
actualisent le navigateur sous quelques secondes. Une saisie non enregistrée
ou un traitement en cours retarde l'actualisation pour ne pas perdre le travail.
Les données de `artifacts/web/` sont conservées quand on arrête puis reprend le
**même** Codespace, mais ne sont pas envoyées dans GitHub. Exporter ce qu'il faut
conserver avant de supprimer un Codespace.

Cette actualisation concerne les fichiers du Codespace. **Cette conversation
Codex et un Codespace sont deux machines différentes.** Les changements effectués
ici doivent être envoyés dans GitHub, puis récupérés dans le terminal Codespaces
avec `git pull --ff-only`. Les modifications faites directement dans Codespaces
s'affichent sans cette étape. Si les dépendances changent, exécuter aussi
`bash .devcontainer/setup.sh`, puis redémarrer le Codespace si nécessaire.

La configuration utilise Python 3.12, uv 0.12.19 et les versions de `uv.lock`.
Les scripts ne recréent pas les données et ne lancent pas de serveur supplémentaire
si PsychoMark est déjà prêt. Journaux : `artifacts/codespaces/server-8000.log`.
Pour relancer le serveur si nécessaire :

```bash
.venv/bin/python .devcontainer/start.py
```

Si le port 8000 est occupé par un autre service, le script le signale sans arrêter
ce service. Une modification de `.devcontainer/` nécessite **Rebuild Container**.
L'utilisation effective de Codespaces dépend des droits et du quota du compte
GitHub ; la présence de la configuration ne crée pas à elle seule un Codespace.

## Installation

Python 3.11 ou plus et [uv](https://docs.astral.sh/uv/) sont nécessaires.
Depuis la racine du dépôt :

```bash
uv sync --frozen --extra dev
.venv/bin/python -m psychomark --help
```

`uv.lock` fixe les versions des dépendances. OpenCV est installé en version
headless : aucun environnement graphique n'est nécessaire.

## Lancer l'interface web

```bash
cd /workspace/PsychoMark
uv sync --frozen --extra dev
.venv/bin/python -m psychomark.web --port 8000
```

Pour activer le rechargement pendant le développement hors Codespaces, ajouter
`--reload` à cette commande. Le mode normal n'injecte pas de script d'actualisation
et n'expose pas l'endpoint de suivi des sources.

Le serveur écoute en local sur le port 8000. Utiliser le navigateur de la machine
qui exécute le serveur, ou le mécanisme d'accès aux ports de son environnement
de développement. Le démarrage du serveur dans un environnement cloud ne rend
pas automatiquement son port accessible depuis un ordinateur personnel.
L'interface fonctionne sans compilation JavaScript et sans CDN.

Le bouton **Essayer la démonstration** crée un examen de 20 questions et analyse
une copie synthétique. Il présente 12 bonnes réponses, 2 absences de réponse et
6 cas à vérifier. Aucune note finale n'est affichée avant résolution de ces cas.

Parcours normal :

1. **Créer un examen** : nom, modèle, sections actives et questions (par exemple
   `1-20` ou `1-10, 15`).
2. **Renseigner le corrigé** avec les sélecteurs ou la saisie rapide d'une liste
   de réponses par section. Toutes les questions sélectionnées doivent avoir
   une bonne réponse avant l'enregistrement.
3. **Importer les copies** : une ou plusieurs images ou des PDF multipages.
   Chaque page devient une copie indépendante. Les erreurs de fichiers/pages
   sont présentées sans inventer de réponses.
4. **Consulter la correction** : bonnes réponses, erreurs, absences, cas à
   vérifier, résultats par section et images complète/annotée.
5. **Vérifier les ambiguïtés** sur l'extrait d'image sans annotation. Confirmer
   un choix, une absence ou une réponse multiple. Une réponse multiple confirmée
   compte comme incorrecte. On peut aussi rectifier une lecture automatique
   initialement jugée nette, ou rétablir la décision du moteur.
6. **Obtenir la note et exporter** la correction en CSV ou JSON.

Barème actuel : **1 point par bonne réponse, 0 sinon**, conversion en pourcentage
et note sur 20. Les questions non sélectionnées n'entrent pas dans le dénominateur.
Tant qu'il reste une question incertaine, multiple non confirmée ou illisible,
la note finale reste absente ; une fourchette de points et les réponses déjà
établies sont affichées. Ce n'est pas le score officiel du psychométrique.

Les examens, copies et historiques persistent après rechargement et redémarrage
dans `artifacts/web/`. Les données de chaque copie incluent une **photographie
du corrigé et de la géométrie au moment de l'import**. Modifier un examen affecte
les futurs imports ; les anciennes copies gardent leur version de corrigé.
Les décisions manuelles sont enregistrées à part, sans écraser la lecture du
moteur. Les modifications concurrentes périmées sont refusées.

Pour utiliser vos modèles calibrés ou un autre dossier de données :

```bash
.venv/bin/python -m psychomark.web \
  --template artifacts/private/ecole-v1.json \
  --template artifacts/private/autre-feuille-v1.json \
  --data-dir artifacts/private/web --port 8000
```

Sans `--template`, une feuille synthétique est générée au premier démarrage.
**Elle ne permet pas de lire arbitrairement une photo NITE ou Adar.** L'ajout et
la calibration de modèles restent des opérations en ligne de commande, décrites
plus bas. Le modèle disponible au moment de l'import doit correspondre à la copie.

L'application est un **prototype local pour un seul opérateur**, sans comptes
ni isolation entre organismes. Elle écoute par défaut sur `127.0.0.1` et ne doit
pas être exposée comme un SaaS public avec des données d'élèves. L'option `--host`
permet de choisir l'interface d'écoute pour un environnement de développement
maîtrisé. La durée de conservation et la suppression des données ne sont pas
encore gérées par l'interface. Conserver le dossier SQLite et ses images ensemble.

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
   Utiliser `examples/layout-eight-sections.json` pour comprendre le format,
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

## Vérification et organisation

```bash
.venv/bin/pytest -q
```

Les tests comparent les réponses à une vérité synthétique connue, vérifient les
rotations, la perspective, les marques multiples et traces faibles, les sélections
de questions, les mauvais modèles, le flou, le recadrage, les fichiers corrompus,
la lecture PDF multipage et la protection contre l'écrasement des résultats.
Ils ne mesurent pas les performances sur des copies d'élèves.

La suite couvre également la notation, l'upload HTTP/PDF, la persistance, les
versions de corrigé, la vérification manuelle et la protection contre les mises
à jour périmées, le mode développement et l'origine HTTPS de Codespaces.
**53 tests passent** dans l'environnement de développement.
Une dépréciation du client de test Starlette/httpx peut être affichée ; elle ne
concerne pas le serveur utilisé par le navigateur.

Un test de parcours réel Chromium est disponible séparément :

```bash
uv sync --frozen --extra dev --extra browser
# Si Chromium n'est pas installé sur la machine :
.venv/bin/python -m playwright install chromium
.venv/bin/python tests/browser_smoke.py
```

Le script utilise `/usr/bin/chromium` s'il est disponible, sinon celui installé
par Playwright. Il démarre son propre serveur avec une base temporaire, crée un
examen, saisit le corrigé, importe une copie, vérifie deux réponses et confirme
la note **12/20**, puis contrôle le rechargement, l'export CSV et le rendu mobile.
Il n'altère pas les examens de l'interface habituelle. Ses captures sont dans
`artifacts/browser/`. Le test s'arrête en cas d'erreur JavaScript ou de débordement
horizontal sur la page mobile contrôlée.

Le démarrage Codespaces et le rechargement peuvent aussi être vérifiés sans
créer de Codespace, après installation de l'extra `browser` :

```bash
.venv/bin/python tests/codespaces_smoke.py
```

Ce test démarre un serveur isolé, vérifie que le script est réexécutable sans
doublon, modifie temporairement des fichiers de contrôle, teste le rechargement
du navigateur et de Python, et confirme la conservation des saisies et des examens.
Il ne remplace pas une construction du conteneur et un premier lancement GitHub.

```text
src/psychomark/config.py        Modèles et validation des configurations
src/psychomark/calibration.py   Création des références et prévisualisations
src/psychomark/registration.py  Alignement contrôlé
src/psychomark/engine.py        Contrôles de qualité et lecture des réponses
src/psychomark/images.py        Chargement borné des images et PDF
src/psychomark/cli.py           Commandes et exports
src/psychomark/demo.py          Générateur synthétique reproductible
src/psychomark/grading.py       Corrigé, décisions humaines et notation
src/psychomark/store.py         Persistance SQLite et historique
src/psychomark/web.py           Serveur FastAPI, uploads et exports
src/psychomark/static/          Interface HTML/CSS/JavaScript en français
src/psychomark/development.py   Origine Codespaces et détection des changements
.devcontainer/                 Conteneur et démarrage automatique Codespaces
examples/                      Géométrie et examen de démonstration
tests/                         Tests du moteur et de la commande complète
```
