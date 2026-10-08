# Session 2026-10-07-02 — Skills de design et Be UI

- Date : 2026-10-07, contexte utilisateur Asia/Jerusalem ; même date UTC.
- Intervenant : Codex, installation explicitement demandée par l'utilisateur.
- Départ : `main`, commit `3c0bc21`. Branche de travail : `chore/design-skills`.
- Objectif : installer les six sources demandées et préparer le serveur MCP indiqué,
  sans engager la refonte avant réception des inspirations.

## Réalisé

Installation locale au projet via `npx --yes skills@1.7.1 add SOURCE --skill NOM --agent codex --yes`.
Les six dossiers et leurs ressources sont dans `.agents/skills/`, accompagnés de
`skills-lock.json` et des licences amont. Le dépôt d'Emil contenant 14 skills, son
skill principal `emil-design-eng` a été sélectionné. Aucun autre skill de ses dépôts
ou des dépôts Anthropic/Taste/Pro Max n'est installé.

Configurations MCP Be UI ajoutées pour Codex et VS Code. Le proxy refuse le domaine
avec un 403 CONNECT ; ajout de `mcp.beui.dev` au brouillon réseau, sans retirer les
domaines prédéfinis. Sauvegarder ce brouillon ne change pas le réseau courant.

Documentation des rôles et de la priorité des inspirations. Consignes de communication
enregistrées : agir autant que possible, expliquer ce qui est fait, distinguer une
référence technique d'une action utilisateur indispensable. Ruff exclut les sources
fournies par les skills pour préserver leurs fichiers ; pas de modification applicative.

## Vérification

- L'outil `skills list --agent codex --json` recense les six installations.
- Les six SKILL.md sont présents ; configurations TOML et JSON valides, même URL Be UI.
- Recherche UI/UX Pro Max : `keyboard focus --domain ux -n 1`, résultat pertinent obtenu.
- Impeccable : téléchargement avec contrôle SHA-256 par son lanceur ; `engine-probe`
  retourne `impeccable-engine 0.1.11`. Cache privé dans `/workspace/.cache/impeccable`.
- `.venv/bin/python scripts/dev.py check` : Ruff, format et liens documentaires réussis ;
  53 tests passent (un avertissement Starlette/httpx). Après ajout de la session,
  27 documents contrôlés, aucun lien de fichier local cassé.
- Connexion Be UI non validée ; aucun outil distant recensé, aucune authentification
  supposée. Aucun hook Impeccable ni serveur de modification visuelle activé.
- Sur la demande complémentaire de l'utilisateur, exécution de
  `codex mcp add beui --url https://mcp.beui.dev/mcp` : échec, configuration globale
  `/run/codex-environment/codex-home` en lecture seule. `codex mcp get beui --json`
  ne trouve pas le serveur. Les configurations du projet restent préparées seulement.

## Reprise

[Guide des outils](../../development/design-tools.md), [cadre UI](../../product/ui.md).
Les inspirations et la stack frontend restent à préciser. Une installation de skill
shadcn ne signifie pas que la bibliothèque est déjà intégrée au produit.

Pour Be UI, enregistrer/publier la configuration d'environnement avec le domaine
préparé, puis charger le serveur dans un client MCP compatible et vérifier son
initialisation et la liste d'outils. Ces étapes n'ont pas été effectuées dans cette session.
L'API GitHub est également refusée dans l'environnement ; ne pas annoncer de PR créée
sans preuve. La publication Git utilise la branche dédiée.
