# Guide d'utilisation

Cette application vérifie que les fichiers attendus sont présents dans chaque sous-dossier d'un dossier parent. Elle crée ensuite un rapport Excel indiquant les fichiers manquants.

## 1. Choisir les dossiers

1. Dans **Dossier parent à analyser**, saisissez le chemin du dossier ou cliquez sur **Parcourir…**.
2. Dans **Emplacement du rapport Excel**, saisissez le chemin complet du fichier à créer ou cliquez sur **Enregistrer sous…**. Le fichier porte l'extension `.xlsx`.

L'application analyse uniquement les sous-dossiers directs du dossier parent. Avec `C:\Contrats` comme dossier parent, elle analyse donc `C:\Contrats\Client A`, `C:\Contrats\Client B`, etc.

## 2. Ajouter un fichier attendu

Donnez un **libellé de la recherche**. Ce nom apparaît dans le rapport lorsqu'un fichier est absent, par exemple `Devis` ou `Contrat signé`.

### Texte contenu dans le nom

Cette méthode vérifie que le texte saisi apparaît quelque part dans le nom du fichier. Avec le texte `devis`, les fichiers `devis.pdf`, `22_10_2045_devis_client.docx` et `ancien_devis.xlsx` sont trouvés.

### Modèle à partir d'un exemple

Cette méthode décrit les parties importantes d'un nom sans imposer les parties qui peuvent changer.

1. Saisissez un exemple, par exemple `22_10_2045_devis de patate`.
2. Cliquez sur **Définir les positions du modèle…**.
3. Le tableau affiche la position et le caractère correspondant :

   ```text
   Emplacement | 1 | 2 | 3 | 4 | 5 | 6 | 7 | ...
   Caractère   | 2 | 2 | _ | 1 | 0 | _ | 2 | ...
   ```

4. Ajoutez les parties à vérifier, puis cliquez sur **Valider les positions**.
5. Cliquez sur **Ajouter** dans la fenêtre principale pour ajouter le fichier attendu.

Seules les positions ajoutées sont recherchées. Tout ce qui n'est pas décrit peut changer.

#### Types disponibles

- **Chiffre** : chaque position de la plage doit contenir un chiffre de `0` à `9`.
- **Lettre** : chaque position de la plage doit contenir une lettre.
- **Caractère spécial** : le caractère spécial de l'exemple doit être identique. Cela impose par exemple `_`, `-` ou `.`.
- **Exact** : le ou les caractères de l'exemple doivent être identiques. Cette option convient à un mot fixe, par exemple `devis`.

#### Exemple : date suivie de `_devis`

Pour l'exemple `22_10_2045_devis de patate`, créez les règles suivantes :

| Positions | Type | Signification |
| --- | --- | --- |
| 1 à 2 | chiffre | jour à deux chiffres |
| 3 | caractère spécial | underscore `_` |
| 4 à 5 | chiffre | mois à deux chiffres |
| 6 | caractère spécial | underscore `_` |
| 7 à 10 | chiffre | année à quatre chiffres |
| 11 | caractère spécial | underscore `_` |
| 12 à 16 | exact | mot `devis` |

Ce modèle reconnaît `01_09_2026_devis client.pdf` et `30_12_2030_devis.docx`. Il ne reconnaît pas `01-09-2026_devis.pdf`, car les tirets ne correspondent pas aux underscores demandés, ni `01_09_2026_facture.pdf`, car le mot `devis` est absent. La partie après `devis` peut varier.

## 3. Modifier ou supprimer une règle

Dans **Fichiers attendus**, sélectionnez une ligne : ses données sont recopiées dans les champs. Modifiez-les, puis cliquez sur **Modifier**. Le bouton **Supprimer** retire la règle.

Dans **Définition de modèle**, sélectionnez une ligne du tableau des positions, modifiez la saisie correspondante puis cliquez sur **Modifier la sélection**. Le bouton **Supprimer la sélection** retire la position choisie.

## 4. Enregistrer une recherche

1. Donnez un nom dans **Nom de la sauvegarde**.
2. Cliquez sur **Enregistrer**.

Les recherches sont conservées dans `data/recherches.json`. Sélectionnez une recherche, puis cliquez sur **Charger** pour retrouver ses paramètres. Donner le même nom remplace la sauvegarde existante.

## 5. Lancer et lire le rapport

Cliquez sur **Lancer la recherche et créer le rapport**. La barre de progression indique le dossier analysé, puis la création du rapport.

Le fichier Excel contient un seul onglet : une synthèse en haut, puis une ligne par sous-dossier avec le nombre et les libellés des fichiers manquants, ainsi que les éventuelles erreurs d'accès.
