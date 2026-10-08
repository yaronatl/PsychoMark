---
name: PsychoMark
description: Un atelier de correction calme, entre papier et encre.
colors:
  paper: '#f7f5ef'
  surface: '#fffefa'
  ink: '#292e29'
  muted: '#64685e'
  line: '#dbded3'
  accent: '#303b32'
  sage: '#e5e9df'
  green: '#365d43'
  green-bg: '#eaf0e7'
  amber: '#79521d'
  amber-bg: '#f6ecd8'
  red: '#944838'
  red-bg: '#f7eae4'
  primary-hover: '#475440'
  control-line: '#b4bdab'
  disabled-bg: '#eeeee7'
typography:
  display:
    fontFamily: '"Instrument Serif", Georgia, serif'
    fontSize: clamp(58px, 7.4vw, 96px)
    fontWeight: 400
    lineHeight: 0.99
    letterSpacing: -.026em
  headline:
    fontFamily: '"Instrument Serif", Georgia, serif'
    fontSize: clamp(38px, 4vw, 54px)
    fontWeight: 400
    lineHeight: 1.05
    letterSpacing: -.025em
  title:
    fontFamily: '"Geist", sans-serif'
    fontSize: 18px
    fontWeight: 550
    lineHeight: 1.4
  body:
    fontFamily: '"Geist", sans-serif'
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: '"Geist", sans-serif'
    fontSize: 13px
    fontWeight: 500
    lineHeight: 1.5
rounded:
  badge: 4px
  field: 6px
  button: 7px
  notice: 8px
  preview: 10px
  surface: 12px
  scene: 14px
spacing:
  compact: 8px
  control-gap: 10px
  small: 12px
  medium: 16px
  large: 24px
  section: 36px
  workspace-gutter: 40px
components:
  button-primary:
    backgroundColor: '{colors.accent}'
    textColor: '{colors.surface}'
    typography: '{typography.label}'
    rounded: '{rounded.button}'
    padding: 10px 18px
  button-primary-hover:
    backgroundColor: '{colors.primary-hover}'
  button-secondary:
    backgroundColor: transparent
    textColor: '{colors.ink}'
    typography: '{typography.label}'
    rounded: '{rounded.button}'
    padding: 10px 18px
  button-ghost:
    backgroundColor: transparent
    textColor: '{colors.ink}'
    typography: '{typography.label}'
    rounded: '{rounded.button}'
    padding: 10px 18px
  button-text:
    backgroundColor: transparent
    textColor: '{colors.ink}'
    padding: 10px 0
  input:
    backgroundColor: '{colors.surface}'
    textColor: '{colors.ink}'
    rounded: '{rounded.field}'
    padding: 10px 12px
  navigation-item:
    textColor: '{colors.muted}'
    rounded: '{rounded.button}'
    padding: 10px 12px
  badge-amber:
    backgroundColor: '{colors.amber-bg}'
    textColor: '{colors.amber}'
    rounded: '{rounded.badge}'
    padding: 4px 9px
  card:
    backgroundColor: '{colors.surface}'
    rounded: '{rounded.surface}'
    padding: 24px
  choice:
    backgroundColor: '{colors.surface}'
    textColor: '{colors.ink}'
    rounded: '{rounded.field}'
    width: 44px
    height: 44px
---

# Design System: PsychoMark

## Overview

**Creative North Star: "L’atelier papier et encre"**

L’atelier papier et encre traduit la direction exprimée : calme, chaleureuse, douce et claire, avec une serif travaillée et le caractère d’une papeterie au service d’un outil moderne. Renance est la référence principale ; reMarkable est une référence d’ambiance citée par l’utilisateur. Les couleurs et fontes ci-dessus décrivent la première proposition implémentée ; elles sont normatives pour sa continuité, mais leur rendu n’a pas encore été approuvé par l’utilisateur.

