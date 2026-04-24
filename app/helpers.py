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
    """Retourne un timestamp au format : [YYYY-MM-DD HH:MM:SS.mmm]"""
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")  # Supprime les 3 derniers chiffres des microsecondes

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
