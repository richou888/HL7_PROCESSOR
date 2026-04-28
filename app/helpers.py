import hashlib
import tkinter as tk
from datetime import datetime

def hash_password(password):
    """Hache un mot de passe en SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def log_message(text_widget, message):
    """Ajoute un message à un widget Text (logs)."""
    text_widget.insert(tk.END, message + "\n")
    text_widget.see(tk.END)

def get_timestamp():
    """Retourne un timestamp au format : [YYYY-MM-DD HH:MM:SS]"""
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

def extract_hl7_id(file_path):
    """Extrait l'identifiant depuis une ligne PID dans un fichier HL7."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("PID"):
                    parts = line.split('|')
                    if len(parts) >= 3:
                        pid_field = parts[3]
                        if "^^^I_HCL" in pid_field:
                            before_i_hcl = pid_field.split("^^^I_HCL")[0]
                            if '~' in before_i_hcl:
                                return before_i_hcl.split('~')[-1]
                            else:
                                return before_i_hcl
        return None
    except Exception as e:
        print(f"Erreur lors de la lecture de {file_path}: {e}")
        return None

def extract_hl7_date(file_path):
    """
    Extrait les dates depuis le DERNIER segment SPM d'un fichier HL7.
    Les champs ciblés sont le 17ème et 18ème champs (index 17 et 18 après split '|').
    17 = Date de prélèvement de l'échantillon
    18 = Date de réception de l'échantillon
    Format attendu : YYYYMMDDHHMMSS -> retourne un objet datetime.
    Exemple de ligne SPM :
    SPM|1|...|20241231235800|20250101000318||Y...
    On prend le champ à l'index 17 (le 2ème timestamp, ex: 20250101000318).
    """
    try:
        last_spm_dates = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("SPM"):
                    parts = line.split('|')
                    if len(parts) > 18:
                        date_str_prelv = parts[17].strip()
                        date_str_recep = parts[18].strip()
                        if len(date_str_prelv) >= 14 and len(date_str_recep) >= 14:
                            try:
                                last_spm_dates = [datetime.strptime(date_str_prelv[:14], "%Y%m%d%H%M%S"),datetime.strptime(date_str_recep[:14], "%Y%m%d%H%M%S")]
                            except ValueError:
                                pass
        return last_spm_dates
    except Exception as e:
        print(f"Erreur lors de la lecture de la date dans {file_path}: {e}")
        return None
