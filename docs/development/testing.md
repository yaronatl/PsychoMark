# Validation et fiabilité

[Documentation](../README.md)

## Vérifications reproductibles

```bash
.venv/bin/python scripts/dev.py check
# Une fois l'extra browser et Chromium installés :
.venv/bin/python scripts/dev.py browser
.venv/bin/python scripts/dev.py live
```

`check` exécute le lint Python, le contrôle de format, les liens de fichiers Markdown
et pytest. La CI exécute cette commande sur Python 3.11 et 3.12, puis les deux parcours
navigateur sur 3.12. Les résultats d'une session sont consignés dans la mémoire ;
les résultats distants se consultent dans GitHub Actions.

La suite pytest couvre la géométrie, les transformations, traces faibles et multiples,
le flou, les zones coupées, les fichiers corrompus, les PDF, les exports, la notation,
la persistance, les conflits de révision et l'origine Codespaces. Les fixtures sont
synthétiques. Un avertissement de dépréciation Starlette/httpx peut apparaître ; ne
pas le masquer globalement et traiter une future migration de dépendance séparément.

Le parcours navigateur crée un serveur et une base temporaires : examen, corrigé,
import, cas en attente, validation humaine, note 12/20, rechargement, CSV et largeur
mobile. Il exerce aussi l’import d’une feuille vierge, le placement des repères,
la sauvegarde/reprise, l’essai optique et un examen utilisant le nouveau modèle.
Les repères non sauvegardés protègent la navigation et le rechargement automatique.
Le parcours couvre aussi l’import d’exemples, la saisie/révision des observations,
la reprise, le conflit entre fenêtres, le cadrage manuel après échec d’alignement et
l’export privé. Un contexte Chromium avec `has_touch` exerce de vrais événements
tactiles synthétisés : tracé, déplacement, redimensionnement, annulation du geste,
défilement en mode photo, zoom à deux doigts, centrage, réglage fin d’un bord et butée
à un pixel, réemploi d’un cadre et double appui pendant une sauvegarde. La validation
après déplacement se fait dès le premier appui. Le cadrage est aussi ouvert à 320/390 px
et en paysage ; ces essais Chromium ne remplacent pas un essai Safari sur iPhone.
Les raccourcis clavier sont vérifiés hors des champs. Ce test n’est pas un essai sur
un téléphone physique ni une validation Safari/iOS. Les tests Python contrôlent les doublons, groupes et archives invalides.
Ses captures synthétiques vont dans `artifacts/browser/`. Il ne constitue
pas un audit complet d'accessibilité ou de compatibilité de tous les navigateurs.

Le parcours `live` vérifie le démarrage idempotent, la conservation des données, les
rechargements Python/CSS et la protection des saisies non enregistrées. Il écrit
temporairement deux fichiers de contrôle dans les sources, puis les retire. L'exécuter
séparément des autres vérifications, idéalement dans un checkout sans serveur de travail
en rechargement. Il ne remplace pas une construction Docker et une ouverture de Codespace.

## Évaluer le moteur sur de vraies copies

Le [rejeu S01](omr-baseline.md) et l’[outil d’annotation S02](../guides/annotations.md)
sont disponibles. La collecte humaine et l’évaluation indépendante restent à réaliser.

1. Constituer un corpus autorisé et identifier chaque modèle de feuille/version.
2. Établir une vérité de référence par vérification humaine. Conserver « indéterminable »
   lorsque l'image ne permet pas de conclure ; ne pas fabriquer une intention.
3. Séparer réglage et évaluation. Les photos ou variantes d'une même copie restent dans
   le même groupe pour éviter qu'une image quasi identique serve aux deux usages.
4. Couvrir scanners, téléphones, imprimantes, gommes, croix, contrastes et cadrages.
5. Mesurer les erreurs parmi les réponses automatiques, le taux de révision, les rejets,
   les copies entièrement exactes et la durée. Donner les effectifs et résultats par
   famille de défauts/modèle, pas uniquement une moyenne globale.
6. Garder un jeu de contrôle à part ; évaluer toute modification de seuil ou ajout d'IA
   avec la même procédure, sans utiliser le corrigé pour lire une marque.

Les seuils optiques ne sont pas des probabilités calibrées. Aucun seuil commercial
d'acceptation ni taux réel n'est annoncé avant ces mesures. Un gain d'automatisation
qui augmente les erreurs silencieuses doit être visible dans le bilan.

Le parcours `browser_annotation_flow.py` vérifie aussi le mode enchaîné : proposition
issue d’un cadre sauvegardé, chiffre + Entrée, AZERTY/pavé numérique, déplacement au
clavier, retour du focus depuis le cadrage, réponse non propagée, erreur réseau avec
reprise, touche Entrée maintenue, séparation des sections, préférences après rechargement
et deux appuis tactiles avec commandes persistantes. Toutes les données sont synthétiques.

Les tests [S04](photometric-trial.md) vérifient les effets sur les traits faibles et
colorés avec ombres/compression JPEG, une référence adaptée à une image réduite,
les contrôles de contraste avec repli, les pixels coupés et les grilles à cinq choix
verticaux. Ils contrôlent aussi que changer un label humain ne change ni les images
traitées ni les scores, que le résultat historique reste intact et que les rejets
gardent leurs dénominateurs. Les essais réels restent privés et exploratoires ;
le classement d’une marque ne constitue pas une mesure de précision des réponses.

Les tests [S05](classic-reader.md) exigent des décisions exactes sur les cas propres,
des abstentions sur les traces concurrentes et les pixels indisponibles, ainsi que
des lectures automatiques correctes sur une perspective avec ombres/JPEG. Ils
contrôlent 2/5/10 choix, l’absence de lien entre labels et décisions, et le comptage
des erreurs/abstentions sans exclure les rejets. La variante reste hors ligne ;
ses échecs sur les vraies copies sont conservés dans les rapports privés.

Les tests [S06](specialized-reader.md) vérifient séparation des acquisitions/groupes,
permission d’entraînement, revue de géométrie liée aux empreintes, intégrité des images
et poids, reproductibilité CPU et absence de fuite des labels de développement vers
l’apprentissage. Le lecteur ML exige l’extra `ml` ; son job CI distinct l’installe.
Un entraînement synthétique réussi vérifie le circuit, pas sa capacité sur les photos réelles.
