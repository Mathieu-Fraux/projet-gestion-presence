"""Création et validation des règles utilisées pour reconnaître les fichiers."""

from __future__ import annotations

import re
from typing import Any


def normaliser_texte(texte: str, sensible_a_la_casse: bool) -> str:
    """Retourne le texte tel quel ou en minuscules selon l'option de casse."""
    return texte if sensible_a_la_casse else texte.casefold()


def construire_expression_modele(
    exemple: str, regles_positions: list[dict[str, Any]], sensible_a_la_casse: bool = True
) -> re.Pattern[str]:
    """Construit une expression régulière à partir d'un exemple et de positions décrites.

    Les positions affichées à l'utilisateur commencent à 1. Les caractères qui ne
    sont pas explicitement marqués comme variables restent donc strictement égaux
    à ceux de l'exemple (un point reste un point et un tiret reste un tiret).
    """
    if not exemple:
        raise ValueError("Un exemple de nom de fichier est nécessaire.")

    # Une position ne peut appartenir qu'à une seule règle, afin d'éviter toute
    # ambiguïté dans le modèle décrit par l'utilisateur.
    positions: dict[int, str] = {}
    for regle in regles_positions:
        debut, fin = int(regle["debut"]), int(regle["fin"])
        if debut < 1 or fin < debut or fin > len(exemple):
            raise ValueError("Une position indiquée est en dehors de l'exemple.")
        for position in range(debut, fin + 1):
            if position in positions:
                raise ValueError("Deux règles ne peuvent pas couvrir la même position.")
            positions[position] = regle["type"]

    morceaux: list[str] = []
    # On parcourt chaque caractère : ceux sans règle sont protégés avec re.escape,
    # ce qui donne précisément le comportement attendu pour '.' et '-'.
    for index, caractere in enumerate(exemple, start=1):
        type_regle = positions.get(index)
        if type_regle == "chiffre":
            morceaux.append(r"\d")
        elif type_regle == "lettre":
            morceaux.append(r"[A-Za-zÀ-ÖØ-öø-ÿ]")
        elif type_regle == "quelconque":
            morceaux.append(r".")
        # Ces choix sont volontaires et lisibles : un utilisateur peut préciser
        # qu'une position doit contenir un point ou un tiret, sans apprendre Regex.
        elif type_regle == "point":
            morceaux.append(re.escape("."))
        elif type_regle == "tiret":
            morceaux.append(re.escape("-"))
        elif type_regle == "underscore":
            morceaux.append(re.escape("_"))
        elif type_regle:
            raise ValueError(f"Type de position inconnu : {type_regle}")
        else:
            morceaux.append(re.escape(caractere))

    indicateurs = 0 if sensible_a_la_casse else re.IGNORECASE
    return re.compile("^" + "".join(morceaux) + "$", indicateurs)


def fichier_correspond(nom_fichier: str, regle: dict[str, Any]) -> bool:
    """Indique si un nom de fichier satisfait une règle créée dans l'IHM."""
    mode = regle["mode"]
    valeur = regle["valeur"]
    sensible_a_la_casse = regle.get("sensible_a_la_casse", False)

    if mode == "exact":
        return normaliser_texte(nom_fichier, sensible_a_la_casse) == normaliser_texte(
            valeur, sensible_a_la_casse
        )
    if mode == "contient":
        return normaliser_texte(valeur, sensible_a_la_casse) in normaliser_texte(
            nom_fichier, sensible_a_la_casse
        )
    if mode == "modele":
        expression = construire_expression_modele(
            valeur, regle.get("regles_positions", []), sensible_a_la_casse
        )
        return expression.fullmatch(nom_fichier) is not None

    raise ValueError(f"Mode de recherche inconnu : {mode}")
