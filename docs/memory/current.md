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

**Priorité actuelle : prendre en charge la feuille NITE montrée par l’utilisateur**
comme modèle fourni avec le produit, avant un assistant générique de création de modèles.
Lire [le cadrage du pilote](../product/nite-pilot.md). Le PNG est visible dans le chat,
mais son fichier n’est pas accessible au programme ici ; demander le fichier téléchargeable
ou le PDF source pour calibrer. Ne pas annoncer de compatibilité NITE à ce stade.

Consulter [la dernière session](sessions/2026-10-08-03-paper-ink-proposal.md) et Git.
Recueillir le retour visuel sur l’accueil et la correction, puis affiner dans la direction
exprimée. Les captures de revue sont locales sous `.impeccable/review/` (ignorées par Git).
La branche de travail est `feat/paper-ink-design` ; sa présence sur GitHub ne synchronise
pas le Codespace séparé de l’utilisateur. Vérifier le statut réel avant toute intégration.

Ensuite : feuille vierge et scans autorisés pour calibrer un premier modèle réel et
constituer une vérité de référence. Suivre les [priorités](../product/roadmap.md).
