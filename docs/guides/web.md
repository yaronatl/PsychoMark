# Utiliser la correction web

[Documentation](../README.md)

## Lancer l'interface web

```bash
# Depuis la racine du dépôt
uv sync --frozen --extra dev
.venv/bin/python -m psychomark.web --port 8000
```

Pour activer le rechargement pendant le développement hors Codespaces, ajouter
`--reload` à cette commande. Le mode normal n'injecte pas de script d'actualisation
et n'expose pas l'endpoint de suivi des sources.

Le serveur écoute en local sur le port 8000. Utiliser le navigateur de la machine
qui exécute le serveur, ou le mécanisme d'accès aux ports de son environnement
de développement. Le démarrage du serveur dans un environnement cloud ne rend
pas automatiquement son port accessible depuis un ordinateur personnel.
L'interface fonctionne sans compilation JavaScript et sans CDN.

Le bouton **Essayer la démonstration** crée un examen de 20 questions et analyse
une copie synthétique. Il présente 12 bonnes réponses, 2 absences de réponse et
6 cas à vérifier. Aucune note finale n'est affichée avant résolution de ces cas.

Parcours normal :

1. **Créer un examen** : nom, modèle, sections actives et questions (par exemple
   `1-20` ou `1-10, 15`).
2. **Renseigner le corrigé** avec les sélecteurs ou la saisie rapide d'une liste
   de réponses par section. Toutes les questions sélectionnées doivent avoir
   une bonne réponse avant l'enregistrement.
3. **Importer les copies** : une ou plusieurs images ou des PDF multipages.
   Chaque page devient une copie indépendante. Les erreurs de fichiers/pages
   sont présentées sans inventer de réponses.
4. **Consulter la correction** : bonnes réponses, erreurs, absences, cas à
   vérifier, résultats par section et images complète/annotée.
5. **Vérifier les ambiguïtés** sur l'extrait d'image sans annotation. Confirmer
   un choix, une absence ou une réponse multiple. Une réponse multiple confirmée
   compte comme incorrecte. On peut aussi rectifier une lecture automatique
   initialement jugée nette, ou rétablir la décision du moteur.
6. **Obtenir la note et exporter** la correction en CSV ou JSON.

Barème actuel : **1 point par bonne réponse, 0 sinon**, conversion en pourcentage
et note sur 20. Les questions non sélectionnées n'entrent pas dans le dénominateur.
Tant qu'il reste une question incertaine, multiple non confirmée ou illisible,
la note finale reste absente ; une fourchette de points et les réponses déjà
établies sont affichées. Ce n'est pas le score officiel du psychométrique.

Les examens, copies et historiques persistent après rechargement et redémarrage
dans `artifacts/web/`. Les données de chaque copie incluent une **photographie
du corrigé et de la géométrie au moment de l'import**. Modifier un examen affecte
les futurs imports ; les anciennes copies gardent leur version de corrigé.
Les décisions manuelles sont enregistrées à part, sans écraser la lecture du
moteur. Les modifications concurrentes périmées sont refusées.

Pour utiliser vos modèles calibrés ou un autre dossier de données :

```bash
.venv/bin/python -m psychomark.web \
  --template artifacts/private/ecole-v1.json \
  --template artifacts/private/autre-feuille-v1.json \
  --data-dir artifacts/private/web --port 8000
```

Sans `--template`, une feuille synthétique est générée au premier démarrage.
**Elle ne permet pas de lire arbitrairement une photo NITE ou Adar.** L'ajout et
la calibration de modèles restent des opérations en ligne de commande, décrites
dans le [guide du moteur](cli.md). Le modèle disponible au moment de l'import doit correspondre à la copie.

L'application est un **prototype local pour un seul opérateur**, sans comptes
ni isolation entre organismes. Elle écoute par défaut sur `127.0.0.1` et ne doit
pas être exposée comme un SaaS public avec des données d'élèves. L'option `--host`
permet de choisir l'interface d'écoute pour un environnement de développement
maîtrisé. La durée de conservation et la suppression des données ne sont pas
encore gérées par l'interface. Conserver le dossier SQLite et ses images ensemble.
