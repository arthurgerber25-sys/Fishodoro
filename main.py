from flask import Flask, render_template, request, jsonify, url_for, redirect, session
from classe_projet import Session, Utilisateur, Tache, ListeTache, Apparence
import datetime
import threading
from base_de_donnees_fonction import *
from fonctions import *
from statistiques import *

app = Flask(__name__)
app.secret_key = "cle_secrete_super_random_123"  # ⚠️ À remplacer par une variable d'environnement en production


# ══════════════════════════════════════════════════════════════════
#  CATALOGUES (chargés une seule fois au démarrage du serveur)
# ══════════════════════════════════════════════════════════════════

# Skins de poissons disponibles en boutique, chargés depuis la BDD
CATALOGUE_SKINS = recup_apparence()

# Thèmes visuels disponibles (définis en dur dans le code)
# Chaque thème modifie : couleur des algues, gradient de fond, couleurs des poissons de fond
CATALOGUE_THEMES = [
    {"id": 101, "nom": "theme_ocean",   "label": "Océan Classique",   "prix": 0,
     "algue_color": "#0a8f3b,#34c759",
     "bg_gradient": "180deg,#001022,#002244,#003366,#004080",
     "fish_colors": ["#FFD700,#FFA500","#FF6347,#FF4500","#00BFFF,#1E90FF","#32CD32,#228B22","#FF69B4,#FF1493","#1E90FF,#00CED1"]},

    {"id": 102, "nom": "theme_corail",  "label": "Récif Corallien",   "prix": 40,
     "algue_color": "#c0392b,#e74c3c",
     "bg_gradient": "180deg,#000a1a,#001033,#08003d,#100050",
     "fish_colors": ["#FF6B35,#F7931E","#FFD700,#FF8C00","#FF4E50,#F9D423","#EF3B36,#FFFFFF","#FFA07A,#FF6347","#FF7F50,#FF4500"]},

    {"id": 103, "nom": "theme_abyssal", "label": "Abysses Violets",   "prix": 90,
     "algue_color": "#6c3483,#9b59b6",
     "bg_gradient": "180deg,#030008,#07001a,#0a0025,#0d0030",
     "fish_colors": ["#8E44AD,#6C3483","#A569BD,#7D3C98","#BB8FCE,#8E44AD","#D7BDE2,#A569BD","#7D3C98,#4A235A","#C39BD3,#884EA0"]},

    {"id": 104, "nom": "theme_biolum",  "label": "Bioluminescent",    "prix": 120,
     "algue_color": "#00ffcc,#00bfff",
     "bg_gradient": "180deg,#000d10,#001520,#001f30,#002a40",
     "fish_colors": ["#00FFFF,#00CED1","#7FFFD4,#00FA9A","#00FF7F,#00CED1","#40E0D0,#48D1CC","#20B2AA,#5F9EA0","#ADFF2F,#7FFF00"]},

    {"id": 105, "nom": "theme_coucher", "label": "Coucher de Soleil", "prix": 70,
     "algue_color": "#d35400,#e67e22",
     "bg_gradient": "180deg,#00080f,#001428,#001f3f,#002855",
     "fish_colors": ["#FF4500,#FF6347","#FF8C00,#FFA500","#FFD700,#FFA07A","#FF7043,#FFAB40","#FF5722,#FF8A65","#FFCA28,#FF7043"]},
]


# ── Helpers de recherche dans les catalogues ──────────────────────────────────

def get_skin_by_id(skin_id):
    """Retourne le dict du skin correspondant à skin_id, ou le skin de base si introuvable."""
    for s in CATALOGUE_SKINS:
        if s["id"] == skin_id:
            return s
    return CATALOGUE_SKINS[0]


def get_theme_by_id(theme_id):
    """Retourne le dict du thème correspondant à theme_id, ou le thème par défaut si introuvable."""
    for t in CATALOGUE_THEMES:
        if t["id"] == theme_id:
            return t
    return CATALOGUE_THEMES[0]


# ══════════════════════════════════════════════════════════════════
#  ÉTAT GLOBAL DU SERVEUR
# ══════════════════════════════════════════════════════════════════

