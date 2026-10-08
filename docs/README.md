# Documentation

## Parcours de lecture

Pour tester : [Codespaces](guides/codespaces.md) → [interface web](guides/web.md) →
[ajouter une feuille](guides/sheets.md).
Pour reprendre le développement : [état actuel](memory/current.md) →
[architecture](architecture/overview.md) → [stack](development/stack.md) →
[workflow](development/workflow.md).

## Classement

| Dossier | Contenu et source de référence |
|---|---|
| `guides/` | Procédures pour l'utilisateur : cloud, correction web, [moteur et calibration](guides/cli.md) |
| `architecture/` | [Modules et données](architecture/overview.md), [OMR](architecture/omr.md), [API](architecture/api.md) |
| `architecture/decisions/` | [Décisions durables et leur justification](architecture/decisions/README.md) |
| `development/` | [Stack](development/stack.md), [workflow](development/workflow.md), [validation](development/testing.md), [données](development/data.md) |
| Outils visuels | [Skills installés et connexion Be UI](development/design-tools.md) |
| `product/` | [Priorités](product/roadmap.md) et [choix visuels](product/ui.md) |
| Inspirations | [Direction Renance](product/visual-direction.md) et [originaux](product/references/README.md) |
| Système visuel | [DESIGN.md](../DESIGN.md), description et tokens de la proposition construite ; [PRODUCT.md](../PRODUCT.md), contexte produit destiné aux outils de design |
| `memory/` | [Protocole de reprise](memory/README.md), [état courant](memory/current.md), [sessions](memory/sessions/README.md) |
| `templates/` | Modèles de [session](templates/session.md) et de [décision](templates/decision.md) |

## Règles documentaires

- Une information durable a une seule page de référence ; les autres pages la lient.
- Distinguer **implémenté**, **proposé**, **à décider** et **non vérifié**.
- Une commande s'exécute à la racine du dépôt, sauf mention contraire.
- Utiliser des liens relatifs vers les fichiers ; les scripts contrôlent leur existence,
  pas la validité des ancres, des liens externes ou des affirmations techniques.
- Mettre les résultats datés dans les sessions, pas un compteur de tests permanent
  dans tous les guides. Mettre une procédure dans un guide, pas dans un journal.
- Mettre à jour la page concernée avec le code dans le même changement.
- Ne pas créer un journal pour chaque message. Une session décrit un lot de travail
  significatif ; ne pas recopier la conversation ou exposer de données personnelles.
