"""Fenêtre principale Windows pour configurer et lancer une vérification."""

from __future__ import annotations

import queue
import threading
from copy import deepcopy
from pathlib import Path
from tkinter import BooleanVar, StringVar, Tk, Toplevel, filedialog, messagebox, ttk
from typing import Any

from core.rapport_excel import generer_rapport_excel
from core.recherche import verifier_dossiers
from core.sauvegardes import charger_recherches, enregistrer_recherches


MODES = {
    "Texte contenu dans le nom": "contient",
    "Modèle à partir d'un exemple": "modele",
}


class FenetrePrincipale:
    """Réunit les paramètres de recherche, les sauvegardes et le lancement du rapport."""

    def __init__(self, racine: Tk) -> None:
        """Initialise les variables, puis dessine les zones de la fenêtre."""
        self.racine = racine
        self.racine.title("Vérification de présence de fichiers")
        self.racine.minsize(900, 650)
        self.file_messages: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.regles: list[dict[str, Any]] = []
        # Cette liste temporaire reçoit les positions créées dans la fenêtre de modèle.
        self.regles_positions_en_cours: list[dict[str, Any]] = []
        self.recherches = charger_recherches(Path("data/recherches.json"))
        self.chemin_dossier = StringVar()
        self.chemin_rapport = StringVar()
        self.nom_sauvegarde = StringVar()
        self.libelle = StringVar()
        self.mode = StringVar(value="Texte contenu dans le nom")
        self.valeur = StringVar()
        self.sensible_casse = BooleanVar(value=False)
        self.statut = StringVar(value="Prêt à configurer une recherche.")

        self._construire_interface()
        self._rafraichir_sauvegardes()

    def _construire_interface(self) -> None:
        """Construit les cadres et commandes de l'interface principale."""
        conteneur = ttk.Frame(self.racine, padding=14)
        conteneur.pack(fill="both", expand=True)
        conteneur.columnconfigure(1, weight=1)
        conteneur.rowconfigure(3, weight=1)

        # Le premier bloc définit le dossier dont les sous-dossiers seront analysés.
        dossier = ttk.LabelFrame(conteneur, text="1. Dossier parent à analyser", padding=10)
        dossier.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        dossier.columnconfigure(0, weight=1)
        ttk.Entry(dossier, textvariable=self.chemin_dossier).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(dossier, text="Parcourir…", command=self._choisir_dossier).grid(row=0, column=1)

        # Le second bloc contient la destination précise du rapport Excel demandé.
        rapport = ttk.LabelFrame(conteneur, text="2. Emplacement du rapport Excel", padding=10)
        rapport.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        rapport.columnconfigure(0, weight=1)
        ttk.Entry(rapport, textvariable=self.chemin_rapport).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(rapport, text="Enregistrer sous…", command=self._choisir_rapport).grid(row=0, column=1)

        # Cette zone permet d'ajouter plusieurs fichiers attendus avant la recherche.
        regles = ttk.LabelFrame(conteneur, text="3. Fichiers attendus", padding=10)
        regles.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        for colonne in range(4):
            regles.columnconfigure(colonne, weight=1 if colonne in (0, 2) else 0)
        ttk.Label(regles, text="Libellé de la recherche").grid(row=0, column=0, sticky="w")
        ttk.Label(regles, text="Méthode").grid(row=0, column=1, sticky="w")
        ttk.Label(regles, text="Nom / texte / exemple").grid(row=0, column=2, sticky="w")
        ttk.Entry(regles, textvariable=self.libelle).grid(row=1, column=0, sticky="ew", padx=(0, 6))
        ttk.Combobox(regles, textvariable=self.mode, values=list(MODES), state="readonly", width=28).grid(row=1, column=1, sticky="ew", padx=(0, 6))
        ttk.Entry(regles, textvariable=self.valeur).grid(row=1, column=2, sticky="ew", padx=(0, 6))
        ttk.Button(regles, text="Ajouter", command=self._ajouter_regle).grid(row=1, column=3, sticky="ew")
        ttk.Checkbutton(regles, text="Respecter majuscules/minuscules", variable=self.sensible_casse).grid(row=2, column=0, columnspan=2, sticky="w", pady=(5, 0))
        ttk.Button(regles, text="Définir les positions du modèle…", command=self._ouvrir_positions).grid(row=2, column=2, columnspan=2, sticky="e", pady=(5, 0))

        self.table_regles = ttk.Treeview(regles, columns=("libelle", "mode", "valeur"), show="headings", height=5)
        for cle, titre, largeur in [("libelle", "Libellé", 220), ("mode", "Méthode", 180), ("valeur", "Règle", 360)]:
            self.table_regles.heading(cle, text=titre)
            self.table_regles.column(cle, width=largeur)
        self.table_regles.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        self.table_regles.bind("<<TreeviewSelect>>", self._charger_regle_selectionnee)
        actions_regles = ttk.Frame(regles)
        actions_regles.grid(row=3, column=3, sticky="nsew", padx=(6, 0), pady=(8, 0))
        ttk.Button(actions_regles, text="Modifier", command=self._modifier_regle).pack(fill="x")
        ttk.Button(actions_regles, text="Supprimer", command=self._retirer_regle).pack(fill="x", pady=(4, 0))

        # Les recherches enregistrées réemploient ensemble le dossier et les règles.
        sauvegardes = ttk.LabelFrame(conteneur, text="Recherches enregistrées", padding=10)
        sauvegardes.grid(row=3, column=0, columnspan=3, sticky="nsew", pady=(0, 8))
        sauvegardes.columnconfigure(0, weight=1)
        sauvegardes.rowconfigure(0, weight=1)
        self.table_sauvegardes = ttk.Treeview(sauvegardes, columns=("nom", "dossier"), show="headings", height=5)
        self.table_sauvegardes.heading("nom", text="Nom")
        self.table_sauvegardes.heading("dossier", text="Dossier parent")
        self.table_sauvegardes.column("nom", width=200)
        self.table_sauvegardes.column("dossier", width=580)
        self.table_sauvegardes.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=(0, 8))
        ttk.Label(sauvegardes, text="Nom de la sauvegarde").grid(row=0, column=1, columnspan=2, sticky="w")
        ttk.Entry(sauvegardes, textvariable=self.nom_sauvegarde).grid(row=1, column=1, sticky="ew", pady=(2, 0))
        ttk.Button(sauvegardes, text="Enregistrer", command=self._enregistrer_configuration).grid(row=1, column=2, padx=(6, 0), pady=(2, 0))
        ttk.Button(sauvegardes, text="Charger", command=self._charger_configuration).grid(row=2, column=1, pady=(6, 0), sticky="ew")
        ttk.Button(sauvegardes, text="Supprimer", command=self._supprimer_configuration).grid(row=2, column=2, pady=(6, 0), padx=(6, 0))

        bas = ttk.Frame(conteneur)
        bas.grid(row=4, column=0, columnspan=3, sticky="ew")
        bas.columnconfigure(0, weight=1)
        self.progression = ttk.Progressbar(bas, mode="determinate")
        self.progression.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(bas, text="Lancer la recherche et créer le rapport", command=self._lancer).grid(row=0, column=1)
        ttk.Label(conteneur, textvariable=self.statut).grid(row=5, column=0, columnspan=3, sticky="w", pady=(8, 0))

    def _choisir_dossier(self) -> None:
        """Ouvre l'explorateur Windows pour sélectionner le dossier parent."""
        chemin = filedialog.askdirectory(title="Choisir le dossier parent à analyser")
        if chemin:
            self.chemin_dossier.set(chemin)

    def _choisir_rapport(self) -> None:
        """Ouvre l'explorateur Windows pour choisir le dossier et le nom du XLSX."""
        chemin = filedialog.asksaveasfilename(
            title="Enregistrer le rapport Excel", defaultextension=".xlsx",
            filetypes=[("Rapport Excel", "*.xlsx")], initialfile="rapport_presence.xlsx"
        )
        if chemin:
            self.chemin_rapport.set(chemin)

    def _ajouter_regle(self) -> None:
        """Valide les champs et ajoute une règle à la liste à vérifier."""
        if not self.libelle.get().strip() or not self.valeur.get().strip():
            messagebox.showwarning("Information manquante", "Renseignez le libellé et la règle du fichier.")
            return
        regle = {
            "libelle": self.libelle.get().strip(), "mode": MODES[self.mode.get()],
            "valeur": self.valeur.get().strip(), "sensible_a_la_casse": self.sensible_casse.get(),
            "regles_positions": getattr(self, "regles_positions_en_cours", []),
        }
        self.regles.append(regle)
        self.libelle.set("")
        self.valeur.set("")
        self.regles_positions_en_cours = []
        self._rafraichir_regles()

    def _retirer_regle(self) -> None:
        """Retire la règle actuellement sélectionnée dans le tableau."""
        selection = self.table_regles.selection()
        if selection:
            del self.regles[int(selection[0])]
            self._rafraichir_regles()

    def _modifier_regle(self) -> None:
        """Remplace la règle sélectionnée par les valeurs actuellement saisies."""
        selection = self.table_regles.selection()
        if not selection:
            messagebox.showinfo("Sélection requise", "Sélectionnez une ligne à modifier.")
            return
        if not self.libelle.get().strip() or not self.valeur.get().strip():
            messagebox.showwarning("Information manquante", "Renseignez le libellé et la règle du fichier.")
            return
        index = int(selection[0])
        positions = getattr(self, "regles_positions_en_cours", self.regles[index].get("regles_positions", []))
        self.regles[index] = {
            "libelle": self.libelle.get().strip(), "mode": MODES[self.mode.get()],
            "valeur": self.valeur.get().strip(), "sensible_a_la_casse": self.sensible_casse.get(),
            "regles_positions": positions,
        }
        self.regles_positions_en_cours = []
        self._rafraichir_regles()

    def _charger_regle_selectionnee(self, _evenement: object) -> None:
        """Place les données d'une règle dans le formulaire pour pouvoir les modifier."""
        selection = self.table_regles.selection()
        if not selection:
            return
        regle = self.regles[int(selection[0])]
        self.libelle.set(regle["libelle"])
        self.mode.set(next(nom for nom, cle in MODES.items() if cle == regle["mode"]))
        self.valeur.set(regle["valeur"])
        self.sensible_casse.set(regle.get("sensible_a_la_casse", False))
        self.regles_positions_en_cours = deepcopy(regle.get("regles_positions", []))

    def _rafraichir_regles(self) -> None:
        """Redessine le tableau après un ajout, une suppression ou un chargement."""
        self.table_regles.delete(*self.table_regles.get_children())
        for index, regle in enumerate(self.regles):
            mode_lisible = next(nom for nom, cle in MODES.items() if cle == regle["mode"])
            self.table_regles.insert("", "end", iid=str(index), values=(regle["libelle"], mode_lisible, regle["valeur"]))

    def _ouvrir_positions(self) -> None:
        """Permet de décrire les positions variables d'un exemple de nom de fichier."""
        if self.mode.get() != "Modèle à partir d'un exemple" or not self.valeur.get().strip():
            messagebox.showinfo("Modèle requis", "Choisissez le mode modèle et saisissez d'abord un exemple.")
            return
        PositionsDialog(self.racine, self, self.valeur.get().strip())

    def _enregistrer_configuration(self) -> None:
        """Ajoute ou remplace une recherche complète dans data/recherches.json."""
        nom = self.nom_sauvegarde.get().strip()
        if not nom:
            messagebox.showwarning("Nom de sauvegarde requis", "Donnez un nom à cette sauvegarde avant de l'enregistrer.")
            return
        if not self.chemin_dossier.get().strip() or not self.regles:
            messagebox.showwarning("Information manquante", "Le dossier parent et au moins une règle sont nécessaires.")
            return
        configuration = {"nom": nom, "dossier_parent": self.chemin_dossier.get().strip(), "regles": self.regles}
        self.recherches = [item for item in self.recherches if item["nom"] != nom] + [configuration]
        enregistrer_recherches(Path("data/recherches.json"), self.recherches)
        self._rafraichir_sauvegardes()

    def _rafraichir_sauvegardes(self) -> None:
        """Met à jour la liste des configurations mémorisées."""
        self.table_sauvegardes.delete(*self.table_sauvegardes.get_children())
        for index, item in enumerate(self.recherches):
            self.table_sauvegardes.insert("", "end", iid=str(index), values=(item["nom"], item["dossier_parent"]))

    def _charger_configuration(self) -> None:
        """Replace dans le formulaire le dossier et les règles d'une sauvegarde."""
        selection = self.table_sauvegardes.selection()
        if not selection:
            return
        item = self.recherches[int(selection[0])]
        self.nom_sauvegarde.set(item["nom"])
        self.chemin_dossier.set(item["dossier_parent"])
        self.regles = item["regles"]
        self._rafraichir_regles()

    def _supprimer_configuration(self) -> None:
        """Supprime définitivement une configuration sélectionnée après confirmation."""
        selection = self.table_sauvegardes.selection()
        if selection and messagebox.askyesno("Confirmation", "Supprimer cette recherche enregistrée ?"):
            del self.recherches[int(selection[0])]
            enregistrer_recherches(Path("data/recherches.json"), self.recherches)
            self._rafraichir_sauvegardes()

    def _lancer(self) -> None:
        """Démarre l'analyse dans un thread afin que la barre de progression reste active."""
        if not self.chemin_rapport.get().strip():
            messagebox.showwarning("Rapport requis", "Choisissez l'emplacement d'enregistrement du rapport.")
            return
        self.progression.configure(value=0, maximum=1)
        self.statut.set("Préparation de la recherche…")
        # Les valeurs Tkinter sont lues ici, dans le thread graphique : Tkinter
        # n'est pas conçu pour que le thread de fond lise directement ses variables.
        dossier_parent = self.chemin_dossier.get().strip()
        chemin_rapport = self.chemin_rapport.get().strip()
        regles = deepcopy(self.regles)
        threading.Thread(
            target=self._travail_recherche, args=(dossier_parent, regles, chemin_rapport), daemon=True
        ).start()
        self.racine.after(100, self._lire_messages)

    def _travail_recherche(
        self, dossier_parent: str, regles: list[dict[str, Any]], chemin_rapport: str
    ) -> None:
        """Exécute le moteur puis l'export Excel hors du thread graphique."""
        def signaler(courant: int, total: int, texte: str) -> None:
            self.file_messages.put(("progression", (courant, total, texte)))
        try:
            resultat = verifier_dossiers(dossier_parent, regles, signaler)
            self.file_messages.put(("statut", "Création du rapport Excel…"))
            rapport = generer_rapport_excel(resultat, chemin_rapport)
            self.file_messages.put(("termine", (resultat, rapport)))
        except Exception as erreur:
            self.file_messages.put(("erreur", str(erreur)))

    def _lire_messages(self) -> None:
        """Applique, dans le thread Tkinter, les messages émis par le travail de fond."""
        actif = True
        try:
            while True:
                type_message, contenu = self.file_messages.get_nowait()
                if type_message == "progression":
                    courant, total, texte = contenu
                    self.progression.configure(maximum=max(total, 1), value=courant)
                    self.statut.set(texte)
                elif type_message == "statut":
                    self.statut.set(contenu)
                elif type_message == "termine":
                    resultat, rapport = contenu
                    self.statut.set("Rapport créé avec succès.")
                    messagebox.showinfo("Terminé", f"Rapport enregistré :\n{rapport}\n\nFichiers manquants : {resultat['nombre_fichiers_manquants']}")
                    actif = False
                elif type_message == "erreur":
                    self.statut.set("La recherche a échoué.")
                    messagebox.showerror("Erreur", contenu)
                    actif = False
        except queue.Empty:
            pass
        if actif:
            self.racine.after(100, self._lire_messages)


