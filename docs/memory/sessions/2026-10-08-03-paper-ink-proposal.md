# Session 2026-10-08-03 — Première proposition papier/encre

- Date utilisateur : 2026-10-08, Asia/Jerusalem ; intervention le 7 octobre en UTC.
- Agent : Codex.
- Départ : `docs/visual-direction`, `9ba8d54` ; travail sur `feat/paper-ink-design`.
- Demande : construire une première refonte calme, chaude, claire, serif, papier/stylo/encre,
  ancienne et moderne ; Renance préféré, reMarkable cité. Puis demande explicite de Torph
  et invitation à utiliser Be UI.

## Réalisé

Accueil éditorial navigable, scène QCM illustrative, présentation du parcours et accès
à la vraie démonstration. Atelier, configuration, import et correction harmonisés.
Polices Instrument Serif et Geist locales, licences conservées. Scans non filtrés,
extraits contenus en hauteur. Sur petit écran, sélection d’une question vers le panneau
avec focus et retour vers la question. Démonstration et états provisoires conservés.

Torph vanilla installé et verrouillé ; transition réelle des libellés d’analyse,
respect du mouvement réduit et nettoyage après requête. Catalogue Button Be UI consulté,
comportement de pression adapté au CSS natif ; aucun composant React officiel installé.
Build local des assets, licence MIT et empreinte exacte du style injecté pour CSP.
Node ajouté à la configuration Codespaces/CI, sans dépendance Node au runtime Python.

[ADR 0002](../../architecture/decisions/0002-local-browser-dependencies.md), guides,
[direction](../../product/visual-direction.md), [PRODUCT.md](../../../PRODUCT.md),
[DESIGN.md](../../../DESIGN.md) et sidecar Impeccable assurent la reprise.
La proposition n’est pas encore une validation graphique par l’utilisateur.

## Vérification

- `scripts/dev.py check` : Ruff et format conformes, 35 documents sans lien local cassé,
  **56 tests réussis** ; avertissement Starlette/httpx préexistant.

- Installation gelée Python, `npm ci --ignore-scripts`, `npm run build` et script
  `.devcontainer/setup.sh` exécutés. Le script setup retire l’extra browser ; réinstallé
  explicitement pour les tests. Node local 24.19.0 ; conteneur/CI configurés Node 22.
- Paquet Python construit : présence des polices, modules JS et empreinte CSP vérifiée
  dans la wheel.
- Chromium : accueil, clavier/skip, largeurs 320/390/768, mouvement réduit, création,
  corrigé, import, note provisoire, deux décisions, note 12/20, rechargement, CSV,
  navigation mobile aller/retour et vraie démo. Torph testé en mouvement normal pendant
  la requête, contrôle désactivé et ressources nettoyées ; aucune erreur console/CSP.
- Parcours live : démarrage idempotent, actualisation CSS, protection du formulaire,
  redémarrage Python, base conservée. Une reprise du test attendait encore le symbole
  « ＋ » supprimé du bouton ; sélecteur actualisé au libellé, puis parcours réussi.
- Revue Impeccable séparée : trois demandes (aller/retour mobile, mention illustrative
  mobile, suppression des flèches typographiques). Verdict final **ship sur ces trois
  corrections**, toutes résolues. Torph n’est pas évalué visuellement par les captures fixes.
- Détecteur exécuté une fois : avertissements de polices fréquentes conservées car elles
  servent le brief. Résolution locale de `/assets/style.css` impossible pour ce détecteur ;
  CSS aussi fourni directement. Ne pas présenter ce contrôle comme un audit exhaustif.
- reMarkable inaccessible via réseau ; référence traitée à partir de la description
  utilisateur. Aucun contenu de son site actuel prétendu examiné.

Captures locales : `.impeccable/review/desktop.png`, `mobile.png`, `correction.png`,
`correction-mobile.png`, `correction-mobile-selection.png`. Un premier extrait mobile
capturé avant chargement a été rejeté puis recapturé après `img.decode()`.
Les fichiers sont ignorés et ne contiennent que des données synthétiques.

## Environnement et publication

Le brouillon cloud a été enregistré avec les champs `install_script` et `start_skill`
actualisés pour npm/Torph et le workflow visuel. Réseau et secrets conservés. Cette
sauvegarde ne publie pas l’environnement : revue/enregistrement puis publication dans
les paramètres restent nécessaires pour activer la nouvelle version enregistrée.

Le checkout cloud et le Codespace de l’utilisateur restent séparés. Aucune
synchronisation de son Codespace, fusion de branche, publication de site ni exécution
de CI distante n’est déduite d’un push Git. Rebuild complet du conteneur non exécuté ici.

## Suite

Recueillir les retours visuels et ajuster la proposition ; décider d’un framework global
seulement si nécessaire. Poursuivre ensuite calibration et mesure sur copies réelles
autorisées, sans confondre les tests de parcours et la précision de l’OMR.
