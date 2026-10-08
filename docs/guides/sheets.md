# Ajouter une feuille dans l’interface

[Documentation](../README.md) · [Créer et corriger un examen](web.md)

Cette fonction crée un **modèle de feuille** : une image vierge et les positions des
cases à lire. Le modèle ne contient pas les bonnes réponses. Il pourra servir à
plusieurs examens, complets ou courts, avec des corrigés différents.

## Parcours sans terminal

1. Dans l’application, ouvrir **Mes feuilles → Ajouter une feuille**.
2. Importer la feuille vierge : PNG, JPG, TIFF simple ou PDF d’une page, 64 Mio maximum.
   Préférer le PDF original ou un scan bien droit. Une photo en perspective n’est pas
   une bonne référence pour tracer des grilles régulières.
3. Donner un nom reconnaissable, par exemple « Feuille du centre — version octobre ».
4. Pour chaque grille, saisir son numéro, le nombre de questions imprimées et le
   nombre de choix par question. Puis cliquer, dans cet ordre :
   - coin supérieur gauche du cadre imprimé ;
   - coin inférieur droit du même cadre ;
   - centre de la réponse 1 de la question 1 ;
   - centre de la réponse 1 de la dernière question ;
   - centre de la dernière réponse de la question 1.
5. Ajuster la demi-largeur et la demi-hauteur des cases. Les ellipses doivent épouser
   les cases imprimées. Le zoom agrandit la feuille ; les coordonnées permettent
   de corriger un clic ou de placer les repères au clavier. Cliquer **Ajouter la grille**.
6. Répéter pour les autres grilles. **Ajuster** permet de reprendre une grille ;
   appliquer ensuite les ajustements. **Retirer** enlève une grille du brouillon.
7. Cliquer **Vérifier et sauvegarder les zones**. Python vérifie la géométrie, le cadre,
   la référence vierge et les repères nécessaires à l’alignement. L’aperçu calculé
   montre les zones effectivement utilisées. Le brouillon est sauvegardé à cette étape.
8. Dans **Essayer sur une copie remplie**, importer une copie de cette même feuille.
   Comparer les réponses détectées avec l’original et la version annotée. Les marques
   multiples, lectures incertaines et zones illisibles restent signalées. Une lecture
   « unique » peut elle aussi être incorrecte : cet essai n’est pas une mesure de précision.
9. Vérifier toutes les ellipses de l’aperçu, cocher la confirmation, puis cliquer
   **Enregistrer le modèle**. L’essai sur une copie est recommandé, pas obligatoire.
10. **Créer un examen avec cette feuille** ouvre l’éditeur avec ce modèle sélectionné.
    Choisir les sections réellement utilisées et les questions à noter, puis fournir
    le corrigé et importer les copies comme auparavant.

Les repères en cours ne sont pas enregistrés avant l’étape de vérification. Une alerte
prévient la sortie de l’éditeur avec du travail non sauvegardé ; l’actualisation de
développement attend aussi la fin du travail. Après vérification, le brouillon
se retrouve dans **Mes feuilles**, même après redémarrage du serveur.

## Ce que cette version accepte

- Plusieurs grilles régulières, différentes tailles et questions en ligne ou colonne.
- De 2 à 100 questions imprimées par grille dans l’assistant, 2 à 10 choix, jusqu’à 50 grilles.
  Un examen peut sélectionner une seule question d’une grille plus grande.
- Cadres imprimés utilisables et suffisamment de détails stables pour l’alignement.
- Référence de 128 à 10 000 pixels par côté, au plus 20 mégapixels.

Une feuille sans cadre, des cases irrégulières, une référence courbée ou fortement
perspective nécessitent une évolution du moteur. L’assistant ne reconnaît pas
universellement la structure d’une nouvelle feuille : vous placez les repères,
l’application calcule les positions intermédiaires.

Un modèle enregistré est figé pour préserver les examens existants. Pour changer
les positions, importer une nouvelle version. Un recalibrage du brouillon invalide
l’essai précédent. Les anciennes versions techniques restent sur disque ; la
suppression et le nettoyage depuis l’interface ne sont pas encore disponibles.

## Où vivent les données et comment cela fonctionne

L’application appelle `calibration.py`, puis `Engine.analyze()` pour l’essai.
Aucun apprentissage ni service d’IA externe n’intervient. Le corrigé est transmis
seulement au module de notation lors d’un véritable examen.

Les fichiers restent dans `artifacts/web/sheets/` par défaut, avec le reste des données
privées de l’application. Sauvegarder **tout le dossier de données**, pas uniquement
SQLite. Les modèles enregistrés sont chargés au redémarrage, sans option `--template`
ni commande supplémentaire. Le workflow CLI existant reste disponible.

**NITE et Adar ne sont pas déclarés compatibles par cette livraison.** L’assistant
permet de les configurer si leurs fichiers et leurs caractéristiques conviennent ;
il faudra ensuite comparer les résultats à des copies réellement corrigées à la main.

## Comprendre un essai « illisible »

Le résultat distingue désormais deux étapes :

- **Alignement non confirmé** : la photo n’a pas été rapprochée de la référence
  avec assez de précision. Aucune réponse n’est interprétée.
- **Alignement réussi**, puis un contrôle refusé : les grilles peuvent être repérées
  alors que leurs cases sont trop petites dans la photo, qu’un cadre correspond mal,
  que des zones sont hors champ ou que la netteté relative est insuffisante.

Les motifs sont affichés en français avec les sections et questions concernées.
Le **Détail technique du diagnostic** conserve les mesures du moteur. Ce sont des
conditions de refus, pas la preuve que l’utilisateur a mal photographié sa copie.
En particulier, un PDF idéal et une impression photographiée peuvent présenter un
écart de netteté important : il faut examiner les fichiers avant d’ajuster le contrôle.

Pour faire examiner un blocage, cliquer **Télécharger le diagnostic (images incluses)**.
Le ZIP contient la référence vierge, la configuration exacte, l’aperçu des zones,
la copie décodée, son annotation et le résultat brut. Aucun examen, corrigé ou autre
copie n’y est ajouté. Les images ne sont pas anonymisées ; le bouton télécharge
le fichier, sans l’envoyer à un tiers. Ce diagnostic suffit à reproduire l’essai avec
la version du moteur indiquée dans le résultat. Il fonctionne aussi pour les essais
conservés avant l’ajout de ce bouton, sans refaire la calibration.
