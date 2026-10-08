# État actuel

Mis à jour le 2026-10-08 (Asia/Jerusalem). Cette page décrit le dépôt, pas un déploiement garanti.

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
  Collecte réelle et ML restent à faire.
- Annotation mobile accélérée : numéros pour les réponses uniques, absence en un
  appui, cadre par glissement avec déplacement/redimensionnement, réemploi explicite
  du dernier cadre, alias retenu par onglet et bouton de sauvegarde fixe sur téléphone.
  Poignées déportées de 48 px, zoom à deux doigts, centrage et réglage par bord avec
  boutons de précision disponibles après le premier retour mobile.
  Les ambiguïtés restent détaillées ; aucune confirmation ou marque n’est propagée.

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

**Demande actuelle : accélérer l’annotation, en priorité sur mobile.**
Le [plan détaillé](../product/hybrid-omr-plan.md) découpe le travail en dix lots, avec
contrats, données, critères de passage et répartition des agents. L’orientation hybride
est soutenue par l’utilisateur ; S01 et l’outillage S02 sont implémentés, aucune implémentation ML
n’a commencé. Voir [ADR 0004](../architecture/decisions/0004-hybrid-omr-experiment.md).

Consulter [la dernière session](sessions/2026-10-08-12-touch-crop-precision.md) et vérifier Git.
Branche : `feat/annotation-corpus` (S02 initial : `48715cf`, puis adaptation mobile), issue de
`docs/monochrome-findings` (`dfaa622`). Les changements précédents sont inclus par
ascendance. Publier cette branche ne synchronise pas le Codespace distinct et ne
prouve pas une fusion dans `main`. La création de PR par l’API GitHub reste refusée
(`Forbidden`) ; aucune PR créée pour S02.

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
image réelle ajoutée à Git. Les labels humains sont vides, la précision reste non mesurée.

Prochain lot : **S03, recalage local**, puis comparaison des traitements S04.
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
Le futur modèle ne reçoit jamais le corrigé et démarre en observation, sans effet sur
les notes. PyTorch est seulement proposé pour S06, aucune dépendance ML installée.
L’écran S02 réutilise la direction papier/encre et les composants natifs. Les skills
frontend-design, Emil, Impeccable et UI UX Pro Max ont guidé la finition ; Be UI Button
a été consulté. Shadcn et Taste n’ont pas entraîné de migration React ou de refonte.
