# S04 — Comparaison photographique contrôlée

[Plan hybride](../product/hybrid-omr-plan.md) · [Géométrie S03](local-registration.md) ·
[Contrats de régions](../architecture/regions.md)

## Portée

Implémenté : `photometry.py` prépare des paires référence/photo ;
`photometric_trial.py` les compare hors ligne. Ni entraînement, ni décision de réponse,
ni modification du moteur actif ou des notes. Le corrigé n’entre jamais dans ces modules.

Le but est de distinguer une différence d’éclairage ou d’impression d’une marque ajoutée.
Un traitement peut réduire les différences sur les cases vides **et** affaiblir des
traits utiles. Le rapport expose les deux, sans choisir automatiquement un gagnant.

## Expérience reproductible

Commande de référence pour l’agent ou un développeur ; aucune action utilisateur
nécessaire pendant la livraison de S04 :

```bash
.venv/bin/python -m psychomark.photometric_trial \
  artifacts/private/annotated-export-40/source.png \
  --template artifacts/private/annotated-export-40/template.json \
  --manifest artifacts/private/annotated-export-40/manifest.json \
  --output artifacts/private/baselines/nouvel-essai-s04
```

Le manifeste est facultatif. Lorsqu’il est fourni, ses empreintes, dimensions,
identifiants, choix et observations sont vérifiés. Seul le groupe `development`
est accepté ; cet outil ne doit pas servir à régler les traitements sur le jeu réservé.
`training_allowed=false` est compatible avec cette évaluation sans apprentissage.
Les fichiers d’entrée et annotations ne sont jamais modifiés.

Le dossier de sortie doit être nouveau. Code de sortie 0 : rapport terminé, même si
le repérage échoue ; code 2 : erreur d’exécution. `report.json` est écrit en dernier
avec `complete=true`. Un dossier interrompu n’est pas un rapport valide.

### Ce qui reste fixe

- Un seul recalage global candidat, avec la normalisation existante **avant ORB**,
  comme dans S03. Les garde-fous géométriques existants restent actifs. Pas de recalage
  local ajouté : S03 ne fournit pas encore de correction acceptée sur les grilles réelles serrées.
- La photo couleur originale est projetée une seule fois pour toutes les variantes.
  Les coordonnées et dimensions source restent disponibles dans `regions.json`.
- Le masque de mesure est identique : intérieur elliptique historique et pixels
  de la référence normalisée originale supérieurs à 200. On ne change pas les pixels
  mesurés pour favoriser un traitement. Les anneaux et chiffres peuvent néanmoins
  laisser des résidus après impression ou décalage ; S05 devra en tenir compte.
- Un masque de présence rejette les pixels partiellement fournis par le bord lors
  de l’interpolation bilinéaire. Ce masque ne certifie ni netteté ni bon positionnement.
  La normalisation de la page reste sensible au voisinage, notamment près d’un bord coupé.
- Les labels et cadres humains interviennent seulement dans la comparaison finale,
  après les traitements. Ils ne guident ni le recalage ni le contraste.

### Variantes figées

| Variante | Différence par rapport à `normalized` |
|---|---|
| `raw_gray` | Aucune correction d’éclairage ; témoin en niveaux de gris |
| `normalized` | Normalisation historique de la page entière : estimation du papier, sigma 25 px, plancher 40 |
| `min_channel` | Canal BGR minimum avant normalisation ; conserve l’encre colorée mais peut renforcer l’impression et le bruit |
| `reference_contrast` | Ajustement affine de l’intensité de la **référence**, séparément par grille, sur l’impression hors cases |
| `reference_resolution` | Référence projetée vers la grille de pixels source puis retour en référence, interpolation bilinéaire |
| `reference_blur` | Flou gaussien de sigma 0,8 pixel référence sur la référence seulement, avant normalisation |
| `combined` | Résolution + flou + contraste de référence ; les replis sont indiqués par grille |

Ce sont des ablations prédéfinies, pas une recherche des paramètres donnant le meilleur
résultat sur les labels. Les paramètres et versions sont enregistrés dans le rapport.
Le traitement couleur ne supprime aucun canal choisi comme « couleur d’impression ».
Il n’y a ni super-résolution générative, ni débruitage inventant une marque.