# Timer Pomodoro global (partagé entre tous les utilisateurs connectés)
# ⚠️ Pour un usage multi-utilisateurs, il faudrait un timer par session Flask
session_pomodoro = Session(1800)   # 1800 s = 30 minutes par défaut

# Liste de tâches en mémoire (rechargée depuis la BDD à chaque connexion)
liste_taches = ListeTache()

# Verrou pour protéger les accès concurrents au timer (thread-safe)
_timer_lock = threading.Lock()


# ══════════════════════════════════════════════════════════════════
#  HELPERS INTERNES
# ══════════════════════════════════════════════════════════════════

def get_poissons():
    """Lit le solde de poissons de l'utilisateur connecté directement en BDD.

    Returns:
        Entier (solde actuel), ou 0 si l'utilisateur n'est pas connecté.
    """
    user_id = session.get("user_id")
    if user_id is None:
        return 0
    result = lire_en_bdd("Poissons", "nbr_poisson", f"id_utilisateur = {user_id}")
    return result[0] if result else 0


def set_poissons(nouveau_total: int):
    """Met à jour le solde de poissons de l'utilisateur connecté en BDD."""
    user_id = session.get("user_id")
    if user_id is None:
        return
    modifier_en_bdd("Poissons", f"nbr_poisson = {nouveau_total}", f"id_utilisateur = {user_id}")


def get_apparences_debloquees_ids():
    """Retourne la liste des IDs de skins débloqués par l'utilisateur connecté.

    Le skin de base (id=1) est toujours inclus même s'il n'est pas en BDD.

    Returns:
        Liste d'entiers (IDs des apparences possédées).
    """
    user_id = session.get("user_id")
    if user_id is None:
        return [1]
    try:
        result = lire_en_bdd("Apparence_debloque", "id_apparence", f"id_utilisateur = {user_id}")
        ids = list(result) if result else []
        if 1 not in ids:
            ids.append(1)   # Le skin de base est toujours disponible
        return ids
    except Exception:
        return [1]


def get_apparence_equipee():
    """Retourne le dict de l'apparence actuellement équipée depuis la session Flask.

    Returns:
        Dict avec clés : id, lien_image, hauteur, largeur, zoom.
        Valeurs par défaut (skin de base) si aucune apparence n'est stockée en session.
    """
    return session.get("user_apparence", {
        "id": 1,
        "lien_image": "/static/Skin_de_base.png",
        "hauteur": 45, "largeur": 45, "zoom": 1.0
    })


def get_theme_equipe():
    """Retourne le thème actif depuis la session Flask.

    Returns:
        Dict du thème (voir CATALOGUE_THEMES), ou le thème par défaut.
    """
    return session.get("user_theme", CATALOGUE_THEMES[0])


def _enregistrer_session_bdd(user_id: int, duree_secondes: int):
    """Enregistre une session Pomodoro complétée en BDD.

    Génère un ID unique basé sur le timestamp. Les erreurs sont capturées
    et logguées sans interrompre le flux de l'application.
    """
    try:
        id_session = int(datetime.datetime.now().timestamp() * 1000) % 1000000
        date_fait = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ajouter_en_bdd("Session", [(id_session, duree_secondes, date_fait, 1, user_id)])
    except Exception as e:
        print(f"[BDD] Erreur enregistrement session : {e}")


def _accorder_poissons(user_id: int, duree_secondes: int):
    """Crédite les poissons gagnés à la fin d'une session de travail.

    Gains :
        Session courte (1800 s / 30 min) → 30 poissons
        Session longue (3300 s / 55 min) → 55 poissons

    Returns:
        Tuple (poissons_gagnes, nouveau_total).
    """
    gains = {1800: 30, 3300: 55}
    poissons_gagnes = gains.get(duree_secondes, 30)  # 30 par défaut si durée inconnue
    result = lire_en_bdd("Poissons", "nbr_poisson", f"id_utilisateur = {user_id}")
    ancien = result[0] if result else 0
    nouveau = ancien + poissons_gagnes
    modifier_en_bdd("Poissons", f"nbr_poisson = {nouveau}", f"id_utilisateur = {user_id}")
    return poissons_gagnes, nouveau


