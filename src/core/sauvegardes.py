"""Persistance des configurations de recherche dans un fichier JSON local."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def charger_recherches(chemin_sauvegarde: Path) -> list[dict[str, Any]]:
    """Lit les recherches sauvegardées ou retourne une liste vide au premier lancement."""
    if not chemin_sauvegarde.exists():
        return []
    try:
        contenu = json.loads(chemin_sauvegarde.read_text(encoding="utf-8"))
        return contenu if isinstance(contenu, list) else []
    except (OSError, json.JSONDecodeError):
        # Un fichier devenu illisible ne doit pas empêcher d'ouvrir l'application.
        return []


def enregistrer_recherches(chemin_sauvegarde: Path, recherches: list[dict[str, Any]]) -> None:
    """Enregistre toutes les recherches au format JSON, avec une écriture lisible."""
    chemin_sauvegarde.parent.mkdir(parents=True, exist_ok=True)
    chemin_sauvegarde.write_text(
        json.dumps(recherches, ensure_ascii=False, indent=2), encoding="utf-8"
    )
