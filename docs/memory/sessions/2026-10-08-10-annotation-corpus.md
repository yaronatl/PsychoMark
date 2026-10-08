# Session 2026-10-08-10 — S02, corpus et annotation humaine

- Date UTC : 2026-10-08.
- Intervenants : Codex, agent backend sur `corpus.py` et ses tests ; intégration,
  navigateur, skills et documentation dans la session principale.
- Branche : `feat/annotation-corpus`, départ `dfaa622` (`docs/monochrome-findings`).
- Objectif : créer, reprendre et exporter des observations humaines, y compris sans
  alignement, sans modifier les décisions optiques ni la notation.

## Réalisé

Espace **Annotations**, import image/PDF/diagnostic, comparaison vierge/copie, états
visuels par choix, alias de relecture, question complète et position vérifiée séparément.
Source zoomable et rectangle manuel par deux clics ou coordonnées clavier. Révisions,
historique, sauvegarde atomique, groupes et doublons de pixels contrôlés, exports privés.
Aucune nouvelle dépendance et aucun changement des seuils du moteur.

Les deux diagnostics réels connus s’importent en développement : 90 questions chacun,
90 extraits proposés sur le premier et aucun sur le second après refus d’alignement.
Les observations restent vides et l’autorisation d’apprentissage fausse. L’essai vit
sous `artifacts/private/s02-corpus-check-dxo051on/`, hors Git ; aucun scan réel dans les
captures navigateur ou les tests versionnés.

## Application des skills

Frontend-design, Emil, Impeccable et UI UX Pro Max consultés pour la surface native.
Contexte Impeccable chargé une fois ; inspection desktop/mobile groupée. Shadcn est
consulté, sans installer de composants React dans la stack native. Taste exclut ce
type d’outil de travail de son périmètre. Be UI répond via le client du projet : son
Button est consulté, les boutons partagés restent l’adaptation native existante.

| Before | After | Why |
|---|---|---|
| Aucun parcours d’annotation indépendant | Source et référence, observations vierges, note absente | Limiter l’influence du corrigé et des prédictions |
| Repérage refusé bloquant l’examen des zones | Cadrage manuel et alternative clavier | Conserver les exemples difficiles sans fausse géométrie |
| Retour d’erreur générique sans focus dédié | Alerte focalisable et saisie conservée | Permettre une reprise après erreur ou conflit |
| Navigation mobile prévue pour trois liens | Quatrième lien avec retour à la ligne | Accès aux annotations sans débordement |

Le détecteur Impeccable a été exécuté une fois (sortie 2, avis présents). Il ne résout
pas les routes FastAPI `/assets/` depuis l’HTML local et signale plusieurs tokens/polices
historiques, ainsi que la légende 12 px du nouvel écran. Cette taille reprend les
légendes existantes ; la direction typographique est conservée. Ce résultat n’est pas
présenté comme un audit d’accessibilité réussi. Le navigateur charge les assets réels.

## Vérification

| Contrôle | Résultat observé | Limite |
|---|---|---|
| `scripts/dev.py check` | Réussi : Ruff, format, liens locaux, 89 tests | Fixtures synthétiques ; avertissement Starlette/httpx existant |
| `scripts/dev.py browser` | Réussi : parcours historique et annotations, reprise, conflit, cadrage et export | Chromium ; pas tous les navigateurs |
| Largeurs 320, 390, 768 et 1440 px | Aucun débordement horizontal ; captures synthétiques desktop/mobile examinées | Pas un audit exhaustif d’accessibilité |
| Import des deux diagnostics réels | Réussi, refus géométriques conservés et labels vides | Ni précision ni intention de l’élève évaluées |
| `scripts/dev.py live` | Non exécuté : démarrage/rechargement inchangés | Protection de saisie vérifiée par le parcours navigateur |

Les essais navigateur ont révélé puis permis de corriger les noms accessibles des
champs et une expression HTML `pattern` incompatible avec le mode `v` de Chromium.
Le test de concurrence provoque et vérifie volontairement un HTTP 409 ; toute autre
erreur de console fait échouer le parcours.

## Documentation et reprise

[Guide](../../guides/annotations.md), [API](../../architecture/api.md),
[ADR 0005](../../architecture/decisions/0005-private-annotation-corpus.md) et
[plan](../../product/hybrid-omr-plan.md) actualisés.

L’outillage S02 est disponible ; les observations réelles restent à recueillir.
Le cadrage manuel valide une question, pas chacune de ses cases. Métadonnées figées,
pas de détection de quasi-doublons ni d’accord inter-annotateurs automatisé. Aucun
modèle ML entraîné. Prochain lot technique : S03, puis comparaisons photographiques S04.
Publication de branche et synchronisation du Codespace sont des opérations distinctes.

Publication : commit `48715cf` poussé sur `origin/feat/annotation-corpus`. La création
automatique de PR via `gh pr create` échoue : `Post https://api.github.com/graphql:
Forbidden`. La branche est disponible sur GitHub ; aucune PR créée, fusion dans
`main` ou synchronisation du Codespace n’est annoncée.
