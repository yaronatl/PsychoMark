# Session — Premier diagnostic réel d’une référence numérique et d’une photo

Date : 2026-10-08. Branche documentaire : `docs/printed-photo-findings`.

## Entrée et méthode

L’utilisateur a transmis le ZIP de diagnostic demandé. Ses fichiers ont été extraits
par une liste de noms autorisés dans `artifacts/private/photo-diagnostic/`, hors Git.
Référence, copie et aperçu inspectés, analyse relancée avec le moteur existant.
Aucun nom, scan, export de réponses ou identifiant de copie n’est ajouté au dépôt.

## Constats

Le blocage est reproduit sur les trois grilles configurées. L’alignement réussit,
la netteté des cadres passe et les grilles sont entièrement visibles. La taille des
cases dans le fichier reçu est juste sous le minimum configuré ; la correspondance
des cadres échoue aussi sur deux grilles. Les repères paraissent globalement cohérents.

La copie imprimée présente également des fonds colorés alternés et un rendu de
l’impression différents de la référence numérique. Une disposition identique ne
suffit pas à assurer l’équivalence photométrique du modèle de soustraction actuel.

Une expérience privée en mémoire assouplissant les deux contrôles ne résout pas la
lecture : toutes les questions deviennent incertaines à cause des traces concurrentes.
Des explorations de canal couleur/masquage n’ont pas donné de solution validée.
**Aucun paramètre ni algorithme de production n’a été modifié.** Ne pas présenter
cette session comme une correction du moteur ou une validation de compatibilité NITE.

Les mesures et le compte rendu détaillé sont dans le dossier privé, `findings.md`.
La reproduction concorde sur les statuts, raisons et mesures arrondies ; la matrice
présente des différences d’arrondi flottant entre environnements, sans effet constaté
sur ces résultats.

## Reprise

Le problème de la photo n’est plus inexpliqué. Le prochain essai utile est le fichier
photo original de meilleure définition et, si disponible, une référence vierge de la
même version imprimée. Cela permettra de séparer la perte de résolution des différences
d’impression. Le moteur nécessite ensuite une comparaison plus robuste aux impressions
et, selon les mesures, un recalage local des grilles ; ces évolutions ne sont pas livrées.

La priorité reste la fiabilité : pas d’assouplissement destiné seulement à transformer
un refus en note. Les cas avec traces/effacements doivent rester vérifiables.
Aucun corrigé n’a été utilisé dans les expériences, aucun taux de précision établi.
Vérification de cette livraison documentaire : liens locaux et diff. Les tests du
code ne sont pas répétés : aucun code de l’application n’est modifié.