def _etat_timer():
    """Construit et retourne le dict d'état du timer (utilisé dans les réponses JSON).

    Returns:
        Dict avec : temps_restant, en_cours, phase, compteur_sessions.
    """
    return {
        "temps_restant":      session_pomodoro.get_temps_restant(),
        "en_cours":           session_pomodoro.sessions_en_cours,
        "phase":              session_pomodoro.phase,
        "compteur_sessions":  session_pomodoro.compteur_sessions,
    }


def build_apparence_dict(skin):
    """Construit le dict standardisé d'une apparence pour les templates et la session Flask.

    Gère les deux cas de nommage possible : "lien" (BDD) ou "lien_image" (session).

    Args:
        skin : Dict brut d'un skin (issu du CATALOGUE_SKINS ou de la BDD).

    Returns:
        Dict normalisé avec clés : id, lien_image, hauteur, largeur, zoom.
    """
    return {
        "id":        skin.get("id", 1),
        "lien_image": skin.get("lien", skin.get("lien_image", "/static/Skin_de_base.png")),
        "hauteur":   skin.get("hauteur", 45),
        "largeur":   skin.get("largeur", 45),
        "zoom":      skin.get("zoom", 1.0),
    }


# ══════════════════════════════════════════════════════════════════
#  ROUTES FLASK
# ══════════════════════════════════════════════════════════════════

@app.route("/", methods=["GET", "POST"])
def login():
    """Page de connexion / inscription.

    GET  → Affiche le formulaire.
    POST → Traite la connexion ou l'inscription selon le bouton "Envoi" cliqué.
           En cas de succès, charge les données de l'utilisateur dans la session Flask
           et redirige vers la page d'accueil.
    """
    if request.method == "POST":
        nom = request.form.get("nom_utilisateur")
        mdp = request.form.get("mdp")

        if nom and mdp:
            user = Utilisateur(nom, mdp)

            if request.form.get("Envoi") == "Connexion":
                if connexion(user):
                    # Stocke les informations clés en session Flask
                    session["nom_utilisateur"] = user.nom_utilisateur
                    session["user_id"]         = user.id_utilisateur

                    # Chargement du skin équipé depuis la BDD
                    skin_equipe = CATALOGUE_SKINS[0]
                    try:
                        row = lire_en_bdd("Apparence_equipe", "*", f"id_utilisateur = {user.id_utilisateur}")
                        if row:
                            id_app = row[0][1]
                            for s in CATALOGUE_SKINS:
                                if s["id"] == id_app:
                                    skin_equipe = s
                                    break
                    except Exception:
                        pass
                    session["user_apparence"] = build_apparence_dict(skin_equipe)

                    # Chargement du thème équipé depuis la BDD
                    theme_equipe = CATALOGUE_THEMES[0]
                    try:
                        row_theme = lire_en_bdd("Apparence_equipe", "id_apparence",
                                                f"id_utilisateur = {user.id_utilisateur} AND type = 'theme'")
                        if row_theme:
                            theme_equipe = get_theme_by_id(row_theme[0])
                    except Exception:
                        pass
                    session["user_theme"] = theme_equipe

                    # Chargement des thèmes possédés
                    try:
                        rows_themes = lire_en_bdd("Apparence_debloque", "id_apparence",
                                                   f"id_utilisateur = {user.id_utilisateur}")
                        themes_ids = [r for r in rows_themes if r >= 101]  # Les thèmes ont des IDs ≥ 101
                        if 101 not in themes_ids:
                            themes_ids.append(101)  # Thème de base toujours disponible
                        session["themes_possedes"] = themes_ids
                    except Exception:
                        session["themes_possedes"] = [101]

                    return redirect(url_for("accueil"))
                else:
                    return render_template("index.html", erreur="Identifiants incorrects")

            if request.form.get("Envoi") == "Inscription":
                if inscription(user):
                    session["nom_utilisateur"] = nom
                    session["user_id"]         = user.id_utilisateur
                    session["user_apparence"]  = build_apparence_dict(CATALOGUE_SKINS[0])
                    session["user_theme"]      = CATALOGUE_THEMES[0]
                    try:
                        ajouter_en_bdd("Apparence_debloque", [(1, user.id_utilisateur)])  # Débloque le skin de base
                    except Exception:
                        pass
                    return redirect(url_for("accueil"))
                else:
                    return render_template("index.html", erreur="Nom d'utilisateur déjà pris")

    return render_template("index.html")


