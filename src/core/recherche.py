"""Analyse des sous-dossiers et calcul des fichiers attendus manquants."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from core.patterns import fichier_correspond

ProgressionCallback = Callable[[int, int, str], None]


def verifier_dossiers(
    dossier_parent: str, regles: list[dict[str, Any]], progression: ProgressionCallback | None = None
) -> dict[str, Any]:
    """Vérifie, dans chaque sous-dossier direct, la présence de toutes les règles.

    La fonction ne dépend pas de l'interface : elle retourne uniquement des données
    structurées, qui peuvent ensuite être affichées ou exportées vers Excel.
    """
    parent = Path(dossier_parent)
    if not parent.is_dir():
        raise ValueError("Le dossier parent indiqué n'existe pas ou n'est pas un dossier.")
    if not regles:
        raise ValueError("Ajoutez au moins un fichier attendu avant de lancer la recherche.")

    # Le projet vérifie les dossiers situés juste sous le dossier parent, comme le
    # faisait le prototype initial. Les fichiers placés directement dans le parent
    # ne sont donc pas considérés comme un dossier à analyser.
    try:
        sous_dossiers = sorted((item for item in parent.iterdir() if item.is_dir()), key=lambda x: x.name.casefold())
    except PermissionError as erreur:
        raise ValueError(f"Impossible de lire le dossier parent : {erreur}") from erreur

    resultats: list[dict[str, Any]] = []
    total = len(sous_dossiers)
    for index, dossier in enumerate(sous_dossiers, start=1):
        if progression:
            progression(index - 1, total, f"Analyse de : {dossier.name}")

        try:
            # Seuls les fichiers présents directement dans le sous-dossier sont lus.
            fichiers = [item.name for item in dossier.iterdir() if item.is_file()]
            manquants = [
                regle["libelle"]
                for regle in regles
                if not any(fichier_correspond(fichier, regle) for fichier in fichiers)
            ]
            resultats.append({
                "nom_dossier": dossier.name,
                "chemin_dossier": str(dossier),
                "fichiers_trouves": fichiers,
                "fichiers_manquants": manquants,
                "erreur": "",
            })
        except (PermissionError, OSError, ValueError) as erreur:
            # Une erreur sur un dossier est conservée dans le rapport sans empêcher
            # l'analyse des autres dossiers.
            resultats.append({
                "nom_dossier": dossier.name,
                "chemin_dossier": str(dossier),
                "fichiers_trouves": [],
                "fichiers_manquants": [],
                "erreur": str(erreur),
            })

        if progression:
            progression(index, total, f"Analyse terminée : {dossier.name}")

    return {
        "dossier_parent": str(parent),
        "nombre_dossiers": total,
        "nombre_fichiers_manquants": sum(len(item["fichiers_manquants"]) for item in resultats),
        "resultats": resultats,
    }
