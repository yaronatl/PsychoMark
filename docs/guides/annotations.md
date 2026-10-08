# Constituer des exemples annotés

[Documentation](../README.md) · [Plan OMR hybride](../product/hybrid-omr-plan.md)

L’espace **Annotations** prépare les exemples qui serviront à améliorer et à comparer
les lecteurs. Il décrit les marques visibles, sans afficher le corrigé ni les réponses
du moteur. Il ne change aucune note et ne lance aucun entraînement.

## Importer une copie

1. Dans l’atelier, ouvrir **Annotations → Ajouter une copie** (`#/annotations/new`).
2. Choisir une image, un PDF d’une page ou un ZIP de diagnostic PsychoMark, jusqu’à
   64 Mio. Une image/PDF utilise un modèle enregistré dans **Mes feuilles** ; le ZIP
   contient déjà sa référence et les questions de l’essai.
3. Donner un identifiant au **papier physique**, par exemple `feuille-001`, sans nom
   d’élève. Toutes les photos de ce même papier doivent reprendre cet identifiant.
4. Garder **Développement** pour les cas déjà examinés. Les autres usages préparent
   des exemples distincts pour l’apprentissage, le réglage des seuils et le test réservé.
   Un diagnostic reste obligatoirement en développement.
5. Dans **Regrouper des feuilles liées**, utiliser un même groupe pour les exemples
   apparentés qui ne doivent pas se retrouver dans plusieurs usages. Par défaut,
   le groupe est l’identifiant du papier. L’application contrôle la cohérence des
   identifiants déclarés ; elle ne reconnaît pas automatiquement le scripteur.
6. L’autorisation d’apprentissage est décochée par défaut. La laisser vide permet
   d’annoter sans rendre la copie admissible à un futur entraînement.

Le papier, le groupe, l’usage et l’autorisation sont figés à l’import dans cette
première version. Il n’existe pas encore d’écran de transfert ou de suppression.
Une image aux pixels identiques est refusée même si son encodage PNG diffère. Les
photos proches, recadrées ou recompressées avec pertes ne sont pas dédupliquées
automatiquement : leurs identifiants communs restent indispensables.

## Annoter rapidement sur téléphone

L’écran se concentre sur une question. **Toutes les copies** permet de revenir à la
liste ; les options et l’historique restent disponibles plus bas. Le bouton
**Enregistrer et continuer** reste au bas de l’écran sur téléphone.

1. Renseigner son alias dans **Relecture et options** une fois. Il est retenu dans
   cet onglet, y compris après rechargement ; seuls les labels enregistrés vivent
   sur le serveur. Sur un appareil partagé, vérifier l’alias avant une nouvelle séance.
2. Vérifier l’extrait et cocher la confirmation du numéro de question et de ses choix.
   **Comparer avec le modèle vierge** ouvre la référence si nécessaire.
3. Si un seul choix est nettement marqué, toucher son numéro : cette action indique
   explicitement que **les autres cases sont sans marque**. Pour une question vide,
   toucher **Aucune case marquée**. Aucun de ces boutons n’enregistre à lui seul.
4. **Enregistrer et continuer** sauvegarde puis ouvre la prochaine question non
   observée. Arrivé au bout, il revient aux éventuelles questions passées plus tôt.

La position et les marques ne sont jamais copiées automatiquement à la question
suivante. **Passer** laisse la question sans nouvelle observation ; une saisie en
cours demande confirmation avant d’être quittée. **Revoir la dernière** retourne à
la dernière question enregistrée pour la rectifier ; ce n’est pas une suppression
d’historique. Le sélecteur donne accès à toute question.

Pour plusieurs marques ou un doute, ouvrir **Plusieurs marques ou une trace douteuse**.
Les choix détaillés restent disponibles, sans forcer de réponse unique :

| Observation | Signification |
|---|---|
| Aucune marque | Aucune marque ajoutée visible ; contour et chiffre imprimés exclus |
| Marque nette | Une marque ajoutée clairement visible, remplissage ou coche |
| Trace ambiguë | Une trace ne permettant pas une décision certaine, notamment après effacement |
| Case illisible | Qualité ou cadrage empêchant de lire cette case |

Sur ordinateur, les chiffres **1 à 9** et **0** permettent la même saisie rapide.
Depuis le titre de question, **Entrée** demande l’enregistrement. Les raccourcis
n’interceptent pas la saisie des champs, les liens ou les contrôles natifs. Les modèles
à dix choix conservent leur dixième bouton, sans raccourci à un seul chiffre.

