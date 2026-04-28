import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import calendar
from app.processor import HL7Processor
from app.helpers import log_message, get_timestamp
import threading


# ======================================================================
#  Widget Calendrier natif (sans dépendance externe)
# ======================================================================

class CalendarPicker(ttk.Frame):
    """
    Sélecteur de date natif basé sur tkinter pur.
    Affiche un bouton avec la date sélectionnée.
    Au clic, ouvre une popup avec un calendrier mensuel navigable.
    Fermeture uniquement sur sélection d'un jour ou clic en dehors de la popup.
    """

    def __init__(self, parent, initial_date=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._date = initial_date or datetime.today().date()
        self._popup = None

        self._btn = ttk.Button(self, text=self._format(), command=self._open_popup, width=14)
        self._btn.pack()

    def _format(self):
        return self._date.strftime("%d/%m/%Y")

    def get_date(self):
        return self._date

    def _open_popup(self):
        # Si déjà ouverte, on la ferme (toggle)
        if self._popup is not None:
            try:
                if self._popup.winfo_exists():
                    self._close_popup()
                    return
            except Exception:
                pass

        self._popup = tk.Toplevel(self)
        self._popup.overrideredirect(True)
        self._popup.resizable(False, False)
        self._popup.grab_set()

        # Position sous le bouton
        x = self._btn.winfo_rootx()
        y = self._btn.winfo_rooty() + self._btn.winfo_height() + 2
        self._popup.geometry(f"+{x}+{y}")

        self._nav_year = self._date.year
        self._nav_month = self._date.month
        self._build_calendar()

        # Ferme si clic en dehors de la popup — via binding sur la root
        self._popup.bind("<Button-1>", self._on_popup_click)
        self._popup.after(100, self._bind_outside_click)

    def _bind_outside_click(self):
        """Lie le clic extérieur sur la fenêtre racine pour fermer la popup."""
        root = self._get_root()
        root.bind("<Button-1>", self._check_outside_click, add="+")

    def _unbind_outside_click(self):
        root = self._get_root()
        try:
            root.unbind("<Button-1>")
        except Exception:
            pass

    def _get_root(self):
        w = self
        while w.master:
            w = w.master
        return w

    def _on_popup_click(self, event):
        """Empêche la propagation du clic dans la popup vers le root."""
        return "break"

    def _check_outside_click(self, event):
        """Ferme la popup si le clic est en dehors."""
        if self._popup is None:
            return
        try:
            if not self._popup.winfo_exists():
                return
            px = self._popup.winfo_rootx()
            py = self._popup.winfo_rooty()
            pw = self._popup.winfo_width()
            ph = self._popup.winfo_height()
            ex, ey = event.x_root, event.y_root
            if not (px <= ex <= px + pw and py <= ey <= py + ph):
                self._close_popup()
        except Exception:
            pass

    def _close_popup(self):
        self._unbind_outside_click()
        if self._popup:
            try:
                self._popup.grab_release()
                self._popup.destroy()
            except Exception:
                pass
            self._popup = None

    def _build_calendar(self):
        """Construit ou reconstruit le contenu de la popup."""
        for w in self._popup.winfo_children():
            w.destroy()

        outer = ttk.Frame(self._popup, relief="solid", borderwidth=1)
        outer.pack()

        # -- Navigation --
        nav = ttk.Frame(outer)
        nav.pack(fill=tk.X, pady=4, padx=4)

        ttk.Button(nav, text="◀◀", width=3,
                   command=self._prev_year).pack(side=tk.LEFT)
        ttk.Button(nav, text="◀", width=3,
                   command=self._prev_month).pack(side=tk.LEFT, padx=2)

        month_name = f"{calendar.month_name[self._nav_month]} {self._nav_year}"
        ttk.Label(nav, text=month_name, width=16,
                  anchor="center", font=("", 10, "bold")).pack(side=tk.LEFT, expand=True)

        ttk.Button(nav, text="▶▶", width=3,
                   command=self._next_year).pack(side=tk.RIGHT)
        ttk.Button(nav, text="▶", width=3,
                   command=self._next_month).pack(side=tk.RIGHT, padx=4)

        # -- Jours de la semaine --
        days_frame = ttk.Frame(outer)
        days_frame.pack(padx=4)
        day_names = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        for col, name in enumerate(day_names):
            fg = "red" if col >= 5 else "black"
            ttk.Label(days_frame, text=name, width=4,
                      anchor="center", foreground=fg).grid(row=0, column=col)

        # -- Grille des jours --
        cal = calendar.monthcalendar(self._nav_year, self._nav_month)
        for row, week in enumerate(cal, start=1):
            for col, day in enumerate(week):
                if day == 0:
                    ttk.Label(days_frame, text="", width=4).grid(row=row, column=col)
                    continue

                is_selected = (
                    day == self._date.day and
                    self._nav_month == self._date.month and
                    self._nav_year == self._date.year
                )
                is_today = (
                    day == datetime.today().day and
                    self._nav_month == datetime.today().month and
                    self._nav_year == datetime.today().year
                )

                if is_selected:
                    bg, fg = "steelblue", "white"
                elif is_today:
                    bg, fg = "#e8f4fd", "steelblue"
                elif col >= 5:
                    bg, fg = "white", "#cc0000"
                else:
                    bg, fg = "white", "black"

                btn = tk.Button(
                    days_frame,
                    text=str(day),
                    width=3,
                    relief="flat",
                    bg=bg, fg=fg,
                    activebackground="lightblue",
                    cursor="hand2",
                    command=lambda d=day: self._select_day(d)
                )
                btn.grid(row=row, column=col, padx=1, pady=1)

        # -- Bouton Aujourd'hui --
        ttk.Button(outer, text="Aujourd'hui",
                   command=self._goto_today).pack(pady=4)

    def _select_day(self, day):
        from datetime import date
        self._date = date(self._nav_year, self._nav_month, day)
        self._btn.config(text=self._format())
        self._close_popup()
        self.event_generate("<<DateSelected>>")

    def _goto_today(self):
        today = datetime.today().date()
        self._nav_year = today.year
        self._nav_month = today.month
        self._date = today
        self._btn.config(text=self._format())
        self._build_calendar()
        self.event_generate("<<DateSelected>>")

    def _prev_month(self):
        if self._nav_month == 1:
            self._nav_month = 12
            self._nav_year -= 1
        else:
            self._nav_month -= 1
        self._build_calendar()

    def _next_month(self):
        if self._nav_month == 12:
            self._nav_month = 1
            self._nav_year += 1
        else:
            self._nav_month += 1
        self._build_calendar()

    def _prev_year(self):
        self._nav_year -= 1
        self._build_calendar()

    def _next_year(self):
        self._nav_year += 1
        self._build_calendar()

    def config(self, **kwargs):
        if "state" in kwargs:
            self._btn.config(state=kwargs["state"])


# ======================================================================
#  Application principale
# ======================================================================

class HL7ProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Outil de Flagging de Fichiers HL7")
        self.root.geometry("950x900")
        self.processor = HL7Processor()

        self.hl7_directory = tk.StringVar()
        self.identifiers_file = tk.StringVar()
        self.use_ipp = tk.BooleanVar(value=True)
        self.use_date = tk.BooleanVar(value=False)

        self.create_widgets()

    # ------------------------------------------------------------------ #
    #  Construction de l'interface
    # ------------------------------------------------------------------ #

    def create_widgets(self):

        # --- Sélection des fichiers ---
        input_frame = ttk.LabelFrame(self.root, text="Sélection des fichiers", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(input_frame, text="Dossier HL7 :").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(input_frame, textvariable=self.hl7_directory, width=65).grid(row=0, column=1, padx=5)
        ttk.Button(input_frame, text="Parcourir...",
                   command=self.choose_hl7_directory).grid(row=0, column=2)

        ttk.Label(input_frame, text="Fichier identifiants (CSV) :").grid(
            row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.ipp_entry = ttk.Entry(input_frame, textvariable=self.identifiers_file, width=65)
        self.ipp_entry.grid(row=1, column=1, padx=5, pady=(5, 0))
        self.ipp_browse_btn = ttk.Button(input_frame, text="Parcourir...",
                                         command=self.choose_identifiers_file)
        self.ipp_browse_btn.grid(row=1, column=2, pady=(5, 0))

        # --- Filtres actifs ---
        filter_frame = ttk.LabelFrame(self.root, text="Filtres actifs", padding=10)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        self.ipp_check = ttk.Checkbutton(
            filter_frame,
            text="Exclusion par identifiant (IPP)  →  déplace dans /exclusionIPP",
            variable=self.use_ipp,
            command=self.toggle_ipp
        )
        self.ipp_check.grid(row=0, column=0, columnspan=6, sticky=tk.W, pady=2)

        self.date_check = ttk.Checkbutton(
            filter_frame,
            text="Filtre par plage de dates (dernier segment SPM)  →  déplace dans /badDate",
            variable=self.use_date,
            command=self.toggle_date
        )
        self.date_check.grid(row=1, column=0, columnspan=6, sticky=tk.W, pady=2)

        # Sous-frame calendriers
        self.date_sub_frame = ttk.Frame(filter_frame)
        self.date_sub_frame.grid(row=2, column=0, columnspan=6, sticky=tk.W, padx=25, pady=6)

        # Date début
        ttk.Label(self.date_sub_frame, text="Date début :").grid(row=0, column=0, sticky=tk.W)
        self.cal_start = CalendarPicker(self.date_sub_frame)
        self.cal_start.grid(row=0, column=1, padx=(5, 2))
        self.cal_start.bind("<<DateSelected>>", lambda e: self._refresh_time_labels())
        self.lbl_start_time = ttk.Label(
            self.date_sub_frame, text="00:00:00",
            foreground="steelblue", font=("Courier", 10), width=10
        )
        self.lbl_start_time.grid(row=0, column=2, padx=(2, 30))

        # Date fin
        ttk.Label(self.date_sub_frame, text="Date fin :").grid(row=0, column=3, sticky=tk.W)
        self.cal_end = CalendarPicker(self.date_sub_frame)
        self.cal_end.grid(row=0, column=4, padx=(5, 2))
        self.cal_end.bind("<<DateSelected>>", lambda e: self._refresh_time_labels())
        self.lbl_end_time = ttk.Label(
            self.date_sub_frame, text="23:59:59",
            foreground="steelblue", font=("Courier", 10), width=10
        )
        self.lbl_end_time.grid(row=0, column=5, padx=(2, 5))

        ttk.Label(
            self.date_sub_frame,
            text="Les jours sélectionnés sont inclus — les fichiers hors plage seront déplacés dans /badDate.",
            foreground="grey"
        ).grid(row=1, column=0, columnspan=6, sticky=tk.W, pady=(4, 0))

        # Désactivé par défaut
        self._set_date_widgets_state(tk.DISABLED)

        # --- Boutons d'action ---
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=8)
        self.start_button = ttk.Button(btn_frame, text="Démarrer le traitement",
                                       command=self.start_processing)
        self.start_button.grid(row=0, column=0, padx=10)
        self.cancel_button = ttk.Button(btn_frame, text="Annuler",
                                        command=self.cancel_processing, state=tk.DISABLED)
        self.cancel_button.grid(row=0, column=1, padx=10)
        ttk.Button(btn_frame, text="Aide", command=self.show_help).grid(row=0, column=2, padx=10)

        # --- Barre de progression ---
        self.progress = ttk.Progressbar(self.root, orient=tk.HORIZONTAL,
                                        length=900, mode='determinate')
        self.progress.pack(pady=5, padx=10)

        # --- Résultats : deux onglets ---
        result_notebook = ttk.Notebook(self.root)
        result_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        ipp_tab = ttk.Frame(result_notebook)
        result_notebook.add(ipp_tab, text="Exclus par IPP")
        self.tree_ipp = ttk.Treeview(ipp_tab, columns=("Chemin",), show="headings")
        self.tree_ipp.heading("Chemin", text="Chemin du fichier déplacé → /exclusionIPP")
        self.tree_ipp.column("Chemin", width=880)
        self.tree_ipp.pack(fill=tk.BOTH, expand=True)

        date_tab = ttk.Frame(result_notebook)
        result_notebook.add(date_tab, text="Exclus par date")
        self.tree_date = ttk.Treeview(date_tab, columns=("Chemin",), show="headings")
        self.tree_date.heading("Chemin", text="Chemin du fichier déplacé → /badDate")
        self.tree_date.column("Chemin", width=880)
        self.tree_date.pack(fill=tk.BOTH, expand=True)

        # --- Export ---
        ttk.Button(self.root, text="Exporter le rapport",
                   command=self.export_report).pack(pady=5)

        # --- Logs ---
        log_frame = ttk.LabelFrame(self.root, text="Logs", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
        self.log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL,
                                        command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _refresh_time_labels(self):
        self.lbl_start_time.config(text="00:00:00")
        self.lbl_end_time.config(text="23:59:59")

    def _set_date_widgets_state(self, state):
        self.cal_start.config(state=state)
        self.cal_end.config(state=state)

    def toggle_ipp(self):
        state = tk.NORMAL if self.use_ipp.get() else tk.DISABLED
        self.ipp_entry.config(state=state)
        self.ipp_browse_btn.config(state=state)

    def toggle_date(self):
        state = tk.NORMAL if self.use_date.get() else tk.DISABLED
        self._set_date_widgets_state(state)

    def _get_date_start(self):
        d = self.cal_start.get_date()
        return datetime(d.year, d.month, d.day, 0, 0, 0)

    def _get_date_end(self):
        d = self.cal_end.get_date()
        return datetime(d.year, d.month, d.day, 23, 59, 59)

    # ------------------------------------------------------------------ #
    #  Sélection fichiers
    # ------------------------------------------------------------------ #

    def choose_hl7_directory(self):
        directory = filedialog.askdirectory(title="Sélectionner le dossier HL7")
        if directory:
            self.hl7_directory.set(directory)
            log_message(self.log_text,
                        f"{get_timestamp()} Dossier HL7 sélectionné : {directory}")

    def choose_identifiers_file(self):
        file_path = filedialog.askopenfilename(
            title="Sélectionner le fichier d'identifiants (CSV)",
            filetypes=[("CSV", "*.csv"), ("Tous", "*.*")]
        )
        if file_path:
            self.identifiers_file.set(file_path)
            log_message(self.log_text,
                        f"{get_timestamp()} Fichier d'identifiants sélectionné : {file_path}")

    # ------------------------------------------------------------------ #
    #  Traitement principal
    # ------------------------------------------------------------------ #

    def start_processing(self):
        if not self.hl7_directory.get():
            messagebox.showwarning("Attention", "Veuillez sélectionner un dossier HL7.")
            return

        if not self.use_ipp.get() and not self.use_date.get():
            messagebox.showwarning("Attention",
                                   "Veuillez activer au moins un filtre (IPP ou Date).")
            return

        # Validation IPP
        identifiers = None
        if self.use_ipp.get():
            if not self.identifiers_file.get():
                messagebox.showwarning("Attention",
                                       "Veuillez sélectionner un fichier CSV d'identifiants.")
                return
            try:
                identifiers = self.processor.load_identifiers(self.identifiers_file.get())
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de charger les identifiants : {e}")
                return
            if not identifiers:
                messagebox.showerror("Erreur", "Aucun identifiant trouvé dans le fichier CSV.")
                return

        # Validation dates
        date_start = None
        date_end = None
        if self.use_date.get():
            date_start = self._get_date_start()
            date_end = self._get_date_end()
            if date_start > date_end:
                messagebox.showerror("Erreur",
                                     "La date de début est postérieure à la date de fin.")
                return

        # Logs
        log_message(self.log_text, f"{get_timestamp()} Traitement démarré")
        if self.use_ipp.get():
            log_message(self.log_text,
                        f"{get_timestamp()} Filtre IPP — {len(identifiers)} identifiant(s) chargé(s)")
        if self.use_date.get():
            log_message(self.log_text,
                        f"{get_timestamp()} Filtre date — "
                        f"du {date_start.strftime('%d/%m/%Y %H:%M:%S')} "
                        f"au {date_end.strftime('%d/%m/%Y %H:%M:%S')}")

        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.progress["value"] = 0
        self.tree_ipp.delete(*self.tree_ipp.get_children())
        self.tree_date.delete(*self.tree_date.get_children())

        def update_progress(current, total):
            self.root.after(0, lambda: self._update_progress_safely(current, total))

        def processing_thread():
            try:
                results_ipp, results_date = self.processor.process_files(
                    hl7_directory=self.hl7_directory.get(),
                    identifiers=identifiers,
                    date_start=date_start,
                    date_end=date_end,
                    use_ipp=self.use_ipp.get(),
                    use_date=self.use_date.get(),
                    progress_callback=update_progress
                )
                for path in results_ipp:
                    self.root.after(0, lambda p=path: self.tree_ipp.insert(
                        "", tk.END, values=(p,)))
                for path in results_date:
                    self.root.after(0, lambda p=path: self.tree_date.insert(
                        "", tk.END, values=(p,)))

                self.root.after(0, lambda: log_message(
                    self.log_text,
                    f"{get_timestamp()} Terminé — "
                    f"{len(results_ipp)} fichier(s) exclus par IPP, "
                    f"{len(results_date)} fichier(s) hors plage de dates."
                ))
            except Exception as e:
                self.root.after(0, lambda: log_message(
                    self.log_text, f"{get_timestamp()} Erreur : {e}"))
            finally:
                self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.cancel_button.config(state=tk.DISABLED))

        threading.Thread(target=processing_thread, daemon=True).start()

    def _update_progress_safely(self, current, total):
        self.progress["value"] = (current / total) * 100 if total > 0 else 0
        self.log_text.insert(
            tk.END, f"{get_timestamp()} Progression : {current}/{total} fichiers traités\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def cancel_processing(self):
        self.processor.stop_requested = True
        self.cancel_button.config(state=tk.DISABLED)
        log_message(self.log_text, f"{get_timestamp()} Traitement annulé par l'utilisateur.")

    # ------------------------------------------------------------------ #
    #  Export & Aide
    # ------------------------------------------------------------------ #

    def export_report(self):
        if not self.processor.results and not self.processor.results_date:
            messagebox.showwarning("Attention", "Aucun résultat à exporter.")
            return
        file_path = filedialog.asksaveasfilename(
            title="Enregistrer le rapport",
            defaultextension=".txt",
            filetypes=[("TXT", "*.txt"), ("CSV", "*.csv")]
        )
        if file_path:
            try:
                self.processor.save_report(file_path)
                log_message(self.log_text,
                            f"{get_timestamp()} Rapport exporté vers {file_path}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'exporter le rapport : {e}")

    def show_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("Aide - Outil de Flagging HL7")
        help_window.geometry("800x600")
        help_text = tk.Text(help_window, wrap=tk.WORD)
        help_scroll = ttk.Scrollbar(help_window, orient=tk.VERTICAL,
                                    command=help_text.yview)
        help_text.configure(yscrollcommand=help_scroll.set)
        try:
            with open("docs/documentation.md", "r", encoding="utf-8") as f:
                help_text.insert(tk.END, f.read())
        except Exception as e:
            help_text.insert(tk.END, f"Impossible de charger la documentation : {e}")
        help_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        help_scroll.pack(side=tk.RIGHT, fill=tk.Y)
