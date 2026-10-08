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

## Décrire les marques

Pour chaque question, comparer le modèle vierge et l’extrait proposé. Vérifier
le numéro et tous les choix, puis renseigner un alias de relecture et chaque case :

| Observation | Signification |
|---|---|
| Aucune marque | Aucune marque ajoutée visible ; le contour et le chiffre imprimés ne comptent pas |
| Marque nette | Une marque ajoutée est clairement visible, remplissage ou coche |
| Trace ambiguë | La trace ne permet pas une décision certaine, notamment après effacement |
| Case illisible | La qualité ou le cadrage empêche de lire cette case |

La conclusion unique, multiple, vide, ambiguë ou illisible découle de ces observations.
Ne pas deviner l’intention de l’élève. Confirmer séparément la position de la question,
puis **Enregistrer et continuer**. Le bouton passe à la prochaine question non observée
après la question courante ; le sélecteur permet de revenir à toute question.

Les changements sont enregistrés avec une révision, un alias et un historique. Une
fenêtre périmée reçoit un conflit au lieu d’écraser une autre modification. La saisie
reste affichée pour permettre sa comparaison après rechargement. Les observations
non enregistrées protègent la navigation et l’actualisation automatique.

## Si le moteur n’a pas positionné les questions

L’original reste accessible, y compris après un échec d’alignement. Ouvrir **Voir
l’original et placer un extrait**, agrandir si nécessaire et choisir **Délimiter
cette question**. Cliquer sur deux coins opposés autour de tous ses choix. Une saisie
des quatre coordonnées, suivie de **Appliquer les coordonnées**, offre une alternative
au clavier. Les coordonnées sont en pixels de l’image source décodée.

Confirmer ensuite la position et enregistrer. Le cadre manuel appartient à cette
observation ; il ne modifie pas le modèle de feuille ni l’alignement du moteur.
On peut aussi déclarer une lecture sur la photo entière ou un extrait mal placé :
ces observations sont conservées, sans être déclarées géométriquement prêtes.
**Un cadre de question confirmé ne valide pas la position de chacune de ses cases.**

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