@app.route("/accueil")
def accueil():
    """Page principale : affiche les tâches en cours et l'état du timer.

    Recharge les tâches "A faire" depuis la BDD à chaque visite pour
    rester synchronisé avec les modifications faites dans d'autres onglets.
    Redirige vers /login si l'utilisateur n'est pas connecté.
    """
    if "nom_utilisateur" not in session:
        return redirect(url_for("login"))

    nom = session.get("nom_utilisateur")
    liste_taches.taches = []  # Réinitialisation de la liste en mémoire

    # Rechargement des tâches non terminées depuis la BDD
    data = lire_en_bdd("Tache", "*", f"id_utilisateur = {session['user_id']} AND statut = 'A faire'")
    for t in data:
        tache_obj = Tache(
            titre_tache=t[1], description_tache=t[7],
            date_fin=t[2], id_utilisateur=t[6], priorite=t[3]
        )
        tache_obj.id_tache = t[0]
        liste_taches.taches.append(tache_obj)

    taches = liste_taches.lister_taches()
    theme  = get_theme_equipe()

    return render_template(
        "accueil.html",
        nom_utilisateur=nom,
        taches=taches,
        temps_restant=session_pomodoro.get_temps_restant(),
        en_cours=session_pomodoro.sessions_en_cours,
        phase=session_pomodoro.phase,
        poissons=get_poissons(),
        apparence=get_apparence_equipee(),
        theme=theme,
    )


@app.route("/etat_timer")
def etat_timer():
    """Endpoint JSON : retourne l'état actuel du timer (polling côté client).

    Le front-end interroge cette route régulièrement pour mettre à jour
    l'affichage du compte à rebours en temps réel.
    """
    if "nom_utilisateur" not in session:
        return jsonify({"error": "Non autorisé"}), 403
    with _timer_lock:
        return jsonify(_etat_timer())


@app.route("/ajouter_tache", methods=["POST"])
def ajouter_tache():
    """Endpoint pour créer une nouvelle tâche via le formulaire de l'accueil.

    Lit les champs du formulaire, crée un objet Tache et le persiste en BDD.

    Returns:
        JSON : {id, titre, description} de la tâche créée.
    """
    if "nom_utilisateur" not in session:
        return jsonify({"error": "Non autorisé"}), 403

    user_id      = session.get("user_id")
    titre        = request.form.get("titre_tache")
    desc         = request.form.get("description_tache")
    date_fin_str = request.form.get("date_fin")
    priorite     = int(request.form.get("priorite", 5))

    date_fin = None
    if date_fin_str and date_fin_str.strip():
        date_fin = datetime.datetime.strptime(date_fin_str, '%Y-%m-%d')

    tache = Tache(titre_tache=titre, description_tache=desc,
                  date_fin=date_fin, id_utilisateur=user_id, priorite=priorite)
    liste_taches.ajouter_tache(tache)

    return jsonify({"id": tache.id_tache, "titre": tache.titre_tache, "description": tache.description_tache})


@app.route("/supprimer_tache/<int:id_tache>", methods=["POST"])
def supprimer_tache(id_tache: int):
    """Marque une tâche comme terminée ("Fait") en BDD et la retire de la liste mémoire.

    L'ID de la tâche est passé dans l'URL.
    """
    if "nom_utilisateur" not in session:
        return jsonify({"error": "Non autorisé"}), 403
    liste_taches.supprimer_tache(id_tache)
    return jsonify({"status": "success"})


@app.route("/commande", methods=["POST"])
def commande():
    """Endpoint pour contrôler le timer (start / pause / stop).

    Reçoit un JSON {"action": "start"|"pause"|"stop"} et applique l'action
    sur l'objet session_pomodoro global.

    Returns:
        JSON : état du timer + solde de poissons.
    """
    if "nom_utilisateur" not in session:
        return jsonify({"error": "Non autorisé"}), 403
    data   = request.get_json()
    action = data.get("action")

    with _timer_lock:
        if action == "start":
            session_pomodoro.demarrer_chronometre()
        elif action == "pause":
            session_pomodoro.pause_chronometre()
        elif action == "stop":
            session_pomodoro.arret_chronometre()
        etat = _etat_timer()
        etat["poissons"] = get_poissons()

    return jsonify(etat)


