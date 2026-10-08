# État actuel

Mis à jour le 2026-10-09 (Asia/Jerusalem). Cette page décrit le dépôt, pas un déploiement garanti.

## Disponible

- Moteur OMR Python/OpenCV, CLI et interface FastAPI française. Examen configurable,
  corrigé, import, vérification humaine, notes brutes et exports ; SQLite et instantanés.
- Codespaces avec actualisation, documentation, ADR et commandes de qualité.
- Six skills de design installés ; Be UI accessible via le client `scripts/beui.py`.
- Première **proposition visuelle papier/encre implémentée** : accueil éditorial,
  espace de travail et correction harmonisés, responsive et navigation clavier.
- Renance reste la référence principale ; l’utilisateur a précisé une ambiance calme,
  chaude et claire, serif, papier/stylo/encre, évoquant reMarkable. Lire
  [la direction](../product/visual-direction.md), [DESIGN.md](../../DESIGN.md) et
  [le cadre UI](../product/ui.md) avant une modification visuelle.
- Torph demandé explicitement, installé en vanilla et utilisé pour le libellé d’analyse.
  Boutons Be UI **adaptés en CSS natif**, pas composants React officiels installés.
  Polices et module servis localement ; build/verrou npm et CSP à empreinte exacte.
- Accueil sur `/` ou `#/home` ; examens directement sur `#/exams`.
- Diagnostic des essais de feuille : motifs de refus en français, distinction entre
  alignement et contrôles locaux, export ZIP reproductible avec les images du seul essai.
  Présentation également disponible pour les anciens essais ; seuils du moteur inchangés.
- **Ajouter une feuille** sur `#/sheets` : import d’une référence vierge, cinq repères
  par grille, aperçu Python, essai d’une copie et modèle disponible pour les examens.
  [Guide](../guides/sheets.md), [ADR 0003](../architecture/decisions/0003-visual-sheet-library.md).
  Les brouillons sont sauvegardés après vérification ; les modèles enregistrés sont figés.
  La bibliothèque persiste sous le dossier privé de données, sans migration SQLite.

- S01 livré : [outil offline de comparaison](../development/omr-baseline.md), rapport HTML
  local, extraits, masques, provenance et [contrats](../architecture/regions.md). Aucun
  changement de décision optique.
- S02 livré : **Annotations** (`#/annotations`), import d’exemples, labels humains
  révisables, source/cadrage manuel après échec d’alignement, groupes et exports privés.
  [Guide](../guides/annotations.md), [ADR 0005](../architecture/decisions/0005-private-annotation-corpus.md).
  Export réel actualisé de 90 annotations reçu et vérifié ; utilisé pour préparer S06.
- Annotation mobile accélérée : numéros pour les réponses uniques, absence en un
  appui, cadre par glissement avec déplacement/redimensionnement, réemploi explicite
  du dernier cadre, alias retenu par onglet et bouton de sauvegarde fixe sur téléphone.
  Poignées déportées de 48 px, zoom à deux doigts, centrage et réglage par bord avec
  boutons de précision disponibles après le premier retour mobile.
  Réutilisation directement accessible : proposition décalée d’une largeur vers la
  droite/gauche, ou reprise au même endroit ; confirmation explicite conservée.
  Les ambiguïtés restent détaillées ; aucune confirmation ou marque n’est propagée.
  Mode enchaîné activable : cadre suivant proposé depuis la question précédente
  enregistrée, chiffre puis Entrée pour confirmer/enregistrer, flèches et C pour ajuster.
  Choix et confirmation fixes sur téléphone ; contexte de la photo visible.

- S03 expérimental hors ligne : [comparaison géométrique](../development/local-registration.md),
  recalage local borné sur cadres imprimés et variantes globales brut/normalisé.
  Sur l’export humain, normalisation avant ORB : centres des choix contenus dans
  40/40 cadres ; recalage local refusé sur les trois grilles serrées. Aucune précision
  de lecture mesurée ni activation dans l’application.

- S04 expérimental hors ligne : [comparaison photographique](../development/photometric-trial.md),
  sept variantes à géométrie fixe, différences appariées avec les observations humaines,
  masques et résidus consultables. Normalisation existante utile ; aucune variante
  supplémentaire ne montre un gain universel. Aucune activation web ni entraînement.

