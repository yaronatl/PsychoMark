# Registre des décisions d'architecture

[Documentation](../../README.md) · [Modèle d'ADR](../../templates/decision.md)

Un ADR explique un choix durable : contexte, options, décision, conséquences et motif
de réexamen. Une décision de stack, un changement de stockage ou un contrat optique
mérite un ADR ; chaque fonction ou correction n'en nécessite pas.

Numéroter `0001-titre.md`, `0002-titre.md`, etc. États : proposé, adopté, remplacé.
Une décision remplacée reste consultable et lie sa remplaçante ; les nouveaux choix
ne doivent pas réécrire l'histoire comme s'ils avaient toujours été retenus.

| ADR | État | Objet |
|---|---|---|
| [0001](0001-mvp-foundation.md) | Adopté pour le MVP actuel | Monolithe Python, moteur indépendant, SQLite, UI provisoire |

Cet ADR décrit les choix effectivement présents. Il ne constitue pas une validation
anticipée des technologies du SaaS ou du futur design system.