@app.route("/changer_duree", methods=["POST"])
def changer_duree():
    """Endpoint pour modifier la durée de la session de travail (30 ou 55 minutes).

    Reçoit un JSON {"duree": N} avec N en minutes.
    Réinitialise complètement le timer avec la nouvelle durée.
    """
    if "nom_utilisateur" not in session:
        return jsonify({"error": "Non autorisé"}), 403
    data           = request.get_json()
    duree_minutes  = int(data.get("duree", 30))

    with _timer_lock:
        session_pomodoro.changer_duree_chronometre(duree_minutes)
        etat = _etat_timer()

    return jsonify(etat)


@app.route("/fin_session", methods=["POST"])
def fin_session():
    """Endpoint appelé par le front-end quand le timer arrive à 0.

    Gère la transition de phase (travail → pause, ou pause → travail).
    Si c'était une session de travail : enregistre en BDD et crédite les poissons.

    Returns:
        JSON : état du timer + poissons_gagnes + nouveau_total + c_etait_travail.
    """
    if "nom_utilisateur" not in session:
        return jsonify({"error": "Non autorisé"}), 403

    user_id            = session.get("user_id")
    data               = request.get_json()
    poissons_gagnes_js = int(data.get("poissons_gagnes", 30))  # Valeur envoyée par le JS (non utilisée)

    with _timer_lock:
        c_etait_travail = session_pomodoro.terminer_session_travail()
        etat            = _etat_timer()

    if c_etait_travail and user_id:
        # Enregistrement en BDD et crédit de poissons
        _enregistrer_session_bdd(user_id, session_pomodoro.duree_session)
        _, nouveau_total = _accorder_poissons(user_id, session_pomodoro.duree_session)
    else:
        # C'était une pause → pas d'enregistrement, pas de poissons
        nouveau_total      = get_poissons()
        poissons_gagnes_js = 0

    etat["nouveau_total"]      = nouveau_total
    etat["poissons_gagnes"]    = poissons_gagnes_js if c_etait_travail else 0
    etat["c_etait_travail"]    = c_etait_travail

    return jsonify(etat)


@app.route("/shop")
def shop():
    """Page boutique : affiche les skins et thèmes disponibles à l'achat.

    Marque chaque item comme "owned" (possédé) ou "cant-afford" (pas assez de poissons)
    pour que le template affiche les états corrects.
    """
    if "nom_utilisateur" not in session:
        return redirect(url_for("login"))

    possedes_ids   = get_apparences_debloquees_ids()
    theme          = get_theme_equipe()
    themes_possedes = session.get("themes_possedes", [101])

    items_skins = [
        {**s, "owned": s["id"] in possedes_ids, "category": "skin"}
        for s in CATALOGUE_SKINS
    ]
    items_themes = [
        {**t, "owned": t["id"] in themes_possedes, "category": "theme"}
        for t in CATALOGUE_THEMES
    ]

    return render_template("shop.html",
                           nom_utilisateur=session["nom_utilisateur"],
                           poissons=get_poissons(),
                           items_skins=items_skins,
                           items_themes=items_themes,
                           apparence=get_apparence_equipee(),
                           theme=theme)


