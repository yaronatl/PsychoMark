# Session — Expliquer les refus de lecture des essais

Date : 2026-10-08. Branche de travail : `fix/sheet-readability-diagnostics`, issue de
`feat/sheet-builder`. La livraison met aussi à jour cette branche utilisateur en avance rapide.

## Problème rapporté

L’utilisateur a créé une référence depuis une image/PDF propre, puis essayé une photo
de la feuille imprimée et remplie. Il voit les cases repérées mais reçoit seulement
« Le moteur n’a pas pu lire cette copie correctement ». Les fichiers de cet essai
sont dans son Codespace et ne sont pas disponibles dans ce checkout.

Le code distingue déjà l’échec d’alignement des refus après alignement : cadres,
netteté relative, résolution, zones coupées. L’interface masquait ces informations.
Une référence PDF idéale et une impression photographiée peuvent présenter un écart
de netteté ; cela reste une hypothèse pour cette copie, pas une cause identifiée.

## Changement

- `readability.py` traduit les conditions de refus, conserve les raisons techniques
  et regroupe les sections/questions concernées. Les ambiguïtés ne deviennent pas
  des problèmes de netteté. Aucun seuil ni décision optique n’est modifié.
- L’interface indique si l’alignement a réussi, explique les refus et affiche les
  mesures dans un détail technique. Les anciens essais obtiennent le diagnostic
  à la lecture, sans modification des extractions persistées.
- Export ZIP de l’essai courant : référence, géométrie, aperçu, copie décodée,
  annotation et résultat brut. Pas de corrigé, base de données ou autre copie.
  L’interface indique que les images sont incluses. Aucun envoi automatique.
- Les pointeurs sont pris sous verrou, les fichiers sources sont immuables et
  l’archive temporaire est fermée après transmission. Une autre version d’essai
  que celle affichée est refusée par `expected_test`, sans export silencieux différent.

## Vérifications

- `scripts/dev.py check` : **66 tests réussis**, Ruff, format et liens vérifiés.
- Test ciblé de reproduction et d’export périmé réexécuté après l’ajout du contrôle
  `expected_test` : réussi. Le ZIP recharge bien le moteur et reproduit l’extraction.
- `scripts/dev.py browser` : réussi, avec refus réel d’alignement (image sans repères),
  refus de cadre sur page alignée, diagnostic persistant, téléchargement et retour
  à une copie lisible. Le scénario de correction existant passe aussi.
- Syntaxe JavaScript et diff vérifiés ; capture synthétique locale dans
  `artifacts/browser/sheet-unreadable.png`.
- `live` non réexécuté : aucun changement du démarrage ou du rechargement.
- Avertissement existant Starlette/httpx conservé. Pas de nouvelle dépendance.

## Reprise

Après récupération de la mise à jour dans son Codespace, l’utilisateur peut rouvrir
sa feuille et télécharger le diagnostic de l’essai déjà conservé. Ce ZIP permettra
l’analyse concrète de sa copie. **La cause réelle de son refus reste à diagnostiquer** ;
ne pas présenter cette amélioration de diagnostic comme une validation des photos NITE.

Voir [le guide](../../guides/sheets.md) et [l’API](../../architecture/api.md).