Les changements gardent une révision, un alias et un historique. Une fenêtre périmée
reçoit un conflit ; une erreur conserve la saisie. Le bouton est bloqué durant la
requête : un double appui ne doit pas enregistrer deux observations. Rien n’est sauvé
hors ligne et rien n’est entraîné automatiquement.

## Cadrer au doigt, à la souris ou au clavier

**Cadrer cette question**, **Ouvrir la photo** ou **Ajuster le cadre** ouvre la photo
originale dans une fenêtre dédiée, en plein écran sur téléphone :

- Sans cadre, glisser d’un coin au coin opposé pour tracer le rectangle.
- En mode **Cadre**, glisser à l’intérieur pour déplacer le rectangle. Les quatre
  grandes poignées (zones tactiles de 48 px) sont déportées vers l’extérieur pour
  éviter de cacher les coins avec le doigt ; les tirer pour redimensionner.
- Glisser à côté du cadre pour déplacer la photo, ou choisir **Photo** pour la
  déplacer depuis n’importe quel endroit sans toucher au rectangle.
- **Pincer à deux doigts** zoome et déplace la photo. Le menu Zoom propose aussi des
  grossissements jusqu’à 1 200 %. **Agrandir le cadre** centre la sélection et adapte
  le zoom à l’écran. Le zoom n’ajoute aucun détail à la photo et ne modifie pas les bornes.
- **Ajuster avec les boutons** permet de choisir le cadre entier ou un seul bord,
  puis de le déplacer avec quatre grandes flèches. Le pas fin vaut 1 pixel de la
  photo source, le pas large 10 pixels, indépendamment du zoom. Un bord ne peut pas
  traverser le bord opposé ou sortir de l’image.
- **Réutiliser l’ancien cadre** est directement visible au-dessus de la photo. Par
  défaut, **À droite** reprend le dernier cadre appliqué sur cette copie et le décale
  de sa propre largeur ; sa hauteur et sa position verticale restent identiques.
  **À gauche** fait le décalage inverse ; **Même endroit** retrouve la position initiale.
  Deux appuis successifs repartent du même ancien cadre : ils ne sautent pas deux questions.
  Le bouton est désactivé tant qu’aucun cadre n’a été appliqué dans cette séance.
- Ce décalage est une proposition pour les questions côte à côte, pas une détection.
  Vérifier les espaces entre colonnes et le numéro de question. Au changement de
  section/ligne, choisir **Même endroit** puis déplacer le cadre. Un décalage hors de
  la photo est refusé sans modifier ni couper le cadre actuel.
- **Autres options et coordonnées** contient **Retracer le cadre** et la saisie des
  quatre bornes. Le zoom et la position de lecture sont conservés pendant la séance ;
  les coordonnées saisies doivent être appliquées explicitement.
- **Utiliser ce cadre** confirme explicitement la position de cette question et montre
  son extrait immédiatement. **Annuler** ou Échap abandonne les changements de la fenêtre.

Un geste tactile interrompu restaure le rectangle précédent. Les bornes sont en pixels
de l’image décodée et restent dans cette image. Le cadre n’est sauvegardé sur le serveur
qu’avec **Enregistrer et continuer** ; il ne change ni le modèle ni le moteur.

Dans **Relecture et options**, on peut encore déclarer une lecture sur la photo entière
ou un extrait mal placé. Ces observations sont conservées sans être géométriquement
prêtes. **Un cadre de question confirmé ne valide pas la position de chaque case.**

## Exporter et reprendre

- **Exporter le manifeste** télécharge les métadonnées, observations et empreintes
  de toutes les acquisitions, sans images ni prédictions.
- **Exporter cette copie** produit un ZIP autonome avec manifeste, source, référence,
  modèle figé, régions/masques disponibles et extraits manuels. Les prédictions ne
  sont pas incluses. Ce ZIP de corpus n’est pas un ZIP de diagnostic réimportable.
- Le dossier privé `artifacts/web/corpus/` (ou `corpus/` dans le dossier de données
  choisi) conserve images et annotations entre redémarrages. Inclure ce dossier dans
  les [sauvegardes](../development/data.md) ; Git ne le sauvegarde pas.

`eligible_for_training` exige l’usage apprentissage, l’autorisation et toutes les
observations avec position confirmée. Il s’agit d’un filtre de préparation, pas d’une
certification des données ni d’une validation des cases. Le corpus n’établit pas
l’indépendance du test ni l’accord entre plusieurs annotateurs. Une seconde lecture
à l’aveugle, la collecte réelle et les mesures de précision restent à organiser.
