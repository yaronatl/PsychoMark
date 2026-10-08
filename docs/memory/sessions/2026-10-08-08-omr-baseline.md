# Session — S01, référence de comparaison et régions

Date : 2026-10-08 (Asia/Jerusalem). Branche : `feat/omr-baseline`.
Commit de départ : `ced6175`.

## Livraison

L’utilisateur autorise le démarrage de S01. `psychomark.baseline` rejoue une image avec
le moteur historique, exporte résultats, résumé français, rapport HTML local, régions,
masques et annotations humaines vides. Les fichiers de sortie existants ne sont jamais
écrasés. L’outil n’est pas intégré à l’interface de correction ; il prépare S02.

Les [contrats](../../architecture/regions.md) précisent coordonnées, transformations,
masques potentiels et consommateurs historiques. Le [guide](../../development/omr-baseline.md)
décrit l’exécution, les métriques et les limites. Aucun changement de moteur, seuil,
base, dépendance ou modèle ML. La normalisation reste celle de la page entière.

Une revue indépendante a trouvé puis fait corriger la fusion des masques de ROI
obliques et l’absence de vérification d’identité des images comparées. Ces deux cas
sont couverts par les tests. Un résultat ancien sans empreinte de source est explicitement
signalé comme non vérifié ; un rapport récent permet une vérification stricte.

## Diagnostic privé

Le cas déjà disponible a été relancé. 90 questions et 360 cases exportées ; 90 refus,
aucun changement de décision par rapport au diagnostic précédent. Alignement global
réussi et mêmes mesures locales ; seules de petites différences numériques de matrice
empêchent l’égalité stricte de tous les diagnostics. L’ancienne extraction n’a pas
d’empreinte source : l’association est celle des fichiers du ZIP précédemment extrait.

Les refus de résolution et de cadre persistent. Inspection exploratoire d’extraits :
marques visibles, positions globalement cohérentes dans cet échantillon, aucune annotation
humaine inventée et aucune conclusion de précision. Ce cas reste du développement connu.

Rapport final privé : `artifacts/private/baselines/s01-photo-v1/summary.md` et `review.html`.
Une seconde exécution sous `s01-photo-replay/` sert à vérifier la reproduction locale.
Les images, annotations et rapports ne sont pas publiés dans Git.

## Vérifications

`.venv/bin/python scripts/dev.py check` réussi : Ruff, format, 47 documents sans lien
local cassé et **75 tests réussis**, dont 9 nouveaux tests S01. Avertissement existant
Starlette/httpx, sans échec. `git diff --check` réussi.

Deux relectures réelles : mêmes décisions que le diagnostic d’origine ; différence
maximale de coefficients de matrice d’environ 1,8 × 10⁻⁹. La seconde exécution locale
confirme source, décisions et diagnostics strictement identiques à la première.

Rapport vérifié avec Chromium : 90 articles, 270 images chargées, détails repliés puis
ouverts sans erreur JavaScript. Le navigateur géré refuse les URL `file://` ; contrôle
effectué via un serveur temporaire limité à localhost, arrêté à la fin. Aucun parcours
de l’application principale exécuté : ses routes et assets restent inchangés.
Les captures et scans privés ne sont pas ajoutés à la CI. Pas d’entraînement ni de
mesure de précision terrain réalisés.

Publication : branche `feat/omr-baseline` poussée sur GitHub. Création de PR tentée
vers `docs/hybrid-omr-plan`, mais l’API GitHub renvoie `Forbidden`. Aucune PR créée,
aucune fusion dans `main` et aucune synchronisation du Codespace revendiquée.

## Reprise

S02 : construire la saisie/reprise des annotations, définir les feuilles physiques
et la séparation des données. S03 peut exploiter les contrats sur des fichiers distincts.
Conserver l’accès privé aux originaux et sorties ; Git ne synchronise pas ces données
ni l’environnement distinct du Codespace. Aucun travail manuel demandé à l’utilisateur
pour exécuter les scripts de S01.
