import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from app.processor import HL7Processor
from app.helpers import log_message
from app.helpers import get_timestamp
import threading

class HL7ProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Outil de Flagging de Fichiers HL7")
        self.root.geometry("900x700")
        self.processor = HL7Processor()
        self.stop_requested = False  # Variable pour gérer l'annulation

        # Variables pour les chemins
        self.hl7_directory = tk.StringVar()
        self.identifiers_file = tk.StringVar()

        # Interface
        self.create_widgets()

    def create_widgets(self):
        # Frame pour les entrées
        input_frame = ttk.LabelFrame(self.root, text="Sélection des fichiers", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        # Dossier HL7
        ttk.Label(input_frame, text="Dossier HL7 :").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(input_frame, textvariable=self.hl7_directory, width=60).grid(row=0, column=1, padx=5)
        ttk.Button(input_frame, text="Parcourir...", command=self.choose_hl7_directory).grid(row=0, column=2)

        # Fichier d'identifiants
        ttk.Label(input_frame, text="Fichier d'identifiants (CSV) :").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(input_frame, textvariable=self.identifiers_file, width=60).grid(row=1, column=1, padx=5)
        ttk.Button(input_frame, text="Parcourir...", command=self.choose_identifiers_file).grid(row=1, column=2)

        # Boutons d'action
        self.start_button = ttk.Button(self.root, text="Démarrer le traitement", command=self.start_processing)
        self.start_button.pack(pady=10)
        self.cancel_button = ttk.Button(self.root, text="Annuler", command=self.cancel_processing, state=tk.DISABLED)
        self.cancel_button.pack(pady=5)

        # Bouton Aide
        ttk.Button(self.root, text="Aide", command=self.show_help).pack(pady=5)

        # Barre de progression
        self.progress = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=800, mode='determinate')
        self.progress.pack(pady=10)

        # Zone de résultats (Treeview)
        result_frame = ttk.LabelFrame(self.root, text="Fichiers à supprimer", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(result_frame, columns=("Chemin",), show="headings")
        self.tree.heading("Chemin", text="Chemin du fichier")
        self.tree.column("Chemin", width=800)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Bouton d'export
        ttk.Button(self.root, text="Exporter le rapport", command=self.export_report).pack(pady=10)

        # Zone de logs
        log_frame = ttk.LabelFrame(self.root, text="Logs", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def choose_hl7_directory(self):
        directory = filedialog.askdirectory(title="Sélectionner le dossier HL7")
        if directory:
            self.hl7_directory.set(directory)
            self.root.after(0, lambda: log_message(self.log_text, f"{get_timestamp()} Dossier HL7 sélectionné : {directory}"))

    def choose_identifiers_file(self):
        file_path = filedialog.askopenfilename(title="Sélectionner le fichier d'identifiants (CSV)")
        if file_path:
            self.identifiers_file.set(file_path)
            self.root.after(0, lambda: log_message(self.log_text, f"{get_timestamp()} Fichier d'identifiants sélectionné : {file_path}"))

    def start_processing(self):
        if not self.hl7_directory.get() or not self.identifiers_file.get():
            messagebox.showwarning("Attention", "Veuillez sélectionner un dossier HL7 et un fichier d'identifiants.")
            return
        self.root.after(0, lambda: log_message(self.log_text, f"{get_timestamp()} Traitement démarré par l'utilisateur"))

        # Désactive les boutons pendant le traitement
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.progress["value"] = 0
        self.tree.delete(*self.tree.get_children())
        self.processor.stop_requested = False

        # Charge les identifiants
        try:
            identifiers = self.processor.load_identifiers(self.identifiers_file.get())
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les identifiants : {e}")
            self.start_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)
            return

        if not identifiers:
            messagebox.showerror("Erreur", "Aucun identifiant trouvé dans le fichier.")
            self.start_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)
            return

        # Fonction pour mettre à jour la barre de progression (thread-safe)
        def update_progress(current, total):
            self.root.after(0, lambda: self._update_progress_safely(current, total))

        # Fonction exécutée dans le thread
        def processing_thread():
            try:
                self.processor.process_files(
                    self.hl7_directory.get(),
                    identifiers,
                    update_progress
                )
                # Mise à jour des résultats et des logs dans le thread principal
                for path in self.processor.results:
                    self.root.after(0, lambda p=path: self.tree.insert("", tk.END, values=(p,)))
                
                timestamp = get_timestamp()
                self.root.after(0, lambda: log_message(self.log_text, f"{get_timestamp()} Traitement terminé. {len(self.processor.results)} fichiers à supprimer."))
            except Exception as e:
                self.root.after(0, lambda: log_message(self.log_text, f"{get_timestamp()} Erreur pendant le traitement : {e}"))
            finally:
                # Réactive les boutons dans le thread principal
                self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.cancel_button.config(state=tk.DISABLED))

        # Lance le traitement dans un thread séparé
        thread = threading.Thread(target=processing_thread, daemon=True)
        thread.start()

    def _update_progress_safely(self, current, total):
        """Met à jour la barre de progression et les logs de manière thread-safe."""
        self.progress["value"] = (current / total) * 100 if total > 0 else 0
        self.log_text.insert(tk.END, f"{get_timestamp()} Progression : {current}/{total} fichiers traités\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def cancel_processing(self):
        """Annule le traitement en cours."""
        self.processor.stop_requested = True
        self.root.after(0, lambda: self.cancel_button.config(state=tk.DISABLED))
        self.root.after(0, lambda: log_message(self.log_text, f"{get_timestamp()} Traitement annulé par l'utilisateur."))

    def export_report(self):
        """Exporte le rapport des fichiers à supprimer."""
        if not self.processor.results:
            messagebox.showwarning("Attention", "Aucun résultat à exporter.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Enregistrer le rapport",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("TXT", "*.txt")]
        )
        if file_path:
            try:
                self.processor.save_report(file_path)
                self.root.after(0, lambda: log_message(self.log_text, f"{get_timestamp()} Rapport exporté vers {file_path}"))
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'exporter le rapport : {e}")

    def show_help(self):
        """Affiche la documentation dans une nouvelle fenêtre."""
        help_window = tk.Toplevel(self.root)
        help_window.title("Aide - Outil de Flagging HL7")
        help_window.geometry("800x600")

        help_text = tk.Text(help_window, wrap=tk.WORD)
        help_scroll = ttk.Scrollbar(help_window, orient=tk.VERTICAL, command=help_text.yview)
        help_text.configure(yscrollcommand=help_scroll.set)

        # Charge la documentation depuis le fichier
        try:
            with open("docs/documentation.md", "r", encoding="utf-8") as f:
                help_text.insert(tk.END, f.read())
        except Exception as e:
            help_text.insert(tk.END, f"Impossible de charger la documentation : {e}")

        help_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        help_scroll.pack(side=tk.RIGHT, fill=tk.Y)