Le rapprochement de résolution simule uniquement l’échantillonnage selon l’homographie.
Il ne connaît pas le flou réel du téléphone, le photocopieur ou sa compression. Deux
rééchantillonnages de la **référence** sont intentionnels ; aucun détail source n’est créé.

### Ajustement de contraste contrôlé

La zone de contrôle couvre la grille imprimée, en excluant toutes les cases et une
marge de 4 pixels référence. Des tuiles alternées de 8 pixels séparent ajustement et
vérification. Le modèle affine référence→photo utilise des médianes dans des classes
d’intensité de largeur 32, chacune avec au moins 16 pixels : le papier blanc ne doit
pas masquer entièrement l’encre dans l’ajustement.

Rejet si moins de 160 pixels par partition, étendue de contraste sous 40, pente hors
0,35–2,5, décalage hors −100–100, erreur moyenne absolue de vérification au-dessus de
35 ou régression supérieure à 0,5 niveau. Ces seuils sont des garde-fous expérimentaux
en unités d’intensité 8 bits, pas des probabilités. En cas de rejet, la référence
d’avant ajustement est conservée et le motif est enregistré.

Seuls les pixels de contrôle alimentent cet ajustement. La normalisation d’éclairage
préalable utilise toutefois le voisinage de la page entière : son indépendance des
marques n’est pas parfaite. Une écriture hors cases peut également contaminer les
contrôles. Les tuiles réservées à la vérification ne sont pas un jeu de test indépendant.

## Mesures et limites

Pour chaque choix, le résidu positif moyen est `moyenne(max(référence − photo, 0))`
sur le masque fixe, en niveaux 0–255. Le résidu signé est aussi conservé. Aucune
couverture seuilée ni règle « prendre le plus sombre » ne produit une réponse.

Avec annotations : distributions séparées `empty`, `marked`, `ambiguous`, `unreadable`,
comptage des questions humaines simples/blanches/multiples/incertaines/illisibles,
différences appariées face à `normalized`. Pour les seules réponses humaines uniques,
le rapport indique l’écart entre le choix marqué et le concurrent au signal le plus fort,
et les améliorations/régressions de ce classement. Un classement correct ne sait pas
reconnaître les blancs ou les doubles marques ; **`answer_accuracy` reste nul**.

Une question n’est comparable aux labels que si son cadre manuel est confirmé,
tous les centres projetés sont dedans et tous les pixels de mesure sont disponibles.
Les exclusions gardent leur motif et leur dénominateur. Une annotation absente n’est
jamais une réponse blanche ; une page refusée n’est jamais « sans erreur ».
La contenance des centres ne prouve pas la précision des contours des cases.

Les contrôles historiques de qualité sont conservés à géométrie fixe et le résultat
historique complet est exporté séparément. Les mesures S04 restent exploratoires même
sur une région refusée par ces contrôles ; elles n’autorisent jamais sa lecture en production.

## Artefacts privés

- `report.json` : matrices/diagnostics, paramètres, versions, empreintes des entrées,
  du code et des artefacts, observations et comparaisons par variante.
- `historical-result.json` : résultat du moteur actif inchangé.
- `regions.json`, `valid.png`, `template.json` : géométrie et configuration utilisées.
  Les régions et images sont absentes si le repérage échoue.
- `questions/NNNN/` : extraits couleur originaux recalés, masque de mesure commun,
  références/photos traitées, résidus et masques de validité par variante.
- `summary.md`, `review.html` : résultats, replis et galerie locale sans accès réseau.

Tout le dossier reste sous `artifacts/private/`, hors Git. Les originaux ne sont pas
archivés intégralement dans le rapport : conserver aussi les entrées, le code et le
verrou de dépendances. Une empreinte ne remplace pas le fichier original.

## Suite

Les résultats datés sont dans la [session S04](../memory/sessions/2026-10-09-02-s04-photometry.md).
S05 doit travailler sur la lecture des marques et les décisions avec abstention,
notamment les résidus présents dans les cases vides. Aucune des variantes S04 n’est
promue par défaut dans l’application. Les nouvelles copies variées permettront de
confirmer ou de contredire les observations faites sur les deux photographies connues.
