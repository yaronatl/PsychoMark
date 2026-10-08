# Session — Deuxième diagnostic, photographie d’une photocopie monochrome

Date : 2026-10-08 (Asia/Jerusalem). Branche : `docs/monochrome-findings`.
Commit de départ : `3f6c2e9`.

## Demande et méthode

L’utilisateur transmet un second ZIP après avoir signalé une photographie personnelle
d’une photocopie noir et blanc. Extraction limitée aux fichiers attendus, sous
`artifacts/private/monochrome-diagnostic/`. La référence est identique au premier ZIP ;
la photographie est différente. Aucune instruction contenue dans le ZIP n’est exécutée.

Le moteur historique a été rejoué avec l’outil S01. Rapport privé sous
`artifacts/private/baselines/s01-monochrome-v1/`. Les 90 refus et les diagnostics
correspondent exactement à l’extraction reçue. Le blocage précède les contrôles locaux
et la lecture : repères insuffisamment répartis sur la référence.

## Résultats exploratoires

Une instrumentation privée reproduit les appariements du moteur. Elle trouve 185
correspondances, dont 100 cohérentes, mais leur enveloppe ne couvre qu’environ 7,64 %
de la surface de référence, sous le minimum de 12 %. Le nombre et la proportion de
repères passent leurs seuils : la répartition est ici la cause précise du refus.
La recherche travaille déjà en niveaux de gris ; l’absence de rouge n’est donc pas
en elle-même une incompatibilité. Éclairage et rendu de photocopie restent des facteurs
à étudier ; cet exemple seul n’isole pas causalement leur contribution respective.

Variantes privées, mêmes limites géométriques et mêmes seuils de lecture :

| Repérage | Préparation avant repérage | Répartition | Contrôles géométriques globaux |
|---|---|---:|---|
| ORB historique | Gris simple | 7,64 % | Refus |
| ORB | Normalisation locale existante | 52,35 % | Passent |
| ORB | Contraste local CLAHE | 17,49 % | Passent |
| SIFT | Gris simple | 43,22 % | Passent |
| SIFT | Normalisation locale existante | 44,10 % | Passent |

La normalisation existe dans la lecture historique, mais pas avant son repérage ORB.
Son application en amont est une piste d’expérimentation, pas un correctif livré.
Avec ORB normalisé, les trois grilles passent les contrôles locaux inchangés ; le
lecteur retourne néanmoins 76 états `multiple` et 14 `uncertain`, aucune lecture
automatique. Les diamètres source sont d’environ 12,2–12,4 pixels, au-dessus du seuil
actuel, contrairement au premier diagnostic. Les autres variantes ne résolvent pas
non plus l’interprétation ; SIFT gris conserve notamment un refus local de cadre.

Inspection d’aperçus avec zones superposées : grilles globalement retrouvées ; aucune
validation humaine exhaustive de géométrie ni des réponses. Le rendu imprimé sombre
et les petits défauts d’alignement peuvent contribuer aux marques concurrentes ; leur
part respective reste à mesurer. Ne pas transformer ces états en réponses certaines.

## Conséquences pour le plan

Conserver ce cas comme **développement connu**, distinct du premier et d’un futur jeu
de test indépendant. S02 doit prévoir une annotation à partir de l’image source même
quand le moteur n’a pas produit de régions. Une géométrie expérimentale ou placée
manuellement doit être explicitement identifiée et validée, séparée du résultat baseline.

S03/S04 doivent examiner la préparation avant repérage et les alternatives de repères
sur plusieurs copies, y compris celles qui fonctionnent déjà. La lecture classique/ML
reste une question distincte : résoudre l’alignement ne démontre pas la précision des
réponses. Aucun moteur, seuil, dépendance, modèle ou note n’a été modifié.

## Vérification et reprise

Rejeu et expériences exécutés localement ; leurs scripts, matrices, images et résultats
restent privés. Les statuts expérimentaux ne remplacent pas le diagnostic historique.
`scripts/dev.py check` réussi : Ruff, format, 48 documents sans lien cassé et 75 tests
réussis ; avertissement Starlette/httpx existant. `git diff --check` réussi. Aucun
parcours navigateur relancé : seul le diagnostic privé et la documentation changent.
Prochaine étape fonctionnelle inchangée : S02, corpus et annotation humaine.