L’accueil a une respiration éditoriale, un titre centré et une scène tangible de feuille et de correction. Les vues de travail sont plus compactes : lignes, formulaires et tableaux font place à la lecture et à la décision humaine. Cette composition appartient à l’accueil ; elle n’impose pas un grand hero aux autres écrans. Le système est extrait du HTML, du CSS et des modules JavaScript existants, sans composition graphique préalablement approuvée.

**Key Characteristics:**

- Papier ivoire, encre végétale et surfaces claires.
- Titres serif expressifs ; commandes, tableaux et chiffres en sans-serif.
- États explicitement libellés et images originales préservées.
- Relief réservé aux objets illustrés et aux messages temporaires.

Sources : `src/psychomark/static/style.css`, `index.html`, `landing.js`, `app.js` et `motion.js` ; contexte dans `PRODUCT.md`, `docs/product/visual-direction.md` et `docs/product/ui.md`. Les jetons du frontmatter décrivent le code ; les rampes du sidecar sont des aides de visualisation synthétiques, pas des couleurs supplémentaires implémentées.

## Colors

Une palette de papeterie claire, tempérée par l’encre végétale et des tons de sauge.

### Primary

- **Encre végétale** (`accent`) : actions primaires, choix retenus, navigation et focus.
- **Encre au survol** (`primary-hover`) : éclaircissement du bouton primaire.

### Secondary

- **Sauge claire** (`sage`) : état informatif et parenté tonale avec la scène de papier. Ce support n’est pas une seconde couleur d’action.
- **Vert de correction** (`green`, `green-bg`), **ambre de vérification** (`amber`, `amber-bg`) et **terre d’erreur** (`red`, `red-bg`) : couples texte/fond sémantiques. Le sens est toujours porté aussi par un libellé.

### Neutral

- **Papier ivoire** (`paper`) : fond de page.
- **Feuille claire** (`surface`) : cartes, champs et texte des commandes sombres.
- **Encre de lecture** (`ink`) : contenu principal ; **crayon secondaire** (`muted`) : aides et métadonnées.
- **Trait de séparation** (`line`) : tableaux et surfaces ; **trait de contrôle** (`control-line`) : champs et choix.
- **Papier désactivé** (`disabled-bg`) : champs désactivés et badge neutre.

**The Encre utile Rule.** Réserver l’accent sombre aux actions, aux choix et à la navigation ; les états de correction gardent leur sens et leur libellé.

## Typography

**Display Font:** Instrument Serif, repli Georgia puis serif.
**Body Font:** Geist, repli sans-serif. Il n’existe pas de police monospace distincte.

Les deux fontes sont auto-hébergées dans les assets avec leurs licences, avec `font-display: swap`. Instrument Serif est utilisée en romain normal ; Geist est variable. La chaleur vient des grandes formes de la serif et de l’espace, tandis que la sans-serif facilite le travail de lecture.

### Hierarchy

- **Display** : grand titre centré d’accueil, selon le jeton `display`. À 580 px et moins, taille `clamp(43px, 11.8vw, 68px)` et interligne (1.04).
- **Headline** : titre principal des vues de travail, selon `headline`. Les titres des sections éditoriales reprennent cette taille avec un interligne (1.06). Sur téléphone, le titre de travail passe à (38 px), les titres de présentation à (40 px), puis celui de fermeture à (34 px).
- **Title** : titres utilitaires de section, selon `title`. Le sous-titre de travail est en Geist (15 px, graisse 550).
- **Body** : texte par défaut selon `body`, soit un corps réel de (14 px), pas une taille de titre. La présentation utilise (15 px / 1.75), puis (13 px / 1.75) sur téléphone. Les descriptions de page sont limitées à (64 ch).
- **Label** : commandes selon `label`. Les aides descendent à (12 px), les métadonnées et badges à (11 px). Les petits caractères dessinés sur la feuille illustrative ne constituent pas une échelle de texte fonctionnel.
- **Chiffres** : chiffres tabulaires dans les tableaux et les statistiques ; ces dernières utilisent (34 px / 1.3), graisse 400.

**The Deux écritures Rule.** La serif porte les titres éditoriaux ; Geist porte les instructions, les réponses et les chiffres.

