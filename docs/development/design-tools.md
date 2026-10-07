# Skills de design et serveur Be UI

[Documentation](../README.md) · [Cadre visuel](../product/ui.md)

## Installé dans le projet

Le 7 octobre 2026, les six sources demandées ont été installées pour Codex avec
`skills` 1.7.1 dans `.agents/skills/`. Ces guides et leurs ressources sont versionnés
dans Git : un checkout du dépôt les récupère sans réexécuter `npx` à chaque session.
[skills-lock.json](../../skills-lock.json) conserve les sources, chemins et empreintes.
Le verrou de l'outil n'est pas une garantie qu'une réinstallation depuis une branche
amont rendrait les mêmes octets ; les copies versionnées dans Git sont notre référence.

| Source | Skill local | Rôle |
|---|---|---|
| `emilkowalski/skill` | [emil-design-eng](../../.agents/skills/emil-design-eng/SKILL.md) | Finition, interactions et animations utiles |
| `pbakaus/impeccable` | [impeccable](../../.agents/skills/impeccable/SKILL.md) | Conception, revue et amélioration de l'interface |
| `anthropics/skills@frontend-design` | [frontend-design](../../.agents/skills/frontend-design/SKILL.md) | Direction graphique intentionnelle et fidélité au brief |
| `shadcn-ui/ui@shadcn` | [shadcn](../../.agents/skills/shadcn/SKILL.md) | Utilisation correcte des composants si cette bibliothèque est retenue |
| `Leonxlnx/taste-skill@design-taste-frontend` | [design-taste-frontend](../../.agents/skills/design-taste-frontend/SKILL.md) | Landing et pages marketing ; sa version actuelle exclut les dashboards |
| `nextlevelbuilder/ui-ux-pro-max-skill@ui-ux-pro-max` | [ui-ux-pro-max](../../.agents/skills/ui-ux-pro-max/SKILL.md) | Recherche locale de recommandations UX et accessibilité |

Le dépôt d'Emil proposait 14 skills au moment de l'installation. Son skill central
`emil-design-eng` a été retenu ; les variantes Swift/Expo et autres extensions ne sont
pas installées. Les autres dépôts ont été limités au skill demandé, sans ajout de leurs
outils non concernés. Les références, scripts et données livrés avec ces six skills
sont conservés ; ce ne sont pas des dépendances de l'application PsychoMark.

## Usage et priorité

1. Lire les choix du produit et les inspirations de l'utilisateur avant toute tâche UI.
2. Choisir un guide principal adapté à la tâche ; consulter les compléments utiles,
   sans appliquer simultanément six directions graphiques différentes.
3. Les inspirations validées, la lisibilité des corrections et les comportements métier
   priment sur les styles proposés par défaut. Ne pas inventer une identité en leur absence.
4. Pour une retouche, conserver la direction existante ; documenter un changement global
   uniquement lorsqu'il est demandé. Comparer le rendu aux références dans le navigateur.
5. Ces fichiers sont disponibles sur disque. Selon le client, leur découverte automatique
   peut nécessiter une nouvelle session ; on peut les lire directement à leurs chemins.

Les recommandations ne donnent pas la permission de publier, de modifier des services
externes ou d'envoyer des scans d'élèves à un tiers. Aucun hook de modification automatique
ni serveur de prévisualisation Impeccable n'a été activé pendant cette installation.

## Outils auxiliaires

UI/UX Pro Max utilise Python et ses données locales, sans dépendance Python supplémentaire.
Exemple de vérification pour un développeur, pas une action demandée à l'utilisateur :

```bash
.venv/bin/python .agents/skills/ui-ux-pro-max/scripts/search.py 'keyboard focus' --domain ux -n 1
```

Dans les exemples amont, remplacer les chemins de plugin Claude par le chemin de ce
skill local. Ne pas générer un design system automatiquement avant les inspirations.

