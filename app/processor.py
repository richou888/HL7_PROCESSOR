import os
import csv
from app.helpers import extract_hl7_id  # <-- Import de la fonction corrigée

class HL7Processor:
    def __init__(self):
        self.results = []
        self.stop_requested = False

    def load_identifiers(self, file_path):
        """Charge les identifiants depuis un fichier CSV."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return {row[0].strip() for row in csv.reader(f) if row}

    def process_files(self, hl7_directory, identifiers, progress_callback=None):
        """Traite les fichiers HL7 et retourne ceux à supprimer."""
        self.results = []
        processed = 0
        total_files = 0

        # Compte le nombre total de fichiers .hl7
        for root, _, files in os.walk(hl7_directory):
            for file in files:
                if file.endswith('.hl7'):
                    total_files += 1

        # Traite les fichiers
        for root, _, files in os.walk(hl7_directory):
            if self.stop_requested:
                break
            for file in files:
                if file.endswith('.hl7'):
                    file_path = os.path.join(root, file)
                    file_id = extract_hl7_id(file_path)  # <-- Utilise la fonction de helpers.py
                    if file_id and file_id in identifiers:
                        self.results.append(file_path)
                    processed += 1
                    if progress_callback and processed % 1000 == 0:
                        progress_callback(processed, total_files)

        # Dernière mise à jour pour atteindre 100%
        if progress_callback:
            progress_callback(total_files, total_files)
        return self.results

    def save_report(self, output_path):
        """Enregistre le rapport des fichiers à supprimer."""
        with open(output_path, 'w', encoding='utf-8') as f:
            for path in self.results:
                f.write(f"{path}\n")