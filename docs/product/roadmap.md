# Priorités et critères de passage

[Documentation](../README.md) · [État actuel](../memory/current.md)

Les étapes sont ordonnées par dépendance ; ce ne sont pas des promesses de dates.

| Étape | État | Critère de sortie |
|---|---|---|
| Moteur et interface de démonstration | Implémenté sur synthétique | Parcours de correction et ambiguïtés vérifiés |
| Cadre de reprise et qualité | Implémenté dans cette livraison | Docs, mémoire, dépendances et commandes vérifiées ; CI configurée |
| Assistant de création de modèles | Implémenté, essais synthétiques | Import, placement manuel, calibration, essai, utilisation dans un examen ; [guide](../guides/sheets.md) |
| Modèle réel pilote | [NITE prioritaire](nite-pilot.md), premier diagnostic réel disponible | Calibration et copies annotées manuellement ; aucun modèle NITE préinstallé validé à ce jour |
| Mesure de fiabilité | [S01 implémenté](../development/omr-baseline.md) ; [outillage S02 livré](../guides/annotations.md), collecte et test indépendant S09 à faire | Rapport reproductible sur un jeu réservé, erreurs et charge humaine mesurées |
| Renforcement du moteur | [Plan hybride proposé](hybrid-omr-plan.md), lots S03–S08 | Recalage local, lecture classique et ML comparés ; observation avant activation |
| Évolution visuelle | Inspirations reçues, Renance prioritaire ; traduction proposée | Bibliothèque et design validés, parcours et accessibilité testés |
| Pilote entreprise | À cadrer | Usage, volume, données, fiabilité et exploitation acceptés avec le pilote |
| SaaS multi-entreprises | Non implémenté | Authentification, isolation, stockage, migrations et restauration éprouvés |

## Dette technique explicite

- Compléter les types des sorties optiques/HTTP et les contrats OpenAPI sans casser les exports.
- Introduire les migrations avant la première évolution du schéma SQLite.
- Organiser et formater le frontend avec l'outillage retenu par l'utilisateur.
- Mesurer les délais et volumes avant d'introduire workers, file de tâches ou nouvelle base.
- Vérifier le workflow sur GitHub et envisager la protection de `main` dans les réglages du dépôt.
- Préparer des sauvegardes restaurables et une politique de suppression pour le pilote réel.

Prochain lot technique : **S05, lecteur classique renforcé**. Les expériences hors ligne
[S03](../development/local-registration.md) et [S04](../development/photometric-trial.md)
sont livrées ; aucune variante n’est activée dans le moteur web. La collecte d’exemples
réels variés continue en parallèle. Les annotations servent à mesurer les gains ;
l’interface d’annotation n’entraîne pas de modèle et ne démontre pas une précision.
