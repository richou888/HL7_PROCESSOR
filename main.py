import tkinter as tk
from app.auth import LoginWindow
from app.gui import HL7ProcessorApp

def main():
    root = tk.Tk()
    root.withdraw()  # Cache la fenêtre principale temporairement

    # Ouvre la fenêtre de login
    login_window = LoginWindow(root)
    root.wait_window(login_window)  # Attend la fermeture de la fenêtre de login

    # Si le login réussit, lance l'application principale
    if login_window.authenticated:
        root.deiconify()  # Affiche à nouveau la fenêtre principale
        root.title("Outil de Flagging de Fichiers HL7")
        app = HL7ProcessorApp(root)  # Utilise la même instance root
        root.mainloop()
    else:
        root.destroy()  # Ferme la fenêtre si le login échoue

if __name__ == "__main__":
    main()