@app.route("/acheter", methods=["POST"])
def acheter():
    """Endpoint JSON pour acheter un skin ou un thème en boutique.

    Vérifie que l'utilisateur a assez de poissons, déduit le prix,
    enregistre l'achat en BDD et met à jour la session Flask.

    Returns:
        JSON : {success: bool, nouveau_total: int} ou {success: False, message: str}.
    """
    if "nom_utilisateur" not in session:
        return jsonify({"error": "Non autorisé"}), 403

    data     = request.get_json()
    item_id  = int(data.get("item_id", 0))
    prix     = int(data.get("prix", 0))
    category = data.get("category", "skin")
    user_id  = session.get("user_id")

    poissons_actuels = get_poissons()
    if poissons_actuels < prix:
        return jsonify({"success": False, "message": "Pas assez de poissons 🐟"})

    if category == "skin":
        possedes = get_apparences_debloquees_ids()
        if item_id in possedes:
            return jsonify({"success": False, "message": "Article déjà possédé"})
        nouveau_total = poissons_actuels - prix
        set_poissons(nouveau_total)
        try:
            ajouter_en_bdd("Apparence_debloque", [(item_id, user_id)])
        except Exception:
            pass

    elif category == "theme":
        themes_possedes = session.get("themes_possedes", [101])
        if item_id in themes_possedes:
            return jsonify({"success": False, "message": "Thème déjà possédé"})
        nouveau_total = poissons_actuels - prix
        set_poissons(nouveau_total)
        themes_possedes.append(item_id)
        session["themes_possedes"] = themes_possedes
        try:
            ajouter_en_bdd("Apparence_debloque", [(item_id, user_id)])
        except Exception:
            pass
    else:
        return jsonify({"success": False, "message": "Catégorie inconnue"})

    # Met à jour le compteur de poissons dépensés
    try:
        result = lire_en_bdd("Poissons", "poisson_depense", f"id_utilisateur = {user_id}")
        depense_actuel = result[0] if result else 0
        modifier_en_bdd("Poissons", f"poisson_depense = {depense_actuel + prix}", f"id_utilisateur = {user_id}")
    except Exception:
        pass

    return jsonify({"success": True, "nouveau_total": nouveau_total})


@app.route("/equipment")
def equipment():
    """Page d'équipement : affiche les skins et thèmes possédés pour les équiper.

    Filtre les catalogues pour ne montrer que les items que l'utilisateur possède.
    """
    if "nom_utilisateur" not in session:
        return redirect(url_for("login"))

    possedes_ids     = get_apparences_debloquees_ids()
    themes_possedes  = session.get("themes_possedes", [101])
    theme            = get_theme_equipe()

    skins_possedes       = [s for s in CATALOGUE_SKINS   if s["id"] in possedes_ids]
    themes_possedes_list = [t for t in CATALOGUE_THEMES  if t["id"] in themes_possedes]

    skin_actuel_id   = get_apparence_equipee().get("id", 1)
    theme_actuel_id  = theme.get("id", 101)

    return render_template("equipment.html",
                           nom_utilisateur=session["nom_utilisateur"],
                           poissons=get_poissons(),
                           apparence=get_apparence_equipee(),
                           theme=theme,
                           skins_possedes=skins_possedes,
                           themes_possedes=themes_possedes_list,
                           skin_actuel_id=skin_actuel_id,
                           theme_actuel_id=theme_actuel_id)


@app.route("/equiper", methods=["POST"])
def equiper():
    """Endpoint JSON pour équiper un skin ou un thème possédé.

    Met à jour la session Flask et la BDD (table Apparence_equipe)
    pour persister le choix entre les connexions.

    Returns:
        JSON : {success: True, nouveau_skin/nouveau_theme} ou {success: False, message}.
    """
    if "nom_utilisateur" not in session:
        return jsonify({"error": "Non autorisé"}), 403

    data     = request.get_json()
    item_id  = int(data.get("id_item", 0))
    category = data.get("category", "skin")
    user_id  = session.get("user_id")

    if category == "skin":
        possedes = get_apparences_debloquees_ids()
        if item_id not in possedes:
            return jsonify({"success": False, "message": "Non possédé"})
        skin = get_skin_by_id(item_id)
        session["user_apparence"] = build_apparence_dict(skin)
        try:
            existe = lire_en_bdd("Apparence_equipe", "id_utilisateur", f"id_utilisateur = {user_id}")
            if existe:
                modifier_en_bdd("Apparence_equipe",
                                f"id_apparence = {item_id}, prix = {skin['prix']}, type = '{skin['type']}'",
                                f"id_utilisateur = {user_id}")
            else:
                ajouter_en_bdd("Apparence_equipe", [(skin["prix"], item_id, user_id, skin["type"])])
        except Exception as e:
            print(f"Erreur équipement BDD: {e}")
        return jsonify({"success": True, "nouveau_skin": build_apparence_dict(skin)})

    elif category == "theme":
        themes_possedes = session.get("themes_possedes", [101])
        if item_id not in themes_possedes:
            return jsonify({"success": False, "message": "Non possédé"})
        theme = get_theme_by_id(item_id)
        session["user_theme"] = theme
        try:
            existe_theme = lire_en_bdd("Apparence_equipe", "id_utilisateur",
                                       f"id_utilisateur = {user_id} AND type = 'theme'")
            if existe_theme:
                modifier_en_bdd("Apparence_equipe",
                                f"id_apparence = {item_id}, prix = {theme['prix']}",
                                f"id_utilisateur = {user_id} AND type = 'theme'")
            else:
                ajouter_en_bdd("Apparence_equipe", [(theme["prix"], item_id, user_id, "theme")])
        except Exception as e:
            print(f"Erreur sauvegarde thème BDD: {e}")
        return jsonify({"success": True, "nouveau_theme": theme})

    return jsonify({"success": False, "message": "Catégorie inconnue"})