## Layout

L’accueil occupe un conteneur centré limité à (1360 px), avec des marges intérieures horizontales de (56 px). Le titre ouvre la page, suivi de la scène papier/écran et de trois étapes séparées par des traits. L’espace de travail dispose d’une barre latérale fixe de (232 px) et d’un contenu limité à (1460 px), avec des marges intérieures de (46 px 40 px). Les espacements récurrents sont extraits dans le frontmatter ; il n’existe pas de grille abstraite supplémentaire à imposer.

La correction partage l’espace entre un tableau flexible et un panneau de (300 px), avec un écart de (24 px). Ce panneau est fixe au défilement à partir de (24 px) du haut ; au-delà de (1700 px), il atteint (350 px). Les formulaires utilisent deux colonnes ; les réponses du corrigé emploient une grille automatique de colonnes d’au moins (86 px).

- À (1100 px) et moins : barre latérale réduite à (210 px), correction en une colonne et panneau dans le flux. La sélection d’une question amène le focus au panneau ; « Retour aux questions » restitue le focus à la question sélectionnée. Les statistiques de copie passent à deux colonnes.
- À (800 px) et moins : navigation en bande horizontale au-dessus du travail ; retrait de la marge latérale du contenu. La scène se resserre et les détails secondaires des étapes sont masqués.
- À (580 px) et moins : formulaires et actions se réorganisent verticalement, statistiques générales en lignes, marges de travail de (18 px) et d’accueil de (20 px). La scène empile la feuille et le panneau ; son libellé illustratif reste visible. Les tableaux sont contenus dans une zone de défilement horizontal.

## Elevation & Depth

Le travail repose sur des surfaces claires bordées, sans ombre sur les cartes ordinaires. La scène d’accueil superpose une feuille légèrement inclinée et un aperçu d’interface. Les ombres sont diffuses, jamais des décalages durs. Le message temporaire reçoit son propre relief.

### Shadow Vocabulary

- **Feuille posée** (`0 12px 35px #424b3924`) : feuille illustrative.
- **Aperçu de correction** (`0 16px 50px #3c4a3029`) : panneau de la scène.
- **Message temporaire** (`0 8px 30px #202a201c`) : notification de résultat ou d’erreur.

**The Papier posé Rule.** Les surfaces de travail restent plates et bordées ; les ombres donnent du relief aux objets de la scène, sans devenir le traitement de chaque carte.

## Shapes

Les angles sont doucement arrondis, avec une hiérarchie distincte pour badges, champs, boutons, notices, aperçus et grandes surfaces (jetons `rounded`). Les limites sont des traits fins (1 px), les cartes de statistiques peuvent rester rectangulaires et transparentes. La feuille illustrative garde des coins droits et une inclinaison de (-5 deg). Les ellipses de QCM et les cercles d’étapes appartiennent au produit ; ils ne sont pas interdits par une règle générique contre les formes décoratives.

## Components

### Buttons

Commandes calmes, lisibles et légèrement tactiles. Le primaire porte l’encre végétale et la feuille claire ; le secondaire a une bordure visible ; le ghost retire cette bordure ; le bouton texte souligne son libellé au survol. Le bouton standard a une hauteur minimale de (44 px), le petit de (38 px). Les liens et boutons conservent le focus global, un contour de (2 px) décalé de (4 px). Les boutons désactivés passent à une opacité de (.55).

Le survol change fond et bordure en (150 ms). Hors réduction de mouvement, une pression applique `scale(.98)` pendant (150 ms) avec l’accélération extraite dans le sidecar ; cette réduction ne s’applique ni aux éléments désactivés ni au focus clavier visible. C’est une adaptation CSS native du comportement Button de Be UI, pas le composant React officiel.

