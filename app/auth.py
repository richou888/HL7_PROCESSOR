import tkinter as tk
from tkinter import messagebox
from app.helpers import hash_password
import os

def load_env_file():
    """Charge les variables d'environnement depuis un fichier .env manuellement."""
    env_vars = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except FileNotFoundError:
        print("Avertissement : Fichier .env non trouvé. Utilisez les valeurs par défaut.")
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier .env : {e}")
    return env_vars

# Charge les variables d'environnement
env_vars = load_env_file()

class LoginWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Authentification")
        self.geometry("300x150")
        self.authenticated = False

        # Récupère les identifiants depuis le fichier .env (ou valeurs par défaut)
        self.valid_username = env_vars.get("APP_USERNAME", "admin")  # Valeur par défaut : "admin"
        self.valid_password_hash = env_vars.get("APP_PASSWORD_HASH", hash_password("password"))  # MDP par défaut : "password"

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Nom d'utilisateur:").pack(pady=5)
        self.username_entry = tk.Entry(self)
        self.username_entry.pack(pady=5)

        tk.Label(self, text="Mot de passe:").pack(pady=5)
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack(pady=5)

        tk.Button(self, text="Se connecter", command=self.check_credentials).pack(pady=10)

    def check_credentials(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if username == self.valid_username and hash_password(password) == self.valid_password_hash:
            self.authenticated = True
            self.destroy()
        else:
            messagebox.showerror("Erreur", f"Identifiants incorrects.\n\nUsername attendu: {self.valid_username}\nHash attendu: {self.valid_password_hash}")