class PositionsDialog:
    """Fenêtre qui associe les portions importantes d'un exemple à leur type."""

    def __init__(self, parent: Tk, application: FenetrePrincipale, exemple: str) -> None:
        """Affiche le tableau de l'exemple et les saisies pour les positions."""
        self.application, self.exemple = application, exemple
        self.fenetre = Toplevel(parent)
        self.fenetre.title("Définition de modèle")
        self.position_unique, self.debut_plage, self.fin_plage = StringVar(), StringVar(), StringVar()
        self.type_unique, self.type_plage = StringVar(value="chiffre"), StringVar(value="chiffre")

        ttk.Label(self.fenetre, text="chaque colonne relie une position au caractère correspondant.").pack(padx=12, pady=(12, 2), anchor="w")
        # Les numéros sont déjà visibles dans les en-têtes ; la seule ligne de
        # données affiche donc directement le caractère de chaque position.
        colonnes = [str(index) for index in range(1, len(exemple) + 1)]
        cadre_table = ttk.Frame(self.fenetre)
        cadre_table.pack(fill="x", padx=12)
        self.table_exemple = ttk.Treeview(cadre_table, columns=colonnes, show="tree headings", height=2)
        self.table_exemple.heading("#0", text="")
        self.table_exemple.column("#0", width=100, stretch=False)
        for colonne in colonnes:
            self.table_exemple.heading(colonne, text="colonne")
            self.table_exemple.column(colonne, width=35, anchor="center", stretch=False)
        self.table_exemple.insert("", "end", text="Caractère", values=list(exemple))
        barre = ttk.Scrollbar(cadre_table, orient="horizontal", command=self.table_exemple.xview)
        self.table_exemple.configure(xscrollcommand=barre.set)
        self.table_exemple.pack(fill="x")
        barre.pack(fill="x")

        types_affiches = ["chiffre", "lettre", "caractère spécial", "exact"]
        saisie = ttk.LabelFrame(self.fenetre, text="Ajouter ou modifier une partie du modèle", padding=10)
        saisie.pack(fill="x", padx=12, pady=10)
        # Première ligne : un seul caractère à une position donnée.
        ttk.Label(saisie, text="Caractère à un seul emplacement").grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(saisie, text="Position").grid(row=1, column=0, sticky="w")
        ttk.Label(saisie, text="Type").grid(row=1, column=1, sticky="w")
        ttk.Entry(saisie, textvariable=self.position_unique, width=10).grid(row=2, column=0, padx=(0, 6))
        ttk.Combobox(saisie, textvariable=self.type_unique, values=types_affiches, state="readonly", width=20).grid(row=2, column=1, padx=(0, 6))
        ttk.Button(saisie, text="Ajouter", command=self._ajouter_unique).grid(row=2, column=2, padx=(0, 18))
        # Seconde ligne : une plage, pratique pour les nombres de date ou un mot exact.
        ttk.Label(saisie, text="Plage de positions").grid(row=3, column=0, columnspan=4, sticky="w", pady=(10, 0))
        ttk.Label(saisie, text="Début").grid(row=4, column=0, sticky="w")
        ttk.Label(saisie, text="Fin").grid(row=4, column=1, sticky="w")
        ttk.Label(saisie, text="Type").grid(row=4, column=2, sticky="w")
        ttk.Entry(saisie, textvariable=self.debut_plage, width=10).grid(row=5, column=0, padx=(0, 6))
        ttk.Entry(saisie, textvariable=self.fin_plage, width=10).grid(row=5, column=1, padx=(0, 6))
        ttk.Combobox(saisie, textvariable=self.type_plage, values=types_affiches, state="readonly", width=20).grid(row=5, column=2, padx=(0, 6))
        ttk.Button(saisie, text="Ajouter", command=self._ajouter_plage).grid(row=5, column=3)

        self.liste = ttk.Treeview(self.fenetre, columns=("debut", "fin", "type"), show="headings", height=5)
        for cle, titre in [("debut", "Début"), ("fin", "Fin"), ("type", "Ce qui est recherché")]:
            self.liste.heading(cle, text=titre)
        self.liste.pack(fill="x", padx=12, pady=4)
        self.liste.bind("<<TreeviewSelect>>", self._charger_selection)
        actions = ttk.Frame(self.fenetre)
        actions.pack(fill="x", padx=12)
        # ttk.Button(actions, text="Modifier la sélection", command=self._modifier).pack(side="left")
        ttk.Button(actions, text="Supprimer la sélection", command=self._supprimer).pack(side="left", padx=(6, 0))
        ttk.Button(self.fenetre, text="Valider les positions", command=self._valider).pack(pady=(4, 12))
        self.regles: list[dict[str, Any]] = deepcopy(application.regles_positions_en_cours)
        self._rafraichir_liste()

    def _creer_regle(self, debut_texte: str, fin_texte: str, type_affiche: str) -> dict[str, Any] | None:
        """Valide les bornes et transforme le type lisible en valeur interne."""
        try:
            debut, fin = int(debut_texte), int(fin_texte)
            if debut < 1 or fin < debut or fin > len(self.exemple):
                raise ValueError
        except ValueError:
            messagebox.showwarning("Positions invalides", f"Indiquez des positions de 1 à {len(self.exemple)}.", parent=self.fenetre)
            return None
        types = {"chiffre": "chiffre", "lettre": "lettre", "caractère spécial": "caractere_special", "exact": "exact"}
        return {"debut": debut, "fin": fin, "type": types[type_affiche]}

    def _ajouter_unique(self) -> None:
        """Ajoute une règle portant sur un caractère unique."""
        regle = self._creer_regle(self.position_unique.get(), self.position_unique.get(), self.type_unique.get())
        if regle:
            self.regles.append(regle)
            self._rafraichir_liste()

    def _ajouter_plage(self) -> None:
        """Ajoute une règle portant sur une plage de caractères de l'exemple."""
        regle = self._creer_regle(self.debut_plage.get(), self.fin_plage.get(), self.type_plage.get())
        if regle:
            self.regles.append(regle)
            self._rafraichir_liste()

    def _rafraichir_liste(self) -> None:
        """Redessine le tableau des positions définies après chaque changement."""
        self.liste.delete(*self.liste.get_children())
        noms = {"chiffre": "chiffre", "lettre": "lettre", "caractere_special": "caractère spécial", "exact": "exact"}
        for index, regle in enumerate(self.regles):
            self.liste.insert("", "end", iid=str(index), values=(regle["debut"], regle["fin"], noms[regle["type"]]))

    def _charger_selection(self, _evenement: object) -> None:
        """Recopie une ligne sélectionnée dans la zone de saisie adéquate."""
        selection = self.liste.selection()
        if not selection:
            return
        regle = self.regles[int(selection[0])]
        noms = {"chiffre": "chiffre", "lettre": "lettre", "caractere_special": "caractère spécial", "exact": "exact"}
        if regle["debut"] == regle["fin"]:
            self.position_unique.set(str(regle["debut"]))
            self.type_unique.set(noms[regle["type"]])
        else:
            self.debut_plage.set(str(regle["debut"]))
            self.fin_plage.set(str(regle["fin"]))
            self.type_plage.set(noms[regle["type"]])

    def _modifier(self) -> None:
        """Remplace la règle sélectionnée par la saisie de ligne unique ou plage."""
        selection = self.liste.selection()
        if not selection:
            messagebox.showinfo("Sélection requise", "Sélectionnez une ligne à modifier.", parent=self.fenetre)
            return
        ancienne = self.regles[int(selection[0])]
        if ancienne["debut"] == ancienne["fin"]:
            nouvelle = self._creer_regle(self.position_unique.get(), self.position_unique.get(), self.type_unique.get())
        else:
            nouvelle = self._creer_regle(self.debut_plage.get(), self.fin_plage.get(), self.type_plage.get())
        if nouvelle:
            self.regles[int(selection[0])] = nouvelle
            self._rafraichir_liste()

    def _supprimer(self) -> None:
        """Retire une définition de position sélectionnée dans le tableau."""
        selection = self.liste.selection()
        if selection:
            del self.regles[int(selection[0])]
            self._rafraichir_liste()

    def _valider(self) -> None:
        """Transmet les positions au formulaire, où elles seront attachées à la règle."""
        self.application.regles_positions_en_cours = self.regles
        self.fenetre.destroy()
