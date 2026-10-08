# État actuel

Mis à jour le 2026-10-08 (Asia/Jerusalem). Cette page décrit le dépôt, pas un déploiement garanti.

## Disponible

- Moteur OMR Python/OpenCV, CLI et interface FastAPI française. Examen configurable,
  corrigé, import, vérification humaine, notes brutes et exports ; SQLite et instantanés.
- Codespaces avec actualisation, documentation, ADR et commandes de qualité.
- Six skills de design installés ; Be UI accessible via le client `scripts/beui.py`.
- Première **proposition visuelle papier/encre implémentée** : accueil éditorial,
  espace de travail et correction harmonisés, responsive et navigation clavier.
- Renance reste la référence principale ; l’utilisateur a précisé une ambiance calme,
  chaude et claire, serif, papier/stylo/encre, évoquant reMarkable. Lire
  [la direction](../product/visual-direction.md), [DESIGN.md](../../DESIGN.md) et
  [le cadre UI](../product/ui.md) avant une modification visuelle.
- Torph demandé explicitement, installé en vanilla et utilisé pour le libellé d’analyse.
  Boutons Be UI **adaptés en CSS natif**, pas composants React officiels installés.
  Polices et module servis localement ; build/verrou npm et CSP à empreinte exacte.
- Accueil sur `/` ou `#/home` ; examens directement sur `#/exams`.
- Diagnostic des essais de feuille : motifs de refus en français, distinction entre
  alignement et contrôles locaux, export ZIP reproductible avec les images du seul essai.
  Présentation également disponible pour les anciens essais ; seuils du moteur inchangés.
- **Ajouter une feuille** sur `#/sheets` : import d’une référence vierge, cinq repères
  par grille, aperçu Python, essai d’une copie et modèle disponible pour les examens.
  [Guide](../guides/sheets.md), [ADR 0003](../architecture/decisions/0003-visual-sheet-library.md).
  Les brouillons sont sauvegardés après vérification ; les modèles enregistrés sont figés.
  La bibliothèque persiste sous le dossier privé de données, sans migration SQLite.

## Limites et choix ouverts

- Proposition graphique encore à apprécier par l’utilisateur ; aucun retour de validation
  du rendu final reçu. Ne pas confondre réalisation et identité approuvée.
- Aucun taux de précision réel annoncé ; NITE/Adar non calibrés, essais synthétiques seulement.
- Pas de SaaS public : ni comptes, ni isolation par entreprise, ni abonnement.
- Framework frontend général et bibliothèque UI restent à choisir. Torph n’impose
  aucune migration React/Tailwind. Voir [ADR 0002](../architecture/decisions/0002-local-browser-dependencies.md).
- Global Codex en lecture seule ; Be UI fonctionne via le client du projet.
- CI distante et rebuild complet Codespaces avec Node restent à vérifier. Installation
  et parcours testés dans cette machine ne prouvent pas le déploiement ailleurs.

## Reprise

**Demande actuelle : rendre l’ajout de feuilles accessible sans scripts manuels.**
L’assistant est implémenté sur la branche `feat/sheet-builder`, issue de `docs/nite-pilot`
et contenant la proposition graphique précédente. Sa publication ne synchronise pas
le Codespace distinct de l’utilisateur. Ne pas prétendre qu’il est déjà sur `main`.

Consulter [la dernière session](sessions/2026-10-08-05-readability-diagnostics.md) et vérifier Git.
L’utilisateur a rencontré un refus « illisible » sur une photo de feuille imprimée,
avec une référence PDF propre. Les fichiers de cet essai sont dans son Codespace,
pas dans ce checkout. Le nouveau diagnostic permet d’examiner ce cas ; la cause réelle
n’est pas encore établie. Ne pas annoncer que la lecture de sa copie est corrigée.
L’utilisateur peut désormais importer son fichier NITE directement dans l’application,
sans dépendre de l’accès du chat aux pièces jointes. L’assistant attend une référence
à plat et des grilles régulières avec cadres imprimés ; il ne reconnaît pas automatiquement
une mise en page inconnue. Pas de taux de précision annoncé ni de modèle NITE préinstallé.

Prochaine étape : accompagner la calibration de la vraie feuille NITE, puis comparer
les lectures à des copies annotées manuellement. Lire [le pilote](../product/nite-pilot.md).
La confirmation de l’aperçu et les essais synthétiques ne valent pas validation terrain.
Continuer à recueillir les retours visuels dans la direction papier/encre.
