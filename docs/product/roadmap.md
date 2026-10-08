# Priorités et critères de passage

[Documentation](../README.md) · [État actuel](../memory/current.md)

Les étapes sont ordonnées par dépendance ; ce ne sont pas des promesses de dates.

| Étape | État | Critère de sortie |
|---|---|---|
| Moteur et interface de démonstration | Implémenté sur synthétique | Parcours de correction et ambiguïtés vérifiés |
| Cadre de reprise et qualité | Implémenté dans cette livraison | Docs, mémoire, dépendances et commandes vérifiées ; CI configurée |
| Modèle réel pilote | [NITE prioritaire](nite-pilot.md), fichier source nécessaire | Modèle NITE préconfiguré, feuille vierge calibrée et copies annotées manuellement |
| Mesure de fiabilité | À faire | Rapport reproductible sur un jeu réservé, erreurs et charge humaine mesurées |
| Renforcement du moteur | À définir selon les erreurs | Comparaison avant/après sur le même protocole ; IA spécialisée seulement si utile |
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

La prochaine étape utile sur le moteur reste l'acquisition de données réelles.
La documentation n'élimine pas ce besoin et une refonte du code ne le remplace pas.
