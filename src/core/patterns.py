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

    Les positions affichées à l'utilisateur commencent à 1. Seules les portions
    explicitement ajoutées sont recherchées : toutes les autres parties du nom
    peuvent varier. Cela permet par exemple d'imposer une date et le mot « devis »
    sans imposer le reste du fichier.
    """
    if not exemple:
        raise ValueError("Un exemple de nom de fichier est nécessaire.")

    if not regles_positions:
        raise ValueError("Décrivez au moins une position pour le modèle.")

    # Une position ne peut appartenir qu'à une seule règle, afin d'éviter toute
    # ambiguïté dans le modèle décrit par l'utilisateur.
    positions: set[int] = set()
    for regle in regles_positions:
        debut, fin = int(regle["debut"]), int(regle["fin"])
        if debut < 1 or fin < debut or fin > len(exemple):
            raise ValueError("Une position indiquée est en dehors de l'exemple.")
        for position in range(debut, fin + 1):
            if position in positions:
                raise ValueError("Deux règles ne peuvent pas couvrir la même position.")
            positions.add(position)

    morceaux: list[str] = ["^"]
    position_suivante = 1
    # Les règles sont traitées dans l'ordre du nom. Chaque espace non décrit entre
    # deux règles devient « .* » : il n'est pas vérifié et peut donc changer.
    for regle in sorted(regles_positions, key=lambda item: int(item["debut"])):
        debut, fin = int(regle["debut"]), int(regle["fin"])
        if debut > position_suivante:
            morceaux.append(r".*")
        longueur = fin - debut + 1
        texte_exemple = exemple[debut - 1 : fin]
        type_regle = regle["type"]
        if type_regle == "chiffre":
            morceaux.append(rf"\d{{{longueur}}}")
        elif type_regle == "lettre":
            morceaux.append(rf"[A-Za-zÀ-ÖØ-öø-ÿ]{{{longueur}}}")
        elif type_regle == "caractere_special":
            if any(caractere.isalnum() for caractere in texte_exemple):
                raise ValueError("« Caractère spécial » ne peut contenir ni lettre ni chiffre.")
            morceaux.append(re.escape(texte_exemple))
        elif type_regle == "exact":
            morceaux.append(re.escape(texte_exemple))
        elif type_regle:
            raise ValueError(f"Type de position inconnu : {type_regle}")
        position_suivante = fin + 1

    # Tout ce qui suit la dernière partie décrite n'a volontairement pas
    # d'importance : extensions, nom de client, version, etc. sont autorisés.
    if position_suivante <= len(exemple):
        morceaux.append(r".*")
    morceaux.append("$")

    indicateurs = 0 if sensible_a_la_casse else re.IGNORECASE
    return re.compile("".join(morceaux), indicateurs)


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
