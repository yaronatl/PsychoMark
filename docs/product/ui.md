# Cadre de l'interface et décisions visuelles

[Documentation](../README.md)

**La direction visuelle, les outils de design et la bibliothèque UI seront choisis
par l'utilisateur.** Aucune décision React, Vue, Tailwind, shadcn ou autre n'est prise.
La présence de HTML/CSS/JS natifs décrit le prototype, pas le futur design system.

## Ce qui existe

L'interface provisoire réside dans [static/](../../src/psychomark/static/).
`app.js` gère les vues et événements, `style.css` les styles, `index.html` la structure,
`live.js` le rafraîchissement en développement. Ce ne sont pas des composants d'une
bibliothèque UI réutilisable. Les styles comportent déjà quelques variables CSS,
sans catalogue de tokens ou de composants validé.

| Élément fonctionnel | Comportement à conserver pendant une refonte |
|---|---|
| Liste et éditeur d'examens | Modèle choisi, sections et questions explicites, corrigé complet |
| Import de copies | Indiquer traitement en cours, erreurs de fichier/page et résultats |
| Tableau de correction | Distinguer lecture automatique, décision humaine et bonne réponse |
| Panneau de vérification | Voir la zone d'origine, choisir, confirmer ou revenir à l'automatique |
| Résumé de note | Afficher une note provisoire tant que des réponses restent en attente |
| Historique et exports | Conserver la traçabilité et permettre de récupérer les résultats |

## À préparer après le choix de l'utilisateur

Consigner la référence de design et la bibliothèque retenue dans un ADR, puis définir
les couleurs, espacements, typographie, états et composants avec cette bibliothèque.
Prévoir les états vide, chargement, succès, erreur, conflit et ambiguïté dès chaque vue.
La couleur seule ne doit pas porter un statut ; conserver labels, focus visible et
utilisation au clavier. Tester les parcours desktop/mobile et les textes français.

Un catalogue visuel et des outils comme Storybook pourront être évalués à ce moment-là.
Ne pas installer un outillage frontend complet avant que ce choix ait été exprimé.