Les boutons de démonstration emploient Torph vanilla (0.1.3) pour le libellé « Analyse en cours… » : durée (220 ms), locale française, échelle désactivée et `respectReducedMotion: true`. Leur largeur minimale est conservée pendant l’analyse ; `aria-label` et `aria-busy` reflètent l’état. Le nettoyage détruit l’instance et restaure le texte, la largeur et les attributs temporaires, y compris après une erreur. Le module est local ; le chargement de son style est couvert par un hash CSP précis.

### Chips

Les badges portent des statuts, pas une interaction de filtrage. Leur couleur et leur fond sont sémantiques, avec texte explicite : correcte, incorrecte, à vérifier, information ou état neutre. Les variantes utilisent une petite forme rectangulaire adoucie ; les onglets de correction sont des boutons distincts, soulignés lorsqu’ils sont actifs.

### Cards / Containers

Les cartes ont le fond `surface`, un trait `line`, le rayon `surface` et un remplissage de (24 px), ramené à (20 px) sur téléphone. Les cartes de tableau n’ont pas de remplissage ; la table défile dans son propre conteneur. Les statistiques utilisent les séparateurs sans multiplier les boîtes. Les notices emploient un fond tonal et un texte sémantique.

### Inputs / Fields

Chaque champ garde son label visible ; les exemples restent dans les placeholders et ne remplacent pas le label. Les champs ont une hauteur minimale de (44 px), le rayon `field`, le trait `control-line` et le fond `surface`. Les messages d’erreur sont en terre d’erreur et les champs désactivés portent le fond dédié. Le focus est celui du système. Les choix de réponse sont de véritables radios dans une cible carrée de (44 px) ; la sélection inverse fond et texte, le focus est dessiné autour du choix.

### Navigation

La navigation de travail associe libellés et icônes SVG au trait. L’élément actif gagne un fond sauge et une graisse (550), le survol un fond plus léger. Sur mobile la navigation se place dans le flux ; les éléments secondaires de la barre latérale sont retirés. L’accueil garde sa propre navigation, plus légère. Le lien d’évitement rend le contenu principal accessible au clavier.

### Scène de papier et panneau de vérification

La scène illustrative est composée en HTML/CSS : feuille QCM, cases elliptiques et panneau d’aperçu. Son libellé « Exemple illustratif » reste lisible quand la barre du panneau revient à la ligne. Elle n’est ni une feuille imprimable compatible, ni une capture de résultats réels. L’entrée unique de la composition translate de (12 px) vers sa position en (800 ms), uniquement hors réduction du mouvement ; aucune animation permanente n’est prévue.

Dans le vrai panneau de vérification, l’extrait reste original, sur blanc, sans filtre et sans teinte. Son cadre mesure (250 px) de haut, l’image au plus (228 px), pour conserver les décisions à portée. La lecture automatique, la décision humaine et la réponse attendue restent distinctes. Le focus aller-retour sur petit écran appartient à ce composant.

## Do's and Don'ts

### Do:

- Do conserver les labels français, les états de chargement et d’erreur, et le focus clavier visible.
- Do laisser les scans sur fond blanc, sans filtre, teinte ni transparence.
- Do montrer les ambiguïtés et la note provisoire jusqu’à leur vérification.
- Do garder la mention « Exemple illustratif » lisible sur téléphone et distinguer cette scène de la démonstration synthétique réelle.
- Do respecter la réduction du mouvement et libérer les animations après une analyse.

### Don't:

- Don’t présenter les fontes, la palette ou ce rendu proposé comme une identité déjà approuvée.
- Don’t employer une illustration de QCM comme feuille compatible avec le moteur ou comme preuve de résultat réel.
- Don’t inventer de taux de précision, de gain chiffré, de client ou de prix.
- Don’t transformer la géométrie des réponses QCM en simple décoration des données de correction.

Les petits « i » décoratifs encore présents dans certaines notices sont un écart existant de pictogramme typographique ; ils ne deviennent pas une règle à réutiliser. Les corrections de revue (focus mobile aller-retour, mention illustrative et retrait des flèches en glyphes) sont intégrées au système décrit. Cette extraction ne modifie pas l’interface et ne constitue pas une nouvelle mesure de performance.
