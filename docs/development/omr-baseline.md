# S01 — Référence de comparaison du moteur

[Plan hybride](../product/hybrid-omr-plan.md) · [Contrat de régions](../architecture/regions.md)

## Portée

L’outil de développement `psychomark.baseline` rejoue le moteur historique sur une
image, sans modifier ses seuils, sa lecture ni les notes. Il exporte les zones même
si un contrôle local refuse la lecture. Un échec d’alignement ne produit aucun faux
extrait associé à une question. Le rapport est privé et ne constitue pas une validation
terrain ni un écran de saisie : le parcours d’annotation interactif appartient à S02.

## Exécution par Codex ou un développeur

Commandes de référence, aucune action utilisateur nécessaire lorsqu’un agent effectue
la session. Exemple après avoir placé un diagnostic dans le dossier privé indiqué :

```bash
.venv/bin/python -m psychomark.baseline \
  artifacts/private/photo-diagnostic/copy.png \
  --template artifacts/private/photo-diagnostic/template.json \
  --compare artifacts/private/photo-diagnostic/result.json \
  --output artifacts/private/baselines/nouvelle-execution
```

`--exam` accepte une sélection existante de sections/questions ; sans option, toutes
les questions configurées sont attendues. `--compare` est facultatif et désigne une
extraction antérieure, jamais un corrigé. Les modèles, références et sélections passent
les validations habituelles du moteur. Une image par exécution ; pour un PDF, préparer
explicitement la page rasterisée avec son outil d’import, conserver l’original et le DPI.
Le chargement corrige l’orientation EXIF ; les coordonnées source concernent cette image décodée.

Le dossier de sortie doit être **nouveau**. Le code de sortie vaut 0 quand le rapport
est produit, même si la copie est refusée ; 2 pour une erreur d’exécution. `report.json`
est écrit en dernier, avec `complete=true`. Un dossier interrompu reste partiel et doit
être conservé ou supprimé explicitement ; le relancer nécessite un nouveau dossier.

## Livrables

| Fichier | Usage |
|---|---|
| `summary.md` | Résumé lisible : couverture, contrôles, limites et comparaison |
| `review.html` | Rapport local autonome, référence/photo/zones agrandies ; prédictions masquées dans des détails repliés |
| `result.json` | Extraction historique intacte, sans ajout de champs |
| `report.json` | Mesures, versions, empreintes des entrées, code Python, artefacts et durée de l’analyse |
| `template.json`, `selection.json` | Instantanés de la configuration utilisée |
| `regions.json`, `valid.png` | Géométrie et disponibilité des pixels, contrat séparé de l’extraction |
| `questions/NNNN/` | Extraits bruts, référence, zones, masques et images normalisées |
| `annotations.pending.json` | Liste complète des questions, champs humains vides ; aucune prédiction recopiée comme label |

Ouvrir `review.html` localement avec son dossier `questions/` conservé à côté. Aucune
requête externe, police distante ou serveur nécessaire. Les liens vers les fichiers
natifs permettent d’examiner la résolution réelle. Le zoom ×3 n’ajoute pas de détail.
Un navigateur géré peut interdire les fichiers locaux ; dans ce cas, un développeur
peut servir uniquement ce dossier sur localhost pour la vérification, puis arrêter
ce serveur. Le rapport ne nécessite aucun accès public.
L’export comporte aussi un aperçu de page susceptible de contenir des données d’identité :
garder **tout le dossier hors Git**, sous `artifacts/private/`, et dans une sauvegarde privée.
Le code peut être publié ; ces fichiers ne sont pas transmis au Codespace par Git.

L’exécution est retraçable par empreintes, mais le dossier n’archive pas les octets
des originaux ni l’environnement Python entier. Conserver aussi image, référence,
configuration initiale, code et verrou des dépendances pour rejouer le même cas ailleurs.
La durée mesurée couvre `Engine.analyze`, exclut initialisation et export ; elle n’est
ni un benchmark de charge ni une mesure de temps complet de correction.

## Mesures et comparaison

La couverture vaut `(single + blank) / toutes les questions attendues`, y compris
celles des pages rejetées. `multiple`, `uncertain` et `unreadable` comptent dans la revue.
Sans annotation validée, erreur automatique et précision restent absentes (`null`).
Une copie refusée ne devient donc jamais « 0 % d’erreur ».

La comparaison exige les mêmes empreintes de modèle/référence, la même sélection et
les mêmes identifiants de questions. Elle distingue changements de décision, scores
et diagnostics numériques. Une matrice peut varier par arrondi entre environnements :
les diagnostics sont comparés strictement, sans cacher ce fait.

L’identité de la source est vérifiée lorsqu’un `file_sha256` ou un rapport baseline
compagnon est disponible. Le compagnon doit correspondre à l’empreinte du résultat.
Pour un ancien diagnostic sans empreinte de source, le rapport indique explicitement
`unverified_no_source_fingerprint` : vérifier soi-même l’association du ZIP et de la photo.
Le résultat précédent sert à mesurer les changements, jamais à prouver leur exactitude.

## Validation et prochain lot

Les tests couvrent la conservation du résultat, les transformations inverses, les
sélections discontinues, cinq choix verticaux, les masques de grilles obliques, les pages
tronquées, les refus d’alignement, l’absence de faux labels et la comparaison des sources.

S02 ajoutera la saisie/reprise d’annotations humaines et les groupes de feuilles
physiques. S03 utilisera les coordonnées et les extraits pour mesurer les corrections
locales. Aucune observation visuelle de Codex ne remplace cette validation humaine.
