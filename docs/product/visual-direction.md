# Direction visuelle — papier et encre

[Cadre UI](ui.md) · [Originaux et provenance](references/README.md) · [Système implémenté](../../DESIGN.md)

## Ce qui est confirmé

L’utilisateur préfère **Renance (`HEg1RfvbwAIpjJa.avif`)** parmi ses inspirations.
Il précise ensuite : univers calme et apaisant, couleurs chaleureuses, douces et
claires, typographies serif travaillées, impression d’intelligence et d’élégance.
Le papier, le stylo et l’encre apportent la dimension ancienne ; l’outil reste moderne.
Il cite reMarkable comme référence d’ambiance et autorise une première refonte.

Cette précision remplace la question ouverte sur la place des fresques et du marbre.
La direction retenue pour cette **première proposition** est celle d’un atelier de
correction et de la papeterie. Les décors monumentaux ne sont pas nécessaires à ce brief.
Le site de reMarkable n’a pas pu être consulté depuis cet environnement (accès HTTP
refusé) ; aucune analyse de son site actuel n’est présentée comme vérifiée.

## Références et hiérarchie

| Référence | Traduction dans la proposition |
|---|---|
| Renance, référence principale | Crème clair, grands titres serif, composition centrée, beaucoup d’espace, primaire sombre, aperçu produit sous le titre |
| reMarkable, ambiance décrite par l’utilisateur | Calme, rapport au papier, sobriété des commandes et place laissée au contenu |
| Incredible | Respiration et hiérarchie éditoriale ; pas de champ de conversation inventé |
| Taskk | Aperçu généreux du produit ; son bleu dominant ne devient pas notre palette |
| Athera | Caractère typographique ; pas de cobalt ni d’italique systématique |
| Energy, vidéo | Progression de la présentation et étapes du produit ; pas d’animation permanente |

Dans Renance, les colonnes et le marbre entourent l’écran du mockup : ce ne sont pas
nécessairement des composants de son site. Les originaux restent archivés ; les images
d’inspiration ne sont pas redistribuées dans l’application ni utilisées comme actifs marketing.

## Première proposition implémentée

- **Accueil** (`/` ou `#/home`) : promesse éditoriale, démonstration réelle, scène illustrative
  feuille/QCM et panneau de correction, trois étapes du parcours et limites du prototype.
- **Espace de travail** (`#/exams`) : navigation et surfaces papier, titres serif, tableaux,
  formulaires et chiffres en sans-serif. Créer, modifier, importer, vérifier et exporter
  restent les fonctions existantes.
- **Correction** : états correct/incorrect/à vérifier explicitement libellés, note provisoire,
  image originale sur fond blanc neutre, extrait limité en hauteur pour garder les décisions accessibles.
- **Mouvement** : une entrée discrète de la scène d’accueil ; aucune animation permanente.
  Respect de `prefers-reduced-motion`.

La scène de l’accueil est une illustration HTML/CSS, libellée comme telle. Elle ne constitue
ni une feuille imprimable compatible avec le moteur, ni une capture de résultats réels.
Les boutons de démonstration ouvrent le véritable parcours sur une copie synthétique.
Aucun prix, témoignage, logo client, taux de fiabilité ou gain chiffré n’est inventé.

La palette, les typographies **Instrument Serif + Geist**, les états et les composants
réalisés sont décrits dans [DESIGN.md](../../DESIGN.md), extrait du code. Les fontes sont
hébergées localement avec leurs licences. Ces choix précis sont **proposés**, pas encore
validés par l’utilisateur après visualisation. La bibliothèque UI future reste à choisir.

## Règles de continuité

1. Lire ce brief, le système implémenté et l’original Renance avant une évolution visuelle.
2. Une retouche locale ne remplace pas implicitement toute la direction.
3. Les références de l’utilisateur priment sur les styles par défaut des skills.
4. Vérifier l’accueil et le travail réel sur ordinateur et mobile ; pas seulement le hero.
5. Conserver les images de scans neutres : aucune teinte, transparence ou filtre graphique.
6. Préserver les ambiguïtés, la note en attente et l’historique ; ne jamais maquiller une incertitude.
7. Consigner les choix validés et les écarts. Ne pas présenter cette proposition comme une identité approuvée.

## Prochaine étape

Recueillir les retours visuels sur cette version navigable : caractère des titres,
chaleur de la palette, composition, densité de l’espace de travail. Affiner ensuite les
écrans dans cette direction. La migration éventuelle vers une bibliothèque de composants
fera l’objet d’un choix explicite et séparé.