Impeccable possède aussi un moteur auxiliaire téléchargé à la première utilisation
avec contrôle SHA-256. Dans Codex cloud, son cache doit être accessible en écriture :

```bash
IMPECCABLE_HOME=/workspace/.cache/impeccable sh .agents/skills/impeccable/scripts/impeccable engine-probe
```

L'état réellement observé de ce moteur est consigné dans la session d'installation.
Ses références Markdown restent lisibles même si son exécutable est indisponible.

## Be UI : accès vérifié depuis le projet

L'URL fournie est `https://mcp.beui.dev/mcp`. Elle est déclarée dans
[la configuration Codex](../../.codex/config.toml) et
[la configuration VS Code/Codespaces](../../.vscode/mcp.json).

Au 8 octobre 2026 (Asia/Jerusalem), la connexion HTTPS et l'initialisation MCP
fonctionnent. Les outils disponibles sont `list_components`, `search_components`,
`get_component` et `get_install_command`. Une recherche et une récupération du composant
Button ont été vérifiées. Aucun composant n'a été installé dans l'application.

La configuration globale de ce Codex cloud reste sur un système de fichiers en lecture
seule : la commande `codex mcp add` ne peut pas y écrire. Le projet est accessible en
écriture, et Codex accepte un paramètre explicite pour lire la définition de Be UI :

```bash
codex -c 'mcp_servers.beui.url="https://mcp.beui.dev/mcp"' mcp get beui --json
```

Cette commande de référence a été exécutée par l'agent : elle confirme la définition du
serveur pour ce processus CLI, mais n'ajoute pas un outil natif à la conversation ouverte.
Les autorisations du système ne sont pas changées ; `HOME` et `CODEX_HOME` restent intacts.

Pour utiliser Be UI ici sans dépendre de cette écriture globale, le petit client
[scripts/beui.py](../../scripts/beui.py) lit directement la configuration du projet et
appelle le serveur MCP. Il utilise `httpx`, déjà présent dans l'extra `dev`.
Commandes de référence pour l'agent ou un développeur, sans action utilisateur requise :

```bash
.venv/bin/python scripts/beui.py tools
.venv/bin/python scripts/beui.py components --category motion
.venv/bin/python scripts/beui.py search button
.venv/bin/python scripts/beui.py component button
.venv/bin/python scripts/beui.py install-command button --package-manager npm
```

Ce client sait consulter le catalogue Be UI au format JSON ; ce n'est pas un client MCP
universel. Il valide les réponses et signale les erreurs avec un code de sortie non nul.
Les sources et commandes retournées sont affichées seulement, jamais exécutées.
Les requêtes sont des termes de recherche ou identifiants publics, pas des copies d'élèves.

Les fichiers de configuration restent utilisables par des clients compatibles dans un
projet de confiance. Leur chargement natif dépend du client hôte ; il n'est pas activé
rétroactivement dans ce chat par la création d'un fichier. L'accès direct ci-dessus est
opérationnel et permet de poursuivre le travail sans intervention de l'utilisateur.

## Maintenance

Ne pas actualiser automatiquement ces sources à chaque démarrage. Une mise à jour se
fait dans un changement dédié, avec comparaison des instructions et ressources et mise
à jour du verrou. Les fichiers amont restent intacts ; Ruff exclut `.agents/skills/`
pour ne pas reformater le code des fournisseurs. Les tests PsychoMark restent inchangés.

Les licences fournies sont conservées : [Anthropic](../../.agents/skills/frontend-design/LICENSE.txt),
[Emil](../vendor-licenses/emilkowalski--skill.txt),
[Impeccable](../vendor-licenses/pbakaus--impeccable.txt),
[shadcn](../vendor-licenses/shadcn-ui--ui.txt),
[Taste](../vendor-licenses/Leonxlnx--taste-skill.txt),
[UI/UX Pro Max](../vendor-licenses/nextlevelbuilder--ui-ux-pro-max-skill.txt).
