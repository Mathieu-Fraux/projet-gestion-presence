# Système de vérification de présence de fichiers

Application Windows qui vérifie, dans chaque sous-dossier d'un dossier parent, la présence de fichiers attendus, puis crée un rapport Excel.

## Fonctionnalités disponibles

- Choix du dossier parent par saisie du chemin ou avec l'explorateur de fichiers Windows.
- Choix du dossier et du nom du rapport Excel avec « Enregistrer sous… ».
- Vérification de plusieurs fichiers attendus dans chaque sous-dossier direct.
- Recherche par texte contenu dans le nom du fichier.
- Recherche par modèle à partir d'un exemple de nom de fichier.
- Définition d'un modèle par positions uniques ou plages de positions.
- Types de positions disponibles : chiffre, lettre, caractère spécial et texte exact.
- Affichage de la correspondance entre les emplacements et les caractères de l'exemple.
- Ajout, modification et suppression des fichiers attendus et des positions d'un modèle.
- Enregistrement, chargement et suppression de recherches sauvegardées.
- Barre de progression pendant l'analyse et la génération du rapport.
- Génération d'un rapport Excel sur un seul onglet, avec une synthèse puis le détail par sous-dossier.

## Lancer l'application

Depuis la racine du projet, installer les dépendances puis lancer :

```powershell
python -m pip install -r requirements.txt
python src/main.py
```

Les recherches sauvegardées sont conservées dans `data/recherches.json`.

Deux recherches sont disponibles : texte contenu dans le nom, ou modèle défini depuis un exemple. Dans un modèle, seules les positions ajoutées sont recherchées ; les autres portions peuvent varier. Le fonctionnement détaillé et un exemple complet sont disponibles dans le [guide d'utilisation](GUIDE_UTILISATION.md).

## À faire

- Corriger des bugs.
- permettre de modifier les recherche a partir du type de fichier (jpeg,txt...)
