========================================
        FISHODORO - README
========================================

Un timer Pomodoro à thème aquatique avec gestion de tâches,
statistiques et boutique de skins. Tu gagnes des "poissons" 🐟
à chaque session complétée, et tu peux les dépenser dans la boutique.



=======================================
	DIFFERENTS COMPTES
=======================================
nom utilisateur: admin	
mot de passe : lol

nom utilisateur: jerome
mot de passe: NSI++

compte vide:
nom utilisateur: pierre 
mot de passe: jean 

========================================
 STRUCTURE DU PROJET
========================================

fishodoro/
├── main.py                      → Serveur Flask, routes et logique principale
├── classe_projet.py             → Classes : Utilisateur, Tache, Session, Apparence
├── fonctions.py                 → Fonctions métier (connexion, stats, graphes)
├── statistiques.py              → Génération des graphes matplotlib (SVG)
├── base_de_donnees_fonction.py  → Fonctions CRUD pour SQLite
├── bdd_projet_test.db           → Base de données SQLite (générée au premier lancement)
├── templates/
│   ├── index.html               → Page de connexion / inscription
│   ├── accueil.html             → Page principale (timer + tâches)
│   ├── stats.html               → Page statistiques avec graphes
│   ├── shop.html                → Boutique (skins et thèmes)
│   ├── equipment.html           → Page d'équipement
│   ├── fullscreen.html          → Timer plein écran
│   └── aide.html                → Page d'aide
└── static/
    ├── icon.png                 → Favicon
    └── Skin_de_base.png         → Sprite du poisson par défaut
        (+ autres sprites de skins)


========================================
 PRÉREQUIS
========================================

- Python 3.10 ou supérieur
- pip


========================================
 INSTALLATION
========================================

1. Cloner ou extraire le projet dans un dossier.

2. (Recommandé) Créer un environnement virtuel :

   python -m venv venv

   Sous Windows :
       venv\Scripts\activate

   Sous macOS/Linux :
       source venv/bin/activate

3. Installer les dépendances :

   pip install flask matplotlib

   sqlite3 est inclus dans la bibliothèque standard Python, aucune installation
   supplémentaire n'est nécessaire.


========================================
 BASE DE DONNÉES
========================================

La base de données SQLite (bdd_projet_test.db) doit exister avant le premier
lancement avec les tables suivantes déjà créées :

    - Utilisateurs        (id, nom_utilisateur, date_inscription, mot_de_passe,
                           nbr_tache, nbr_session)
    - Session             (id, duree, date_fait, statut, id_utilisateur)
    - Tache               (id, titre, date_fin, priorite, statut, date_creation,
                           id_utilisateur, description)
    - Poissons            (nbr_poisson, nbr_poisson_total, id_utilisateur,
                           poissons_depense)
    - Apparence_disponible (id, type, prix, nom, hauteur, largeur, lien, zoom)
    - Apparence_debloque  (id_apparence, id_utilisateur)
    - Apparence_equipe    (prix, id_apparence, id_utilisateur, type)

La base doit également contenir au moins le skin de base dans
Apparence_disponible (nom = 'skin_de_base', id = 1).

Si tu ne disposes pas encore de la base, demande le script de création SQL
à l'équipe ou génère-la manuellement avec DB Browser for SQLite.


========================================
 LANCEMENT
========================================

Depuis la racine du projet (avec le env activé) :

   python main.py

L'application sera disponible à l'adresse :

   http://127.0.0.1:5555

Ouvre ce lien dans ton navigateur, crée un compte et c'est parti !


========================================
 UTILISATION RAPIDE
========================================

1. Connexion / Inscription → page d'accueil (/)
2. Accueil → gère tes tâches et lance le timer Pomodoro
3. Timer → 30 min (session courte) ou 55 min (session longue)
   Chaque session complétée rapporte des 🐟 poissons.
4. Boutique (/shop) → achète des skins de poisson et des thèmes visuels
5. Équipement (/equipment) → équipe tes skins et thèmes débloqués
6. Stats (/stats) → visualise tes graphes de progression


========================================
 NOTES TECHNIQUES
========================================

- Le timer Pomodoro est géré côté serveur (objet Session Python partagé).
  Cela signifie qu'un seul timer est actif pour toute l'instance serveur.
  Pour un usage multi-utilisateurs simultané, il faudrait passer à un timer
  par utilisateur (stocker dans session Flask ou en BDD).

- Les graphes sont générés en SVG par matplotlib à chaque chargement de
  la page /stats. Pour les données vides, certains graphes peuvent lever
  des erreurs : assure-toi d'avoir fait au moins une session et une tâche.

- La clé secrète Flask (app.secret_key dans main.py) est actuellement en
  dur dans le code. Pour un déploiement en production, utilise une variable
  d'environnement :
      import os
      app.secret_key = os.environ.get("SECRET_KEY", "fallback_dev_key")


========================================
 DÉPENDANCES
========================================

flask      → Serveur web et gestion des routes / sessions
matplotlib → Génération des graphes SVG de la page statistiques
sqlite3    → Base de données (inclus dans Python)


========================================
