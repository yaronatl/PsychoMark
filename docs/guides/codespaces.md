# Travailler dans Codespaces

[Documentation](../README.md)

## Développer entièrement dans GitHub Codespaces

Le dépôt contient une configuration `.devcontainer/` pour travailler et tester
dans le navigateur, sans installer le projet sur un ordinateur personnel.

1. Dans le dépôt GitHub **yaronatl/PsychoMark**, ouvrir **Code → Codespaces →
   Create codespace on main**.
2. Attendre la construction du conteneur et l'installation automatique. Le
   serveur démarre automatiquement avec le rechargement de développement.
3. L'aperçu du port **8000** est configuré pour s'ouvrir dans le navigateur. S'il
   ne s'ouvre pas, utiliser l'onglet **Ports**, puis **Open in Browser** sur 8000.
4. Conserver la visibilité du port sur **Private**, valeur par défaut de
   Codespaces. L'application n'a pas de comptes utilisateurs propres.
5. Cliquer sur **Essayer la démonstration** dans PsychoMark.

Les sources, dépendances, examens et copies restent dans le Codespace. Les
modifications de Python redémarrent le serveur ; les modifications de l'interface
actualisent le navigateur sous quelques secondes. Une saisie non enregistrée
ou un traitement en cours retarde l'actualisation pour ne pas perdre le travail.
Les données de `artifacts/web/` sont conservées quand on arrête puis reprend le
**même** Codespace, mais ne sont pas envoyées dans GitHub. Exporter ce qu'il faut
conserver avant de supprimer un Codespace.

Cette actualisation concerne les fichiers du Codespace. **Cette conversation
Codex et un Codespace sont deux machines différentes.** Les changements effectués
ici doivent être envoyés dans GitHub, puis récupérés dans le terminal Codespaces
avec `git pull --ff-only`. Les modifications faites directement dans Codespaces
s'affichent sans cette étape. Si les dépendances changent, exécuter aussi
`bash .devcontainer/setup.sh`, puis redémarrer le Codespace si nécessaire.

La configuration utilise Python 3.12, uv 0.12.19 et les versions de `uv.lock`.
Les scripts ne recréent pas les données et ne lancent pas de serveur supplémentaire
si PsychoMark est déjà prêt. Journaux : `artifacts/codespaces/server-8000.log`.
Pour relancer le serveur si nécessaire :

```bash
.venv/bin/python .devcontainer/start.py
```

Si le port 8000 est occupé par un autre service, le script le signale sans arrêter
ce service. Une modification de `.devcontainer/` nécessite **Rebuild Container**.
L'utilisation effective de Codespaces dépend des droits et du quota du compte
GitHub ; la présence de la configuration ne crée pas à elle seule un Codespace.
