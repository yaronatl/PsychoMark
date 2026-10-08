# Cadre de l’interface et décisions visuelles

[Documentation](../README.md) · [Direction visuelle](visual-direction.md) · [Système implémenté](../../DESIGN.md)

L’utilisateur dirige la partie visuelle. Il a autorisé une première refonte dans un
univers calme de papier et d’encre, avec Renance comme inspiration principale et
reMarkable comme référence d’ambiance. **Cette première proposition est implémentée,
mais son rendu reste à valider ensemble.** La stack frontend future n’est pas décidée.

## Ce qui existe

L’interface est servie par FastAPI, en HTML/CSS/JavaScript natifs, sans nouvelle chaîne
de compilation. Les [skills installés](../development/design-tools.md) guident le
travail. L’utilisateur a aussi demandé **Torph**, installé pour la transition du
libellé des boutons de démonstration pendant l’analyse. Les composants React de
shadcn/Be UI ne sont pas intégrés : le comportement de pression du Button Be UI
est adapté en CSS natif avec une amplitude réduite. Cette adaptation n’est pas une
installation du composant React officiel.

| Source | Responsabilité |
|---|---|
| [index.html](../../src/psychomark/static/index.html) | Structure, navigation de l’atelier, chargement des assets locaux |
| [landing.js](../../src/psychomark/static/landing.js) | Présentation éditoriale et scène illustrative, sans logique de notation |
| [app.js](../../src/psychomark/static/app.js) | Routes, vues de travail, formulaires et appels API |
| [sheets.js](../../src/psychomark/static/sheets.js) et [sheets.css](../../src/psychomark/static/sheets.css) | Bibliothèque de feuilles, placement manuel des grilles et essais |
| [style.css](../../src/psychomark/static/style.css) | Tokens partagés, composants natifs, atelier, accueil et adaptation mobile |
| [live.js](../../src/psychomark/static/live.js) | Rafraîchissement du navigateur en développement |
| [motion.js](../../src/psychomark/static/motion.js) | Libellé d’analyse animé avec Torph, réduction du mouvement et nettoyage |
| [DESIGN.md](../../DESIGN.md) | Description du système réellement construit, à préserver lors des évolutions |

`/` et `#/home` ouvrent la présentation. `#/exams` ouvre directement les examens.
Les liens existants vers un examen ou une copie conservent leur fonctionnement.
La démonstration utilise l’API existante et crée une copie synthétique à vérifier.

## Comportements à conserver

| Surface | Invariant |
|---|---|
| Liste et éditeur | Modèle choisi, sections/questions explicites, corrigé complet |
| Import | Traitement en cours, erreurs de fichier/page et résultats |
| Correction | Lecture automatique, décision humaine et réponse attendue distinctes |
| Vérification | Extrait original, confirmer ou rétablir l’automatique |
| Note | Provisoire tant que des réponses restent en attente |
| Historique et exports | Traçabilité et récupération des résultats |

Les scans restent sur un fond blanc, sans filtre. Les statuts sont exprimés en texte
et en couleur. Conserver les labels de champs, le focus clavier visible, les états
vide/chargement/erreur et la réduction de mouvement. Tester les textes français et
l’absence de débordement sur téléphone.

## Choix futurs

React, Tailwind, shadcn ou toute autre migration nécessitent un choix explicite de
l’utilisateur et un ADR. Le catalogue de composants, un éventuel Storybook et un
outillage frontend complet pourront être définis à ce moment. Installer les skills
n’équivaut pas à choisir cette stack.
