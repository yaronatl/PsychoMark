# Mémoire du projet

[Documentation](../README.md)

La mémoire appartient au dépôt et suit ses versions Git. Elle est lisible par un
développeur humain ou un assistant, sans compte externe ni base vectorielle.
Elle ne s'alimente pas automatiquement depuis les conversations : chaque intervenant
la met à jour avec des faits vérifiés, selon le protocole ci-dessous.

## Trois niveaux

| Niveau | Rôle | Entretien |
|---|---|---|
| [État actuel](current.md) | Résumé court : livré, limites, prochaine étape, dernier journal | Réécrit après chaque session significative |
| [Sessions](sessions/README.md) | Journal daté : objectif, changements, tests, blocages et reprise | Ajouter un fichier par lot significatif, avec le modèle fourni |
| [Décisions](../architecture/decisions/README.md) | Pourquoi les choix durables ont été faits | Ajouter/remplacer un ADR quand la décision change |

Les procédures et l'architecture restent dans leurs guides. La mémoire y renvoie,
sans multiplier des versions contradictoires de la même règle.

## Début de session

1. Lire `AGENTS.md`, `current.md`, le dernier journal pertinent et les ADR concernés.
2. Vérifier la branche, le commit, l'arbre de travail et la disponibilité des outils.
3. Recouper avec le code ; signaler un état périmé plutôt que le considérer comme preuve.
4. Identifier l'objectif et les critères de réussite de la session actuelle.

## Fin de session

1. Copier [le modèle de session](../templates/session.md) sous
   `sessions/AAAA-MM-JJ-NN-sujet.md` en utilisant la date UTC réelle.
2. Noter ce qui a changé, les commandes réellement exécutées, leurs résultats et les
   limites. Ajouter le commit de départ ; le commit de livraison se retrouve dans
   l'historique Git du fichier, ce qui évite une référence circulaire.
3. Lier les guides/ADR concernés et mettre à jour l'index des sessions.
4. Résumer l'état dans `current.md` ; déplacer les détails historiques vers les journaux.

Un journal clôturé reste historique ; une correction factuelle doit être explicite.
Une fois les sessions nombreuses, les classer par année et corriger les liens de l'index,
sans supprimer leurs références Git. Aucune conversation brute, autorisation supposée,
clé, nom d'élève ou copie réelle ne doit entrer dans cette mémoire.