@app.route("/stats")
def stats():
    """Page statistiques : génère et injecte les 4 graphes matplotlib en SVG.

    Les graphes sont générés à chaque requête (pas de cache).
    Pour de meilleures performances avec beaucoup d'utilisateurs,
    envisager de mettre en cache les SVG générés.
    """
    if "nom_utilisateur" not in session:
        return redirect(url_for("login"))
    theme = get_theme_equipe()

    return render_template("stats.html",
                           nom_utilisateur=session["nom_utilisateur"],
                           graphe1=temps_total_travailles(session["user_id"]),    # Barres : heures/jour
                           graphe2=camembert_tache(session["user_id"]),            # Camembert : priorités
                           graphe3=graphe_session_pomodoro(session["user_id"]),    # Courbe : sessions cumulées
                           graphe4=graphe_tache(session["user_id"]),               # Courbe : tâches cumulées
                           temps_total=calcul_temps_total(session["user_id"]),
                           session_total=max_session_compteur(session["user_id"]),
                           tache_total=max_tache_compteur(session["user_id"]),
                           poissons=get_poissons(),
                           apparence=get_apparence_equipee(),
                           theme=theme)


@app.route("/timer")
def fullscreen():
    """Page timer plein écran : affichage simplifié du Pomodoro sans les tâches."""
    if "nom_utilisateur" not in session:
        return redirect(url_for("login"))
    theme = get_theme_equipe()
    return render_template(
        "fullscreen.html",
        temps_restant=session_pomodoro.get_temps_restant(),
        phase=session_pomodoro.phase,
        poissons=get_poissons(),
        apparence=get_apparence_equipee(),
        theme=theme,
    )


@app.route("/aide")
def aide():
    """Page d'aide : accessible même sans être connecté.

    Fournit les données de thème et d'apparence pour maintenir la cohérence visuelle.
    """
    apparence = get_apparence_equipee() if "nom_utilisateur" in session else build_apparence_dict(CATALOGUE_SKINS[0])
    theme     = get_theme_equipe()      if "nom_utilisateur" in session else CATALOGUE_THEMES[0]
    return render_template("aide.html",
                           nom_utilisateur=session.get("nom_utilisateur", ""),
                           poissons=get_poissons(),
                           apparence=apparence,
                           theme=theme,
                           logged_in="nom_utilisateur" in session)


@app.route("/cheat/<int:montant>")
def cheat(montant):
    """Route de triche pour définir manuellement son solde de poissons.

    ⚠️ À SUPPRIMER AVANT TOUT DÉPLOIEMENT EN PRODUCTION.
    Exemple : GET /cheat/999 → attribue 999 poissons à l'utilisateur connecté.
    """
    user_id = session.get("user_id")
    if not user_id:
        return "Non connecté", 403
    modifier_en_bdd("Poissons", f"nbr_poisson = {montant}", f"id_utilisateur = {user_id}")
    return f"✅ Tu as maintenant {montant} poissons !", 200


# ══════════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # debug=True active le rechargement automatique et les messages d'erreur détaillés.
    # ⚠️ Passer debug=False en production.
    app.run(port=5555, debug=True)
