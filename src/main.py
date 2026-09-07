"""Point d'entrée de l'application Windows de vérification de présence."""

from tkinter import Tk

from ihm.fenetre_principale import FenetrePrincipale


def main() -> None:
    """Crée la fenêtre Tkinter puis donne le contrôle à l'interface graphique."""
    racine = Tk()
    FenetrePrincipale(racine)
    racine.mainloop()


if __name__ == "__main__":
    main()
