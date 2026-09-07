"""Génération du rapport Excel à partir des résultats de l'analyse."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter


def generer_rapport_excel(resultat: dict[str, Any], chemin_rapport: str) -> Path:
    """Crée un fichier XLSX comprenant une synthèse et le détail par sous-dossier."""
    destination = Path(chemin_rapport)
    if destination.suffix.lower() != ".xlsx":
        destination = destination.with_suffix(".xlsx")
    destination.parent.mkdir(parents=True, exist_ok=True)

    classeur = Workbook()
    synthese = classeur.active
    synthese.title = "Synthèse"

    # Cette feuille résume les chiffres essentiels pour une lecture immédiate.
    synthese.append(["Rapport de vérification de présence"])
    synthese.append(["Dossier parent", resultat["dossier_parent"]])
    synthese.append(["Sous-dossiers analysés", resultat["nombre_dossiers"]])
    synthese.append(["Fichiers manquants", resultat["nombre_fichiers_manquants"]])
    synthese["A1"].font = Font(bold=True, size=14)
    synthese.column_dimensions["A"].width = 28
    synthese.column_dimensions["B"].width = 70

    detail = classeur.create_sheet("Détail")
    entetes = ["Nom du dossier", "Chemin", "Nombre de fichiers manquants", "Fichiers manquants", "Erreur"]
    detail.append(entetes)
    couleur_entete = PatternFill("solid", fgColor="1F4E78")
    for cellule in detail[1]:
        cellule.font = Font(bold=True, color="FFFFFF")
        cellule.fill = couleur_entete

    # Une ligne par dossier permet de filtrer et trier facilement dans Excel.
    for item in resultat["resultats"]:
        detail.append([
            item["nom_dossier"], item["chemin_dossier"], len(item["fichiers_manquants"]),
            ", ".join(item["fichiers_manquants"]), item["erreur"],
        ])
    detail.freeze_panes = "A2"
    detail.auto_filter.ref = detail.dimensions
    for index, largeur in enumerate([28, 65, 28, 50, 50], start=1):
        detail.column_dimensions[get_column_letter(index)].width = largeur

    classeur.save(destination)
    return destination