- S05 : [premier lecteur classique expérimental](../development/classic-reader.md),
  mesures d’encre et de continuité, contraste local sur original, décisions avec
  abstention et comparaison à géométrie identique. Tests synthétiques concluants,
  mais **aucun gain d’automatisation sur les 90 annotations réelles disponibles**.
  Les chiffres/contours imprimés restent problématiques ; aucune activation web.

- S06 : [premier circuit ML CPU hors ligne](../development/specialized-reader.md), préparation
  des 360 cases, revue de géométrie distincte, entraînement/export/inférence et
  comparaison case seule/référence. Poids entraînés sur synthétique uniquement :
  ils proposent tous les cas réels comme inexploitable, sans gain établi ni activation.

## Limites et choix ouverts

- Proposition graphique encore à apprécier par l’utilisateur ; aucun retour de validation
  du rendu final reçu. Ne pas confondre réalisation et identité approuvée.
- Aucun taux de précision réel annoncé ; validation synthétique et premier diagnostic
  photographique réel reproduit, sans correctif validé ni compatibilité NITE/Adar établie.
- Pas de SaaS public : ni comptes, ni isolation par entreprise, ni abonnement.
- Framework frontend général et bibliothèque UI restent à choisir. Torph n’impose
  aucune migration React/Tailwind. Voir [ADR 0002](../architecture/decisions/0002-local-browser-dependencies.md).
- Global Codex en lecture seule ; Be UI fonctionne via le client du projet.
- CI distante et rebuild complet Codespaces avec Node restent à vérifier. Installation
  et parcours testés dans cette machine ne prouvent pas le déploiement ailleurs.

## Reprise

**Demande actuelle : continuer S06 après réception des 90 annotations.**
GitHub est débloqué ; premier candidat S05 livré hors ligne, gain réel non établi.
L’export des 90 annotations est reçu, vérifié et rejoué avec S05. Il remplace le
précédent pour les prochaines évaluations, sans supprimer son historique.
Le [plan détaillé](../product/hybrid-omr-plan.md) découpe le travail en dix lots, avec
contrats, données, critères de passage et répartition des agents. L’orientation hybride
est soutenue par l’utilisateur ; le premier circuit ML S06 est désormais livré.
Voir [ADR 0004](../architecture/decisions/0004-hybrid-omr-experiment.md) et
[ADR 0006](../architecture/decisions/0006-offline-cpu-ml.md).

