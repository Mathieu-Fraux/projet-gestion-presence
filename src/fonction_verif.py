"""
Script de vérification de présence de fichiers devis dans plusieurs sous-dossiers
Pattern attendu: JJ_MM_AAAA_devis*
"""

# === LIBRAIRIES NÉCESSAIRES ===

import os


import re

from colorama import Fore, Style, init


# Initialisation de colorama pour Windows
init(autoreset=True)


CHEMIN_DOSSIER_PARENT = "./contrat"


# === FONCTION PRINCIPALE ===

def verifier_sousDossier_fichierDevis(chemin_dossier_parent):
    """
    Vérifie la présence de fichiers devis avec le bon format dans tous les sous-dossiers.
     """
    
    # === VÉRIFICATION DU DOSSIER PARENT ===
    

    if not os.path.exists(chemin_dossier_parent):
        print(f"{Fore.RED}Erreur: Le dossier parent '{chemin_dossier_parent}' n'existe pas.{Style.RESET_ALL}")
        return True
    

    if not os.path.isdir(chemin_dossier_parent):
        print(f"{Fore.RED}Erreur: '{chemin_dossier_parent}' n'est pas un dossier.{Style.RESET_ALL}")
        return True
    
    # === DÉFINITION DU PATTERN DE VALIDATION ===
    
    # Pattern d'expression régulière pour valider le nom de fichier
    # Explication du pattern:
    # ^              : Début du nom de fichier (le pattern doit commencer dès le début)
    # \d{2}          : Exactement 2 chiffres (jour: 01-31)
    # \d{4}          : Exactement 4 chiffres (année: ex. 2024)
    # _              : Un underscore (séparateur)
    # devis          : Le mot "devis" en toutes lettres
    # .*             : N'importe quels caractères pour la fin du nom
    pattern = r"^\d{2}_\d{2}_\d{4}_devis.*"
    
    # === LISTAGE DES SOUS-DOSSIERS ===
    
    # Liste tous les éléments dans le dossier parent
    try:
        ToutSousParents = os.listdir(chemin_dossier_parent)
    # Pas la permission de lire le dossier
    except PermissionError:
        print(f"{Fore.RED}Erreur: Pas de permission pour lire le dossier parent '{chemin_dossier_parent}'.{Style.RESET_ALL}")
        return True
    
    # Filtrer pour ne garder que les sous-dossiers et ne pas lire les fichier
    sous_dossiers = [
        ToutSousParent for ToutSousParent in ToutSousParents 
        if os.path.isdir(os.path.join(chemin_dossier_parent, ToutSousParent))
    ]
    
    # Vérifier qu'il y a des sous-dossiers
    if not sous_dossiers:
        print(f"{Fore.RED}Erreur: Aucun sous-dossier trouvé dans '{chemin_dossier_parent}'.{Style.RESET_ALL}")
        return True
    
    # === COMPTEURS GLOBAUX ===
    
    # Compteurs pour le résumé final
    total_fichiers_valides = 0
    total_fichiers_invalides = 0
    total_dossiers_analyses = 0
    
    # En-tête du rapport
    print("\n" + "=" * 70)
    print(f"verification de {len(sous_dossiers)} sous-dossier")
    print("===========\n")
    
    # === parcourir chaque sous-dossier ===
    
    # Parcourir chaque sous-dossier 
    for dossier in sous_dossiers:
        # Construire le chemin complet vers le sous-dossier
        chemin_primaire = os.path.join(chemin_dossier_parent, dossier)
        
        # Afficher le nom du sous-dossier en cours d'analyse
        print(f" {Fore.CYAN}{dossier}{Style.RESET_ALL}")
        print("-------")
        
        # Vérifier que le sous-dossier existe (sécurité supplémentaire)
        if not os.path.exists(chemin_primaire):
            print(f"  {Fore.RED} Erreur: Le sous-dossier n'existe plus.{Style.RESET_ALL}\n")
            continue
        
        # Vérifier que c'est bien un dossier
        if not os.path.isdir(chemin_primaire):
            print(f"  {Fore.RED}⚠ Erreur: N'est pas un dossier valide.{Style.RESET_ALL}\n")
            continue
        
        # === ANALYSE DES FICHIERS DU SOUS-DOSSIER ===
        
        # Ces listes sont créées à CHAQUE itération pour ne pas mélanger les résultats
        fichiers_valides = []
        fichiers_invalides = []
        
        # Lister tous les fichiers dans le sous-dossier actuel
        try:
            fichiers = os.listdir(chemin_primaire)
        # Gestion de l'erreur si on n'a pas la permission de lire ce sous-dossier
        except PermissionError:
            print(f"  {Fore.RED} Erreur: Pas de permission pour lire ce sous-dossier.{Style.RESET_ALL}\n")
            continue
        
        # Parcourir chaque fichier du sous-dossier
        for fichier in fichiers:
            # Construire le chemin complet vers le fichier
            chemin_complet = os.path.join(chemin_primaire, fichier)
            
            # Vérifier que c'est bien un fichier 
            # os.path.isfile() retourne True si c'est un fichier, False sinon
            if os.path.isfile(chemin_complet):
                # re.match() retourne un objet Match si le pattern correspond, None sinon
                if re.match(pattern, fichier):
                    fichiers_valides.append(fichier)
                else:
                    fichiers_invalides.append(fichier)
        
        # === AFFICHAGE DES RÉSULTATS POUR CE SOUS-DOSSIER ===
        
        # Afficher les fichiers valides trouvés dans ce sous-dossier
        if fichiers_valides:
            print(f"  {Fore.GREEN} Fichiers valides ({len(fichiers_valides)}):{Style.RESET_ALL}")
            # Parcourir et afficher chaque fichier valide
            for fichier in fichiers_valides:
                print(f"  -{fichier}\n")
        
        # Afficher les fichiers invalides trouvés dans ce sous-dossier
        if fichiers_invalides:
            print(f"  {Fore.RED} Fichiers invalides ({len(fichiers_invalides)}):{Style.RESET_ALL}")
            # Parcourir et afficher chaque fichier invalide
            for fichier in fichiers_invalides:
                print(f"  -{fichier}\n")

        
        # Afficher un avertissement si le sous-dossier est vide
        if not fichiers_valides and not fichiers_invalides:
            print(f"  {Fore.YELLOW} Aucun fichier trouvé dans ce sous-dossier{Style.RESET_ALL}\n")
        
        # Mettre à jour les compteurs globaux
        total_fichiers_valides += len(fichiers_valides)
        total_fichiers_invalides += len(fichiers_invalides)
        total_dossiers_analyses += 1
    
    # === AFFICHAGE DU RÉSUMÉ FINAL ===
    
    print("==========" )
    print("RÉSUMÉ GLOBAL")
    print("==========")
    print(f"Sous-dossiers analysés: {total_dossiers_analyses}")
    print(f"Fichiers valides trouvés: {Fore.GREEN}{total_fichiers_valides}{Style.RESET_ALL}")
    print(f"Fichiers invalides trouvés: {Fore.RED}{total_fichiers_invalides}{Style.RESET_ALL}")
    print("==========")
    
    # === MESSAGE FINAL ===
    
    # Déterminer si des problèmes ont été trouvés
    if total_fichiers_invalides > 0:
        # Des fichiers invalides ont été trouvés
        print(f"{Fore.RED}document manquant - {total_fichiers_invalides} fichier(s) invalide(s) trouvé(s){Style.RESET_ALL}")
        return True  # Retourne True pour indiquer un problème
    else:
        # Tout est conforme
        print(f"{Fore.GREEN}RAS - tous les fichiers devis sont valides{Style.RESET_ALL}")
        return False  # Retourne False pour indiquer que tout est OK


# === EXÉCUTION DU SCRIPT ===

if __name__ == "__main__":
    """
    Point d'entrée du script.
    Cette partie ne s'exécute que si le fichier est lancé directement
    (et non s'il est importé comme module dans un autre script)
    """
    print(f"Vérification du dossier parent: {CHEMIN_DOSSIER_PARENT}")
    print("-" * 70)
    
    # Appel de la fonction principale et récupération du résultat
    problemes_detectes = verifier_sousDossier_fichierDevis(CHEMIN_DOSSIER_PARENT)
    