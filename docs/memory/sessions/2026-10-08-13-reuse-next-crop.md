# Session 2026-10-08-13 — Réutiliser le cadre pour la question suivante

Demande : remettre le bouton de réemploi à portée de main et proposer la question
suivante en décalant le cadre de sa largeur. Branche `feat/annotation-corpus`, départ
`96ab1e4`. Aucun changement de moteur ou de stockage.

## Comportement

Bouton **Réutiliser l’ancien cadre** visible au-dessus de la photo. Le menu propose
À droite par défaut, Même endroit ou À gauche. Le déplacement utilise exactement la
largeur du dernier cadre appliqué sur cette acquisition, en pixels source. Le zoom
n’intervient pas ; taille et position verticale sont conservées. Le cadre proposé
est centré, ajustable et soumis à **Utiliser ce cadre**, puis à l’enregistrement habituel.
Aucune marque ni annotation n’est propagée.

Les appuis répétés repartent du même cadre précédent. Un dépassement de l’image
conserve le brouillon et invite à reprendre au même endroit. Pas de changement de
ligne/section deviné, pas de compensation automatique des espaces entre questions.
Bouton désactivé sans cadre précédent. Une saisie numérique non appliquée ou un geste
en cours bloque le réemploi pour éviter de les écraser. Annuler abandonne la proposition.

## Interface et validation

Guide Emil consulté pour la continuité des interactions natives, sans animation sur
cette action répétitive. Palette papier/encre inchangée.

| Before | After | Why |
|---|---|---|
| Réemploi caché dans les options | Bouton visible au-dessus de la photo | Accès direct sur téléphone |
| Cadre repris au même endroit uniquement | Décalage d’une largeur ou même endroit | Préparer la question voisine sans retracer |

Tests navigateur : décalage exact, double appui sans cumul, dépassement refusé,
reprise au même endroit, annulation et bouton désactivé sans précédent ; parcours
complet et affichage 320/390 px et paysage : réussi. Inspection de la capture mobile
réussie. `scripts/dev.py check` : Ruff, format, liens et 89 tests réussis ; avertissement
Starlette/httpx préexistant.
Les données et captures sont synthétiques. Aucun téléphone physique/Safari testé.

Guide d’annotation et mémoire mis à jour. Publication GitHub ne synchronise pas le
Codespace distinct ; l’accès distant à celui-ci a renvoyé Forbidden dans cette discussion.
