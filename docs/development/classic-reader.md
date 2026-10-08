# S05 — Lecteur classique expérimental

[Plan hybride](../product/hybrid-omr-plan.md) · [S04](photometric-trial.md) ·
[Régions et observations](../architecture/regions.md)

## Statut et périmètre

`classic_reader.py` mesure les marques et propose des états avec abstention.
`reader_trial.py` compare le moteur historique, le lecteur historique après recalage
normalisé et ce candidat. Tout reste **hors ligne** : aucun appel depuis le web,
aucune modification de note, aucun entraînement ni accès au corrigé.

Cette première version apporte un protocole de comparaison et une protection contre
certaines traces faibles perdues par la normalisation. Elle ne débloque pas encore la
photo réelle annotée. Ses seuils sont exploratoires, pas des probabilités ni une
politique validée sur de nouvelles copies. Résultats dans la
[session S05](../memory/sessions/2026-10-09-03-s05-reader.md).

## Mesurer une case

1. Conserver le recalage global normalisé de S03/S04, sans déplacement vers les marques.
2. Dans l’intérieur elliptique historique, exclure l’encre de référence sous 200 et
   une marge d’un pixel référence autour. Refuser moins de 12 pixels de mesure ou
   moins de 25 % de l’intérieur restant : masquer davantage n’est pas prouver un blanc.
3. Estimer le papier local par le percentile 90 des pixels disponibles hors case,
   à une distance elliptique entre 1,2 et 1,6 rayon, sur du papier de référence >220.
   Refuser un contexte avec moins de 12 pixels de papier. Ces pixels fixes ne suivent
   pas l’encre ; ombres abruptes et traces hors case peuvent perturber l’estimation.
4. Mesurer un signal positif qui exige une différence avec la référence et un contraste
   avec le papier local. Mesurer couverture sombre, traces et plus grande composante
   connexe sombre, avec sa fraction de surface et son étendue relative à la case.
5. Vérifier aussi l’image grise originale : comparer les contrastes locaux source et
   référence, chacun ramené à une intensité papier 255 (plancher 40). Ce second signal
   peut révéler une trace que la normalisation de page a éclaircie. Il sert uniquement
   à demander une revue ; il n’annule jamais un autre indice.

L’exclusion imprimée peut retirer une marque située sur un chiffre. Un masque
insuffisant entraîne un refus, mais ce garde-fou ne détecte pas tous les traits qui
recouvrent exactement l’impression. Aucune hypothèse sur l’intention de l’élève.

## Décision provisoire

Une marque forte exige un contraste normalisé de 75 sur au moins 22 % des pixels,
une composante connexe d’au moins 8 % et une étendue d’au moins 35 % du diamètre sur
un axe. Une trace nécessite un signal de 20 sur au moins 4 % des pixels, dans l’une
des deux voies (normalisée ou originale locale).

- Plusieurs marques fortes : `multiple`, toujours en revue.
- Une marque forte : `single` seulement sans trace concurrente et avec au moins
  0,12 d’écart de couverture sombre face au concurrent ; sinon `uncertain`.
- Traces sans marque forte : `uncertain`.
- Aucun indice suffisant : `blank`, uniquement après les contrôles de qualité.
- Pixels, repérage, résolution, netteté ou support insuffisants : `unreadable`.

On ne choisit jamais automatiquement la case la plus sombre au détriment des autres.
Les 2 à 10 choix configurables et les axes de grille sont conservés. Tous les seuils
du moteur actif restent intacts. Le candidat réutilise les contrôles de section et
les refus de netteté/visibilité par case de `Engine.read_question` ; ses décisions
historiques `single/blank/multiple/uncertain` ne sont pas utilisées comme vérité.

## Rejeu par l’agent

```bash
.venv/bin/python -m psychomark.reader_trial \
  artifacts/private/annotated-export-40/source.png \
  --template artifacts/private/annotated-export-40/template.json \
  --manifest artifacts/private/annotated-export-40/manifest.json \
  --output artifacts/private/baselines/nouvel-essai-s05
```

Commande de référence ; aucune action utilisateur nécessaire lorsque l’agent effectue
la session. Le manifeste est facultatif, mais seul `development` est accepté s’il
est fourni. Identité des fichiers et observations sont validées par les contrats
S03/S04. Les labels sont consultés pour l’évaluation après les décisions, jamais
comme paramètres du lecteur. Une annotation manquante ne devient pas un blanc.

Le dossier doit être nouveau. Code 0 signifie un rapport terminé, y compris pour
une photo refusée ; code 2 signifie une erreur d’exécution. `report.json` est écrit
en dernier avec `complete=true`. Les entrées et annotations ne sont pas modifiées.

## Comparaison et artefacts

Trois variantes isolent le repérage de la lecture : `historical` intact,
`normalized_legacy` à géométrie normalisée, et `classic_v1` à cette même géométrie.
L’évaluation historique utilise sa propre géométrie, jamais celle du candidat.

Les `single` et `blank` comptent comme décisions automatiques expérimentales. Une
décision automatique face à une observation humaine ambiguë est une erreur, même
si le choix paraît plausible. Les décisions à géométrie humaine non vérifiable sont
comptées séparément et jamais créditées correctes. Les refus restent dans le
dénominateur de couverture. Le taux d’erreur est conditionnel aux décisions
automatiques comparables ; **il reste absent (`null`) lorsqu’il n’y en a
aucune**, et non à zéro. Les états prédits par statut humain rendent visibles les
faux `multiple` ou `uncertain`, même s’ils ne déclenchent pas une réponse automatique.

Les changements appariés indiquent erreurs automatiques ajoutées/retirées et passages
entre bonne réponse automatique et revue. Les effectifs, couverture et revue doivent
toujours accompagner l’erreur ; un lecteur refusant tout n’est pas validé comme fiable.
Les conditions de prise de vue ne sont pas inventées à partir des pixels : les
essais synthétiques couvrent des défauts nommés, les cas réels restent deux acquisitions
connues, dont une seule annotée ici. Aucun jeu de test indépendant.

`report.json` conserve paramètres, versions, empreintes, qualité et mesures.
`historical-result.json` reste identique au résultat du moteur actif. `regions.json`
décrit la géométrie candidate. La galerie privée conserve référence, photo originale
recalée, image normalisée et masque utilisé ; un masque nul après refus veut dire
« pas de mesure », pas « réponse vide ». En échec global, aucun crop n’est inventé.

`summary.md` et `review.html` permettent la revue locale sans requête externe. Conserver
les originaux séparément pour reproduction ; ni ces images, ni les annotations, ni
les rapports privés ne vont dans Git. Les données ne sont pas copiées au Codespace
par la publication d’une branche.

## Prochaine étape

Les chiffres et anneaux de la photocopie réelle restent une source majeure de faux
indices de marque. Le candidat n’est pas prêt à être activé. S06 peut construire le
prototype ML comparatif, puis S07 calibrera l’abstention sur des données séparées.
Les nouveaux exports humains et des copies variées sont utiles ; une seule photo
avec davantage de questions ne démontre pas la généralisation. L’export actuellement
reçu doit préciser l’autorisation d’entraînement ; ce droit ne valide pas à lui seul
les coordonnées des cases ni la séparation des groupes. Aucun entraînement n’est
effectué par S05. La [réception des 90 annotations](../memory/sessions/2026-10-09-04-corpus-90.md)
documente le dernier état des données et leur rejeu.
