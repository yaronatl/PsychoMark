# Direction visuelle — Renance comme référence principale

[Cadre UI](ui.md) · [Originaux et provenance](references/README.md)

## Statut et priorité

**Fait confirmé par l'utilisateur : `HEg1RfvbwAIpjJa.avif` est sa référence préférée.**
Le fichier montre Renance, avec une landing crème et une présentation artistique
Renaissance. Cette préférence prime sur les autres références et sur les goûts par
défaut des skills. Elle ne suffit pas à considérer chaque détail comme approuvé.

La traduction ci-dessous est une **proposition de direction**, pas une maquette validée.
La bibliothèque UI et le framework frontend ne sont pas encore confirmés. L'installation
du skill shadcn et l'accès Be UI ne constituent pas cette décision.

## Lecture de la référence principale

| Ce qui est visible | Ce qu'on propose d'en retenir pour PsychoMark |
|---|---|
| Fond crème chaud et noir, peu de couleurs d'interface | Une identité calme, lisible, avec un contraste marqué pour l'action principale |
| Titres serif hauts, contrastés et centrés | Une présence éditoriale pour les titres de présentation |
| Texte fonctionnel sans empattements | Une lecture simple pour les explications, formulaires et résultats |
| Grandes marges et navigation très discrète | Une hiérarchie claire, peu d'éléments simultanément en concurrence |
| Boutons noir et beige, arrondis contenus | Un primaire évident, un secondaire discret, pas de boutons tous en pilule |
| Aperçu de l'application sous le titre | Montrer la correction de copies concrètement dès la landing |
| Fresque dans le cadre de l'aperçu ; colonnes et marbre autour de l'écran | Un univers artistique possible, à distinguer du décor de présentation du mockup |

Le décor extérieur à l'écran ne prouve pas que le site original a une fresque plein
écran. Ne pas transformer cette mise en scène en une exigence de fond pour chaque page.
L'utilisateur a été interrogé sur ce qu'il souhaite reprendre de cet univers : fresques
et marbre inclus, ou surtout sobriété, couleurs crème et typographie. Réponse en attente.

## Rôle des références secondaires

- **Taskk** : un aperçu produit généreux, une sidebar reconnaissable, de la profondeur
  mesurée. Son bleu dominant et son effet de verre ne remplacent pas la palette Renance.
- **Incredible** : respiration autour du message principal, typographie et image large.
  Le paysage et le champ de conversation ne deviennent pas des fonctions de PsychoMark.
- **Athera** : caractère typographique et graphismes simples. Le bleu électrique et
  l'italique généralisé ne sont pas adoptés comme direction principale.
- **Energy, vidéo** : progression de la présentation, aperçu des étapes du produit et
  navigation compacte persistante dans les images échantillonnées. Les effets observés
  ne justifient pas de multiplier les animations dans l'écran de correction.

## Traduction proposée par surface

### Landing page

Composition centrée, éditoriale et aérée. Commencer par la promesse métier, puis montrer
le produit. Exemple de texte de travail : « Vos copies corrigées. Votre temps retrouvé. »
Ce texte n'est pas encore validé et ne promet aucun gain chiffré.

```text
Logo                 Fonctionnement · Démonstration           Ouvrir l'application

                       Grand titre serif, deux lignes
                     Courte explication concrète du produit
                         [ Essayer la démonstration ]

             Cadre visuel large avec aperçu réel de la correction

                  Créer l'examen → Importer → Vérifier les cas douteux
```

L'univers artistique, s'il est retenu, se concentre dans une scène forte qui accueille
l'aperçu produit. Le dessin exact, les images et leur réalisation restent à définir.
Le parcours de démonstration déjà fonctionnel peut être mis en avant ; ne pas inventer
des clients, avis, volumes, prix, comptes ou performances qui n'existent pas encore.

### Dashboard et correction

Conserver la même famille de couleurs et le même soin typographique, avec des surfaces
unies derrière les données. La sidebar peut être crème, l'espace de travail blanc cassé,
les séparateurs fins. Les titres de page peuvent porter l'identité serif avec retenue ;
le tableau, les chiffres, les champs et les commandes restent en sans-serif lisible.

```text
Sidebar             Mes examens                             [ Créer un examen ]
                    Liste des examens et état des corrections

Correction          Questions / réponses / états            Extrait de la copie
                    Filtres et résultats                    Décision de vérification
```

Les images de copies doivent garder un rendu neutre : pas de filtre chaud ni de
transparence qui altérerait la perception du crayon. Les états correct, incorrect,
en attente et illisible restent distincts par texte et symbole, pas seulement par couleur.

## Base de style proposée, à éprouver dans la première maquette

Ces valeurs sont des **approximations de travail**, pas un prélèvement certifié des
couleurs ou une identification des polices originales.

| Rôle | Proposition |
|---|---|
| Fond papier | `#F4F2EB` |
| Surface de lecture | `#FCFBF8` |
| Texte et action primaire | `#181815` |
| Texte secondaire | `#625F57` |
| Surface secondaire | `#E6E2D6` |
| Séparateurs | `#D6D1C5` |

Typographie candidate : **Instrument Serif** pour les grands titres et **Geist Sans**
pour l'interface. Ce sont des propositions à comparer visuellement, pas les noms supposés
des polices de la référence. Les corps et contrastes doivent être vérifiés dans la
maquette desktop/mobile ; ne pas reproduire les petits textes peu contrastés d'un mockup.

Espacement sur une base de 4/8 px ; grands intervalles pour les sections marketing,
rythme plus compact pour le travail. Arrondis modestes pour les contrôles, plus amples
pour la scène produit. Animations courtes sur les interactions, une éventuelle séquence
d'entrée mesurée sur la landing, et respect de la réduction de mouvement.

## Contrôle de fidélité à chaque évolution

1. Ouvrir l'original Renance et lire cette page avant une tâche visuelle.
2. Distinguer la demande locale de retouche d'une demande de changement de direction.
3. Vérifier palette, typographie, espaces et hiérarchie dans des captures desktop/mobile.
4. S'assurer que les éléments empruntés aux références secondaires servent la direction
   principale au lieu de créer un assemblage de styles.
5. Conserver les comportements métier : ambiguïtés explicites, note en attente, historique.
6. Consigner les choix validés et les écarts volontaires ; ne pas remplacer cette référence
   implicitement lors d'une nouvelle session ou sur suggestion d'un skill.

## Prochaine étape

Présenter cette lecture à l'utilisateur, préciser la place des fresques et du marbre,
puis construire une première maquette de landing et un écran représentatif de correction.
La maquette permettra de vérifier l'identité sur les deux usages avant une refonte générale.