Consulter [la dernière session](sessions/2026-10-09-05-s06-prototype.md) et vérifier Git.
Branche actuelle : `feat/specialized-reader`, issue de `feat/classic-reader` (`01dc164`).
Cette branche contient S02, ses améliorations mobiles et S03 par ascendance.
Les candidats S03/S04/S05/S06 restent hors ligne ; aucune synchronisation Codespace ni
fusion `main` n’est impliquée par la publication. `api.github.com` est désormais
autorisé dans le réseau et son accès testé. La création automatique de la
[PR #1](https://github.com/yaronatl/PsychoMark/pull/1) a réussi. Le précédent refus
était un blocage réseau avant GitHub. La liste API des Codespaces n’a retourné aucun
Codespace de ce dépôt accessible à cette session ; les nouvelles annotations ne
sont pas récupérées automatiquement.
La [PR S05 #2](https://github.com/yaronatl/PsychoMark/pull/2) est ouverte en brouillon
sur la branche de #1 pour isoler les changements S05. Les deux PR restent non fusionnées.

Le diagnostic fourni reste dans `artifacts/private/photo-diagnostic/`, hors Git.
L’alignement réussit et la netteté passe. La résolution des cases et la correspondance
de deux cadres bloquent la lecture. Assouplir ces contrôles dans une expérience privée
ne donne que des réponses incertaines. Aucun correctif optique validé n’a été livré.
**L’utilisateur confirme que référence et photo proviennent de la même feuille.**
La différence de rendu ne prouve pas une autre version imprimée ; l’hypothèse antérieure
est non établie. Une meilleure photo aiderait les comparaisons, mais n’est pas un
prérequis pour commencer à améliorer le moteur avec le diagnostic déjà disponible.

S01 fournit désormais une commande de rejeu, les régions de 90 questions du diagnostic,
leurs masques et leur provenance. Les 90 refus historiques sont conservés. Rapport
privé : `artifacts/private/baselines/s01-photo-v1/summary.md` et `review.html` ; aucune
image réelle ajoutée à Git. Les labels préparés par S01 restent vides ; les 40 annotations
humaines reçues ensuite sont conservées dans un export S02 distinct. La précision de lecture reste non mesurée.

Lot en cours : **S06, adaptation aux données réelles**. Le premier prototype CPU est livré ;
les deux modèles entraînés sur synthétique échouent sur les cases réelles. Le premier candidat S05 est mesurable
mais ses seuils ne sont pas validés. S03 et S04 sont livrés comme expériences hors
ligne ; le recalage local des grilles serrées reste une limite ouverte.
Le premier export est conservé dans `artifacts/private/annotated-export-40/`, rapport S03 dans
`artifacts/private/baselines/s03-annotated-v2/`, rapports S04 dans
`artifacts/private/baselines/s04-annotated-export-40-v3/`, `s04-photo-diagnostic-v3/`
et `s04-monochrome-diagnostic-v3/`. Le nouvel export est dans
`artifacts/private/annotated-export-90/` : 59 questions simples, 29 blanches, 2 incertaines,
soit 299 cases vides, 59 marquées, 2 ambiguës. Les 40 premières annotations n’ont pas
changé ; 50 ont été ajoutées. Le nouvel export autorise l’entraînement
(`training_allowed=true`), mais reste en développement, sans validation des régions
individuelles de cases ni jeu indépendant. Aucun entraînement sur ces données réelles effectué.
Sa photo est identique au diagnostic monochrome
(empreinte vérifiée), donc il n’y a que deux photographies distinctes disponibles.
La normalisation améliore la séparation des signaux sur l’exemple annoté ; les
traitements supplémentaires ont des effets variables, pas de gain de lecture établi.
Les 50 nouvelles copies évoquées par l’utilisateur ne sont pas encore fournies.
Les rapports S05 sont dans `artifacts/private/baselines/s05-annotated-export-40-v3/`
et `s05-photo-diagnostic-v3/`. Le rapport actualisé est dans
`artifacts/private/baselines/s05-annotated-90-v1/` : 90/90 cadres contiennent les centres
des choix, mais les 90/90 questions restent en revue. Les prédictions n’ont pas changé ;
cela ne valide pas une précision. La préparation S06 peut utiliser la nouvelle
autorisation, en conservant l’acquisition entière dans un seul groupe et en vérifiant
les régions de cases avant entraînement.
La collecte peut commencer dans **Annotations → Ajouter une copie**, sans scripts.
Les deux diagnostics connus ont été importés dans un dossier de vérification privé
isolé, 90 questions chacun, aucune annotation humaine ni autorisation d’entraînement.
Le premier fournit 90 extraits proposés ; le second exige une lecture sur source ou
un cadrage manuel. Ce sont des cas de développement, pas un test final indépendant.
Le moteur optique et ses refus restent inchangés dans S02.

Second diagnostic disponible sous `artifacts/private/monochrome-diagnostic/`, rapport
historique sous `artifacts/private/baselines/s01-monochrome-v1/`. Référence inchangée,
photo différente. Refus global reproduit : repères cohérents concentrés sur 7,64 %
de la référence, seuil 12 %. Une normalisation avant ORB passe en expérience privée
les contrôles globaux et locaux, mais donne 76 `multiple` et 14 `uncertain` : aucune
lecture automatique validée. Ne pas présenter cette expérience comme un correctif actif.
S02 permet d’annoter la source lorsque le recalage historique échoue, sans
inventer des régions validées. Les deux cas sont du développement connu, pas un test final.

La normalisation locale d’éclairage existe déjà. Mesurer son apport avant de la modifier.
Le CNN ne reçoit jamais le corrigé ; ses sorties hors ligne sont toutes à revoir, sans effet sur
les notes. PyTorch CPU est installé via l’extra optionnel `ml`. Les jeux, revues, poids et
rapports S06 restent dans `artifacts/private/ml/` ; voir la dernière session pour les chemins.
La revue des coordonnées et l’entraînement sur des acquisitions réelles variées restent
à faire avant de passer à la calibration S07. Aucun résultat synthétique ne valide la photo.
L’écran S02 réutilise la direction papier/encre et les composants natifs. Les skills
frontend-design, Emil, Impeccable et UI UX Pro Max ont guidé la finition ; Be UI Button
a été consulté. Shadcn et Taste n’ont pas entraîné de migration React ou de refonte.
