# Données, conservation et évolution

[Documentation](../README.md) · [Architecture](../architecture/overview.md)

## Emplacements

| Donnée | Emplacement actuel | Dans Git ? |
|---|---|---|
| Exemples de configuration synthétiques | `examples/` | Oui |
| Générateur et fixtures synthétiques | `src/psychomark/demo.py`, `tests/` | Oui |
| Base et images du serveur par défaut | `artifacts/web/` | Non |
| Copies et références réelles d'essai | `artifacts/private/` ou stockage privé explicite | Non |
| Rapports et captures de vérification | `artifacts/` | Non |
| Décisions et sessions sans données personnelles | `docs/` | Oui |

Le fichier `.gitignore` évite l'ajout accidentel de ces dossiers ; il ne constitue
ni un chiffrement ni un contrôle d'accès. Un chemin personnalisé hors de `artifacts/`
doit être vérifié avant tout commit. Ne pas nommer les cas de test avec des noms d'élèves.

## Conservation dans le MVP

Le même Codespace conserve normalement ses fichiers entre arrêts et redémarrages.
Sa suppression peut les faire perdre. Git ne sauvegarde pas les données ignorées.
Les exports CSV/JSON ne remplacent pas une sauvegarde complète avec images et historique.
Il n'y a pas encore de rétention automatique ni de commande de sauvegarde intégrée.

Pour une sauvegarde manuelle cohérente : arrêter proprement **le serveur concerné**,
vérifier qu'il ne traite plus d'import, copier son dossier de données complet dans un
stockage privé, puis le relancer. Inclure les modèles personnalisés et leurs références
s'ils vivent ailleurs. Pour valider une restauration, utiliser une copie du dossier,
un autre port et les mêmes modèles ; vérifier examens, images et historique. Ne pas
tester en écrasant les données de travail. Cette procédure reste à exercer sur les
données d'un véritable pilote avant de promettre une capacité de reprise.

## Avant une évolution du stockage

Documenter le schéma source/cible, sauvegarder, ajouter une migration idempotente ou
versionnée, tester une ancienne base avec ses images, et définir le retour arrière.
Ne pas remplacer silencieusement une base existante par une base vide. L'initialisation
`CREATE TABLE IF NOT EXISTS` actuelle ne suffit pas à mettre à niveau des colonnes.

Avant un SaaS avec plusieurs entreprises, concevoir et tester l'authentification,
l'autorisation par organisme, la conservation/suppression, les sauvegardes restaurables
et la gestion du stockage. Ce sont des travaux identifiés, pas des capacités installées.
