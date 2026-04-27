import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from app.processor import HL7Processor
from app.helpers import log_message, get_timestamp
import threading

class HL7ProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Outil de Flagging de Fichiers HL7")
        self.root.geometry("950x850")
        self.processor = HL7Processor()

        # Variables chemins
        self.hl7_directory = tk.StringVar()
        self.identifiers_file = tk.StringVar()

        # Variables filtres
        self.use_ipp = tk.BooleanVar(value=True)
        self.use_date = tk.BooleanVar(value=False)

        self.create_widgets()

    def create_widgets(self):
        # --- Sélection des fichiers ---
        input_frame = ttk.LabelFrame(self.root, text="Sélection des fichiers", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(input_frame, text="Dossier HL7 :").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(input_frame, textvariable=self.hl7_directory, width=60).grid(row=0, column=1, padx=5)
        ttk.Button(input_frame, text="Parcourir...", command=self.choose_hl7_directory).grid(row=0, column=2)

        ttk.Label(input_frame, text="Fichier d'identifiants (CSV) :").grid(row=1, column=0, sticky=tk.W)
        self.ipp_entry = ttk.Entry(input_frame, textvariable=self.identifiers_file, width=60)
        self.ipp_entry.grid(row=1, column=1, padx=5)
        self.ipp_browse_btn = ttk.Button(input_frame, text="Parcourir...", command=self.choose_identifiers_file)
        self.ipp_browse_btn.grid(row=1, column=2)

        # --- Filtres actifs ---
        filter_frame = ttk.LabelFrame(self.root, text="Filtres actifs", padding=10)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        # Checkbox IPP
        self.ipp_check = ttk.Checkbutton(
            filter_frame,
            text="Exclusion par identifiant (IPP)  →  déplace dans /exclusionIPP",
            variable=self.use_ipp,
            command=self.toggle_ipp
        )
        self.ipp_check.grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=2)

        # Checkbox Date
        self.date_check = ttk.Checkbutton(
            filter_frame,
            text="Filtre par plage de dates (dernier SPM)  →  déplace dans /badDate",
            variable=self.use_date,
            command=self.toggle_date
        )
        self.date_check.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=2)

        # Sélecteurs de dates (affichés sous la checkbox date)
        self.date_sub_frame = ttk.Frame(filter_frame)
        self.date_sub_frame.grid(row=2, column=0, columnspan=4, sticky=tk.W, padx=20, pady=2)

        ttk.Label(self.date_sub_frame, text="Date début :").grid(row=0, column=0, sticky=tk.W)
        self.date_start_entry = ttk.Entry(self.date_sub_frame, width=20)
        self.date_start_entry.insert(0, "JJ/MM/AAAA HH:MM:SS")
        self.date_start_entry.grid(row=0, column=1, padx=5)
        self.date_start_entry.bind("<FocusIn>", lambda e: self._clear_placeholder(self.date_start_entry, "JJ/MM/AAAA HH:MM:SS"))

        ttk.Label(self.date_sub_frame, text="Date fin :").grid(row=0, column=2, padx=(20, 0), sticky=tk.W)
        self.date_end_entry = ttk.Entry(self.date_sub_frame, width=20)
        self.date_end_entry.insert(0, "JJ/MM/AAAA HH:MM:SS")
        self.date_end_entry.grid(row=0, column=3, padx=5)
        self.date_end_entry.bind("<FocusIn>", lambda e: self._clear_placeholder(self.date_end_entry, "JJ/MM/AAAA HH:MM:SS"))

        ttk.Label(self.date_sub_frame, text="(format : 01/01/2025 00:00:00)", foreground="grey").grid(
            row=1, column=0, columnspan=4, sticky=tk.W)

        # Désactivé par défaut
        self._set_date_widgets_state(tk.DISABLED)

        # --- Boutons d'action ---
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=8)

        self.start_button = ttk.Button(btn_frame, text="Démarrer le traitement", command=self.start_processing)
        self.start_button.grid(row=0, column=0, padx=10)
        self.cancel_button = ttk.Button(btn_frame, text="Annuler", command=self.cancel_processing, state=tk.DISABLED)
        self.cancel_button.grid(row=0, column=1, padx=10)
        ttk.Button(btn_frame, text="Aide", command=self.show_help).grid(row=0, column=2, padx=10)

        # --- Barre de progression ---
        self.progress = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=900, mode='determinate')
        self.progress.pack(pady=5, padx=10)

        # --- Résultats : deux onglets ---
        result_notebook = ttk.Notebook(self.root)
        result_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Onglet exclusionIPP
        ipp_frame = ttk.Frame(result_notebook)
        result_notebook.add(ipp_frame, text="Exclus par IPP")
        self.tree_ipp = ttk.Treeview(ipp_frame, columns=("Chemin",), show="headings")
        self.tree_ipp.heading("Chemin", text="Chemin du fichier déplacé → /exclusionIPP")
        self.tree_ipp.column("Chemin", width=880)
        self.tree_ipp.pack(fill=tk.BOTH, expand=True)

        # Onglet badDate
        date_frame = ttk.Frame(result_notebook)
        result_notebook.add(date_frame, text="Exclus par date")
        self.tree_date = ttk.Treeview(date_frame, columns=("Chemin",), show="headings")
        self.tree_date.heading("Chemin", text="Chemin du fichier déplacé → /badDate")
        self.tree_date.column("Chemin", width=880)
        self.tree_date.pack(fill=tk.BOTH, expand=True)

        # --- Export ---
        ttk.Button(self.root, text="Exporter le rapport", command=self.export_report).pack(pady=5)

        # --- Logs ---
        log_frame = ttk.LabelFrame(self.root, text="Logs", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
        self.log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # ------------------------------------------------------------------ #
    #  Helpers UI
    # ------------------------------------------------------------------ #

    def _clear_placeholder(self, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)

    def _set_date_widgets_state(self, state):
        self.date_start_entry.config(state=state)
        self.date_end_entry.config(state=state)

    def toggle_ipp(self):
        state = tk.NORMAL if self.use_ipp.get() else tk.DISABLED
        self.ipp_entry.config(state=state)
        self.ipp_browse_btn.config(state=state)

    def toggle_date(self):
        state = tk.NORMAL if self.use_date.get() else tk.DISABLED
        self._set_date_widgets_state(state)

    def _parse_date(self, entry_widget, label):
        """Parse une date saisie au format JJ/MM/AAAA HH:MM:SS."""
        raw = entry_widget.get().strip()
        placeholder = "JJ/MM/AAAA HH:MM:SS"
        if raw == placeholder or raw == "":
            return None
        try:
            return datetime.strptime(raw, "%d/%m/%Y %H:%M:%S")
        except ValueError:
            messagebox.showerror("Format de date invalide",
                                 f"{label} : format attendu JJ/MM/AAAA HH:MM:SS\nEx : 01/01/2025 00:00:00")
            return "ERROR"

    # ------------------------------------------------------------------ #
    #  Sélection fichiers
    # ------------------------------------------------------------------ #

    def choose_hl7_directory(self):
        directory = filedialog.askdirectory(title="Sélectionner le dossier HL7")
        if directory:
            self.hl7_directory.set(directory)
            log_message(self.log_text, f"{get_timestamp()} Dossier HL7 sélectionné : {directory}")

    def choose_identifiers_file(self):
        file_path = filedialog.askopenfilename(
            title="Sélectionner le fichier d'identifiants (CSV)",
            filetypes=[("CSV", "*.csv"), ("Tous", "*.*")]
        )
        if file_path:
            self.identifiers_file.set(file_path)
            log_message(self.log_text, f"{get_timestamp()} Fichier d'identifiants sélectionné : {file_path}")

    # ------------------------------------------------------------------ #
    #  Traitement principal
    # ------------------------------------------------------------------ #

    def start_processing(self):
        if not self.hl7_directory.get():
            messagebox.showwarning("Attention", "Veuillez sélectionner un dossier HL7.")
            return

        if not self.use_ipp.get() and not self.use_date.get():
            messagebox.showwarning("Attention", "Veuillez activer au moins un filtre (IPP ou Date).")
            return

        # Validation IPP
        identifiers = None
        if self.use_ipp.get():
            if not self.identifiers_file.get():
                messagebox.showwarning("Attention", "Veuillez sélectionner un fichier d'identifiants CSV.")
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
            date_start = self._parse_date(self.date_start_entry, "Date début")
            if date_start == "ERROR":
                return
            date_end = self._parse_date(self.date_end_entry, "Date fin")
            if date_end == "ERROR":
                return
            if date_start and date_end and date_start > date_end:
                messagebox.showerror("Erreur", "La date de début est postérieure à la date de fin.")
                return

        log_message(self.log_text, f"{get_timestamp()} Traitement démarré")
        if self.use_ipp.get():
            log_message(self.log_text, f"{get_timestamp()} Filtre IPP actif — {len(identifiers)} identifiants chargés")
        if self.use_date.get():
            log_message(self.log_text, f"{get_timestamp()} Filtre date actif — de {date_start} à {date_end}")

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
                    self.root.after(0, lambda p=path: self.tree_ipp.insert("", tk.END, values=(p,)))
                for path in results_date:
                    self.root.after(0, lambda p=path: self.tree_date.insert("", tk.END, values=(p,)))

                self.root.after(0, lambda: log_message(
                    self.log_text,
                    f"{get_timestamp()} Terminé — {len(results_ipp)} fichier(s) IPP déplacés, "
                    f"{len(results_date)} fichier(s) hors plage déplacés."
                ))
            except Exception as e:
                self.root.after(0, lambda: log_message(self.log_text, f"{get_timestamp()} Erreur : {e}"))
            finally:
                self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.cancel_button.config(state=tk.DISABLED))

        threading.Thread(target=processing_thread, daemon=True).start()

    def _update_progress_safely(self, current, total):
        self.progress["value"] = (current / total) * 100 if total > 0 else 0
        self.log_text.insert(tk.END, f"{get_timestamp()} Progression : {current}/{total} fichiers traités\n")
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
                log_message(self.log_text, f"{get_timestamp()} Rapport exporté vers {file_path}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'exporter le rapport : {e}")

    def show_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("Aide - Outil de Flagging HL7")
        help_window.geometry("800x600")
        help_text = tk.Text(help_window, wrap=tk.WORD)
        help_scroll = ttk.Scrollbar(help_window, orient=tk.VERTICAL, command=help_text.yview)
        help_text.configure(yscrollcommand=help_scroll.set)
        try:
            with open("docs/documentation.md", "r", encoding="utf-8") as f:
                help_text.insert(tk.END, f.read())
        except Exception as e:
            help_text.insert(tk.END, f"Impossible de charger la documentation : {e}")
        help_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        help_scroll.pack(side=tk.RIGHT, fill=tk.Y)
