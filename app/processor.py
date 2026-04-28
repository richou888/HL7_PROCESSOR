import os
import csv
import shutil
from app.helpers import extract_hl7_id, extract_hl7_date

class HL7Processor:
    def __init__(self):
        self.results = []          # Fichiers matchés par exclusion IPP
        self.results_date = []     # Fichiers matchés par filtre de date
        self.stop_requested = False

    def load_identifiers(self, file_path):
        """Charge les identifiants depuis un fichier CSV."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return {row[0].strip() for row in csv.reader(f) if row}

    def process_files(self, hl7_directory, identifiers=None, date_start=None,
                      date_end=None, use_ipp=True, use_date=False,
                      progress_callback=None):
        """
        Traite les fichiers HL7 selon les filtres activés.
        - use_ipp   : active le filtre par identifiant (liste CSV)
        - use_date  : active le filtre par plage de dates (dernier SPM)
        - identifiers : set d'identifiants à exclure
        - date_start / date_end : objets datetime délimitant la plage
        Les fichiers hors plage ou dans la liste sont déplacés dans des
        sous-dossiers créés automatiquement.
        """
        self.results = []
        self.results_date = []
        self.stop_requested = False
        processed = 0
        total_files = 0

        # Création des dossiers de destination si nécessaire
        dir_ipp = os.path.join(hl7_directory, "exclusionIPP")
        dir_date = os.path.join(hl7_directory, "badDate")

        if use_ipp:
            os.makedirs(dir_ipp, exist_ok=True)
        if use_date:
            os.makedirs(dir_date, exist_ok=True)

        # Compte le nombre total de fichiers .hl7
        for root, _, files in os.walk(hl7_directory):
            # On exclut les sous-dossiers de destination pour ne pas les retraiter
            if root in (dir_ipp, dir_date):
                continue
            for file in files:
                if file.endswith('.hl7'):
                    total_files += 1

        # Traitement des fichiers
        for root, dirs, files in os.walk(hl7_directory):
            # Exclut les dossiers de destination du parcours
            dirs[:] = [d for d in dirs if os.path.join(root, d) not in (dir_ipp, dir_date)]

            if self.stop_requested:
                break

            for file in files:
                if not file.endswith('.hl7'):
                    continue

                file_path = os.path.join(root, file)
                moved = False

                # --- Filtre IPP ---
                if use_ipp and identifiers:
                    file_id = extract_hl7_id(file_path)
                    if file_id and file_id in identifiers:
                        dest = os.path.join(dir_ipp, file)
                        try:
                            shutil.move(file_path, dest)
                            self.results.append(f"Fichier : {file} - IPP Exclu : {file_id}")
                            moved = True
                        except Exception as e:
                            print(f"Erreur déplacement IPP {file_path}: {e}")

                # --- Filtre Date ---
                # On vérifie seulement si le fichier n'a pas déjà été déplacé
                if use_date and not moved:
                    file_date = extract_hl7_date(file_path)
                    if file_date is not None:
                        # Hors plage = avant date_start OU après date_end
                        out_of_range = False
                        if date_start and file_date[0] < date_start and file_date[1] < date_start:
                            out_of_range = True
                        if date_end and file_date[0] > date_end and file_date[1] > date_end:
                            out_of_range = True
                        if out_of_range:
                            dest = os.path.join(dir_date, file)
                            try:
                                shutil.move(file_path, dest)
                                self.results_date.append(f"Fichier : {file} - [ Dates Prélèvement : {file_date[0]} - Dates Reception : {file_date[1]}")
                            except Exception as e:
                                print(f"Erreur déplacement date {file_path}: {e}")

                processed += 1
                if progress_callback and processed % 100 == 0:
                    progress_callback(processed, total_files)

        # Dernière mise à jour pour atteindre 100%
        if progress_callback:
            progress_callback(total_files, total_files)

        return self.results, self.results_date

    def save_report(self, output_path):
        """Enregistre le rapport combiné des fichiers déplacés."""
        with open(output_path, 'w', encoding='utf-8') as f:
            if self.results:
                f.write("=== Fichiers exclus par IPP ===\n")
                for path in self.results:
                    f.write(f"{path}\n")
            if self.results_date:
                f.write("\n=== Fichiers exclus par date ===\n")
                for path in self.results_date:
                    f.write(f"{path}\n")
