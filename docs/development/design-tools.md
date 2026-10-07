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

## Be UI : configuration préparée, connexion non validée

L'URL fournie est `https://mcp.beui.dev/mcp`. Elle est déclarée dans
[la configuration Codex](../../.codex/config.toml) et
[la configuration VS Code/Codespaces](../../.vscode/mcp.json).
Ce sont deux clients possibles du même serveur ; ils ne sont pas automatiquement
connectés par l'écriture de ces fichiers. Aucun secret n'y est enregistré.

La commande demandée a aussi été exécutée sous sa syntaxe Codex correcte :
`codex mcp add beui --url https://mcp.beui.dev/mcp`. Elle échoue car le dossier global
`/run/codex-environment/codex-home` est en lecture seule. `codex mcp get beui --json`
confirme qu'aucun serveur de ce nom n'est chargé par cette instance de Codex. La
configuration de projet ci-dessus est donc une préparation, pas une activation réussie.

Le proxy de l'environnement actuel refuse la connexion HTTPS avec une erreur 403,
avant même un échange MCP. Le domaine `mcp.beui.dev` a été ajouté au **brouillon** de
configuration réseau Codex, en conservant les domaines des gestionnaires de paquets.
Cette sauvegarde n'active pas la règle dans la session actuelle. Le serveur n'est donc
pas présenté comme connecté et ses outils n'ont pas pu être recensés ou testés.

Pour lever ce blocage dans Codex cloud, les paramètres de l'environnement doivent être
enregistrés puis publiés avec cette règle. Un client prenant en charge MCP doit ensuite
charger la configuration du projet (et sa confiance, si demandée). Une configuration
de dépôt ne permet pas à l'agent d'ajouter lui-même des outils à une conversation déjà
ouverte. Refaire une initialisation MCP et une liste des outils avant de le déclarer prêt.

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
