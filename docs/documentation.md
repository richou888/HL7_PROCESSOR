# Documentation - Outil de Flagging de Fichiers HL7

## 1. Description
Cet outil permet de parcourir des fichiers HL7, d'extraire un identifiant depuis une ligne `PID`, et de flagger les fichiers dont l'identifiant est présent dans une liste fournie (CSV). Les résultats sont affichés dans l'interface et exportables en CSV/TXT.

## 2. Prérequis
- Python 3.x
- Bibliothèques standard (tkinter, csv, os)
- Fichier `.env` pour les identifiants de login (voir section 4).

## 3. Fonctionnalités
- **Authentification** : Login/mot de passe avec hashage SHA-256.
- **Sélection des fichiers** : Dossier HL7 et fichier CSV d'identifiants.
- **Traitement** : Extraction des identifiants, comparaison avec la liste, flagging.
- **Export** : Génération d'un rapport des fichiers à supprimer.
- **Logs** : Affichage des actions et erreurs.
- **Aide** : Documentation intégrée.

## 4. Configuration
Créez un fichier `.env` à la racine du projet avec :
APP_USERNAME=votre_login
APP_PASSWORD_HASH=sha256_de_votre_mot_de_passe

Pour générer le hash, ouvrez un terminal Python et exécutez :

import hashlib
print(hashlib.sha256("votre_mot_de_passe".encode()).hexdigest())

Copiez le résultat dans .env pour APP_PASSWORD_HASH.

## 5. Utilisation
Lancez main.py.
Authentifiez-vous.
Sélectionnez le dossier HL7 et le fichier CSV d'identifiants.
Cliquez sur "Démarrer le traitement".
Exportez le rapport si nécessaire.

## 6. Structure du code
main.py : Point d'entrée.
app/auth.py : Gestion du login.
app/processor.py : Logique métier (traitement des fichiers).
app/gui.py : Interface graphique.
app/helpers.py : Fonctions utilitaires (hashage, logs, extraction d'ID).


## 7. Exemple de fichier HL7
PID|1||2001234567890^^^ASIP-SANTE-INS-NIR~10502672^^^I_HCL||DUPONT^Jean^^M||19800101|M|||...
L'identifiant extrait est 2001234567890.

## 8. Performances

Optimisation mémoire : Lecture séquentielle des fichiers (pas de chargement en mémoire).
Recherche rapide : Utilisation d'un set pour les identifiants.
Interface réactive : Mise à jour asynchrone de la barre de progression.

## 9. Limites
Pas de parallélisation (pour éviter de bloquer l'ordinateur).
Format des fichiers HL7 doit respecter la structure PID|...|ID^^^....

