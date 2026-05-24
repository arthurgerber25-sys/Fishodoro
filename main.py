from flask import Flask, render_template, request, jsonify, url_for, redirect, session
from classe_projet import Session, Utilisateur, Tache, ListeTache, Apparence
import datetime
import threading
from base_de_donnees_fonction import *
from fonctions import *
from statistiques import *
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cle_secrete_super_random_123")


# ══════════════════════════════════════════════════════════════════
#  CATALOGUES
# ══════════════════════════════════════════════════════════════════

CATALOGUE_SKINS = recup_apparence()

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


def get_skin_by_id(skin_id):
    for s in CATALOGUE_SKINS:
        if s["id"] == skin_id:
            return s
    return CATALOGUE_SKINS[0] if CATALOGUE_SKINS else {"id": 1, "lien": "/static/Skin_de_base.png", "hauteur": 45, "largeur": 45, "zoom": 1.0, "prix": 0, "type": "skin", "nom": "skin_de_base"}


def get_theme_by_id(theme_id):
    for t in CATALOGUE_THEMES:
        if t["id"] == theme_id:
            return t
    return CATALOGUE_THEMES[0]


# ══════════════════════════════════════════════════════════════════
#  ÉTAT GLOBAL
# ══════════════════════════════════════════════════════════════════

_timers: dict = {}
_listes: dict = {}
_timer_lock = threading.Lock()


def _get_timer(user_id: int) -> Session:
    if user_id not in _timers:
        _timers[user_id] = Session(1800)
    return _timers[user_id]


def _get_liste(user_id: int) -> ListeTache:
    if user_id not in _listes:
        _listes[user_id] = ListeTache()
    return _listes[user_id]


# ══════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════

def get_poissons():
    user_id = session.get("user_id")
    if user_id is None:
        return 0
    result = lire_en_bdd("Poissons", "nbr_poisson", f"id_utilisateur = {user_id}")
    return result[0] if result else 0


def set_poissons(nouveau_total: int):
    user_id = session.get("user_id")
    if user_id is None:
        return
    modifier_en_bdd("Poissons", f"nbr_poisson = {nouveau_total}", f"id_utilisateur = {user_id}")


def get_apparences_debloquees_ids():
    user_id = session.get("user_id")
    if user_id is None:
        return [1]
    try:
        result = lire_en_bdd("Apparence_debloque", "id_apparence", f"id_utilisateur = {user_id}")
        ids = list(result) if result else []
        if 1 not in ids:
            ids.append(1)
        return ids
    except Exception:
        return [1]


def get_apparence_equipee():
    return session.get("user_apparence", {
        "id": 1,
        "lien_image": "/static/Skin_de_base.png",
        "hauteur": 45, "largeur": 45, "zoom": 1.0
    })


def get_theme_equipe():
    return session.get("user_theme", CATALOGUE_THEMES[0])


def _enregistrer_session_bdd(user_id: int, duree_secondes: int):
    try:
        id_session = int(datetime.datetime.now().timestamp() * 1000) % 1000000
        date_fait = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Session : (id, duree, date_fait, statut, id_utilisateur)
        # duree stocké en TEXT dans ta BDD → on passe une string
        ajouter_en_bdd("Session", [(id_session, str(duree_secondes), date_fait, 1, user_id)])
    except Exception as e:
        print(f"[BDD] Erreur enregistrement session : {e}")


def _accorder_poissons(user_id: int, duree_secondes: int):
    gains = {1800: 30, 3300: 55}
    poissons_gagnes = gains.get(duree_secondes, 30)
    result = lire_en_bdd("Poissons", "nbr_poisson", f"id_utilisateur = {user_id}")
    ancien = result[0] if result else 0
    nouveau = ancien + poissons_gagnes
    modifier_en_bdd("Poissons", f"nbr_poisson = {nouveau}", f"id_utilisateur = {user_id}")
    return poissons_gagnes, nouveau


def build_apparence_dict(skin):
    return {
        "id":         skin.get("id", 1),
        "lien_image": skin.get("lien", skin.get("lien_image", "/static/Skin_de_base.png")),
        "hauteur":    skin.get("hauteur", 45),
        "largeur":    skin.get("largeur", 45),
        "zoom":       skin.get("zoom", 1.0),
    }


# ══════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        nom = request.form.get("nom_utilisateur")
        mdp = request.form.get("mdp")

        if nom and mdp:
            user = Utilisateur(nom, mdp)

            if request.form.get("Envoi") == "Connexion":
                if connexion(user):
                    session["nom_utilisateur"] = user.nom_utilisateur
                    session["user_id"]         = user.id_utilisateur

                    skin_equipe = CATALOGUE_SKINS[0] if CATALOGUE_SKINS else None
                    try:
                        row = lire_en_bdd("Apparence_equipe", "*", f"id_utilisateur = {user.id_utilisateur}")
                        if row:
                            # Apparence_equipe : (id_utilisateur, id_apparence, prix, type)
                            id_app = row[0][1]
                            for s in CATALOGUE_SKINS:
                                if s["id"] == id_app:
                                    skin_equipe = s
                                    break
                    except Exception:
                        pass
                    session["user_apparence"] = build_apparence_dict(skin_equipe) if skin_equipe else {"id": 1, "lien_image": "/static/Skin_de_base.png", "hauteur": 45, "largeur": 45, "zoom": 1.0}

                    theme_equipe = CATALOGUE_THEMES[0]
                    try:
                        row_theme = lire_en_bdd("Apparence_equipe", "id_apparence",
                                                f"id_utilisateur = {user.id_utilisateur} AND type = 'theme'")
                        if row_theme:
                            theme_equipe = get_theme_by_id(row_theme[0])
                    except Exception:
                        pass
                    session["user_theme"] = theme_equipe

                    try:
                        rows_themes = lire_en_bdd("Apparence_debloque", "id_apparence",
                                                   f"id_utilisateur = {user.id_utilisateur}")
                        themes_ids = [r for r in rows_themes if r >= 101]
                        if 101 not in themes_ids:
                            themes_ids.append(101)
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
                    session["user_apparence"]  = build_apparence_dict(CATALOGUE_SKINS[0]) if CATALOGUE_SKINS else {"id": 1, "lien_image": "/static/Skin_de_base.png", "hauteur": 45, "largeur": 45, "zoom": 1.0}
                    session["user_theme"]      = CATALOGUE_THEMES[0]
                    session["themes_possedes"] = [101]
                    try:
                        ajouter_en_bdd("Apparence_debloque", [(1, user.id_utilisateur)])
                    except Exception:
                        pass
                    try:
                        skin = CATALOGUE_SKINS[0]
                        ajouter_en_bdd("Apparence_equipe",
                                       [(user.id_utilisateur, skin["id"], skin["prix"], skin["type"])])
                    except Exception:
                        pass
                    return redirect(url_for("accueil"))
                else:
                    return render_template("index.html", erreur="Nom d'utilisateur déjà pris")

    return render_template("index.html")


@app.route("/accueil")
def accueil():
    if "nom_utilisateur" not in session:
        return redirect(url_for("login"))

    nom = session.get("nom_utilisateur")
    user_id = session["user_id"]
    timer = _get_timer(user_id)
    lt = _get_liste(user_id)
    lt.taches = []

    # statut = 0 (INTEGER) pour "A faire" dans ta BDD
    data = lire_en_bdd("Tache", "*", f"id_utilisateur = {user_id} AND statut = 0")
    for t in data:
        tache_obj = Tache(
            titre_tache=t[1], description_tache=t[7],
            date_fin=t[2], id_utilisateur=t[6], priorite=t[3]
        )
        tache_obj.id_tache = t[0]
        lt.taches.append(tache_obj)

    taches = lt.lister_taches()
    theme  = get_theme_equipe()

    return render_template(
        "accueil.html",
        nom_utilisateur=nom,
        taches=taches,
        temps_restant=timer.get_temps_restant(),
        en_cours=timer.sessions_en_cours,
        phase=timer.phase,
        poissons=get_poissons(),
        apparence=get_apparence_equipee(),
        theme=theme,
    )


@app.route("/etat_timer")
def etat_timer():
    if "nom_utilisateur" not in session:
        return jsonify({"error": "Non autorisé"}), 403
    with _timer_lock:
        timer = _get_timer(session["user_id"])
        return jsonify({
            "temps_restant":     timer.get_temps_restant(),
            "en_cours":          timer.sessions_en_cours,
            "phase":             timer.phase,
            "compteur_sessions": timer.compteur_sessions,
        })


@app.route("/ajouter_tache", methods=["POST"])
def ajouter_tache():
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
    _get_liste(user_id).ajouter_tache(tache)

    return jsonify({"id": tache.id_tache, "titre": tache.titre_tache, "description": tache.description_tache})


@app.route("/supprimer_tache/<int:id_tache>", methods=["POST"])
def supprimer_tache(id_tache: int):
    if "nom_utilisateur" not in session:
        return jsonify({"error": "Non autorisé"}), 403
    _get_liste(session["user_id"]).supprimer_tache(id_tache)
    return jsonify({"status": "success"})


@app.route("/commande", methods=["POST"])
def commande():
    if "nom_utilisateur" not in session:
        return jsonify({"error": "Non autorisé"}), 403
    data   = request.get_json()
    action = data.get("action")

    with _timer_lock:
        timer = _get_timer(session["user_id"])
        if action == "start":
            timer.demarrer_chronometre()
        elif action == "pause":
            timer.pause_chronometre()
        elif action == "stop":
            timer.arret_chronometre()
        etat = {
            "temps_restant":     timer.get_temps_restant(),
            "en_cours":          timer.sessions_en_cours,
            "phase":             timer.phase,
            "compteur_sessions": timer.compteur_sessions,
            "poissons":          get_poissons(),
        }

    return jsonify(etat)


@app.route("/changer_duree", methods=["POST"])
def changer_duree():
    if "nom_utilisateur" not in session:
        return jsonify({"error": "Non autorisé"}), 403
    data           = request.get_json()
    duree_minutes  = int(data.get("duree", 30))

    with _timer_lock:
        timer = _get_timer(session["user_id"])
        timer.changer_duree_chronometre(duree_minutes)
        etat = {
            "temps_restant":     timer.get_temps_restant(),
            "en_cours":          timer.sessions_en_cours,
            "phase":             timer.phase,
            "compteur_sessions": timer.compteur_sessions,
        }

    return jsonify(etat)


@app.route("/fin_session", methods=["POST"])
def fin_session():
    if "nom_utilisateur" not in session:
        return jsonify({"error": "Non autorisé"}), 403

    user_id            = session.get("user_id")
    data               = request.get_json()
    poissons_gagnes_js = int(data.get("poissons_gagnes", 30))

    with _timer_lock:
        timer = _get_timer(user_id)
        c_etait_travail = timer.terminer_session_travail()
        etat = {
            "temps_restant":     timer.get_temps_restant(),
            "en_cours":          timer.sessions_en_cours,
            "phase":             timer.phase,
            "compteur_sessions": timer.compteur_sessions,
        }

    if c_etait_travail and user_id:
        _enregistrer_session_bdd(user_id, timer.duree_session)
        _, nouveau_total = _accorder_poissons(user_id, timer.duree_session)
    else:
        nouveau_total      = get_poissons()
        poissons_gagnes_js = 0

    etat["nouveau_total"]   = nouveau_total
    etat["poissons_gagnes"] = poissons_gagnes_js if c_etait_travail else 0
    etat["c_etait_travail"] = c_etait_travail

    return jsonify(etat)


@app.route("/shop")
def shop():
    if "nom_utilisateur" not in session:
        return redirect(url_for("login"))

    possedes_ids    = get_apparences_debloquees_ids()
    theme           = get_theme_equipe()
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

    try:
        result = lire_en_bdd("Poissons", "poissons_depense", f"id_utilisateur = {user_id}")
        depense_actuel = result[0] if result else 0
        modifier_en_bdd("Poissons", f"poissons_depense = {depense_actuel + prix}", f"id_utilisateur = {user_id}")
    except Exception:
        pass

    return jsonify({"success": True, "nouveau_total": nouveau_total})


@app.route("/equipment")
def equipment():
    if "nom_utilisateur" not in session:
        return redirect(url_for("login"))

    possedes_ids     = get_apparences_debloquees_ids()
    themes_possedes  = session.get("themes_possedes", [101])
    theme            = get_theme_equipe()

    skins_possedes       = [s for s in CATALOGUE_SKINS   if s["id"] in possedes_ids]
    themes_possedes_list = [t for t in CATALOGUE_THEMES  if t["id"] in themes_possedes]

    skin_actuel_id  = get_apparence_equipee().get("id", 1)
    theme_actuel_id = theme.get("id", 101)

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
            existe = lire_en_bdd("Apparence_equipe", "id_utilisateur",
                                 f"id_utilisateur = {user_id} AND type = 'skin'")
            if existe:
                modifier_en_bdd("Apparence_equipe",
                                f"id_apparence = {item_id}, prix = {skin['prix']}",
                                f"id_utilisateur = {user_id} AND type = 'skin'")
            else:
                ajouter_en_bdd("Apparence_equipe", [(user_id, item_id, skin["prix"], skin["type"])])
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
                ajouter_en_bdd("Apparence_equipe", [(user_id, item_id, theme["prix"], "theme")])
        except Exception as e:
            print(f"Erreur sauvegarde thème BDD: {e}")
        return jsonify({"success": True, "nouveau_theme": theme})

    return jsonify({"success": False, "message": "Catégorie inconnue"})


@app.route("/stats")
def stats():
    if "nom_utilisateur" not in session:
        return redirect(url_for("login"))
    theme = get_theme_equipe()

    return render_template("stats.html",
                           nom_utilisateur=session["nom_utilisateur"],
                           graphe1=temps_total_travailles(session["user_id"]),
                           graphe2=camembert_tache(session["user_id"]),
                           graphe3=graphe_session_pomodoro(session["user_id"]),
                           graphe4=graphe_tache(session["user_id"]),
                           temps_total=calcul_temps_total(session["user_id"]),
                           session_total=max_session_compteur(session["user_id"]),
                           tache_total=max_tache_compteur(session["user_id"]),
                           poissons=get_poissons(),
                           apparence=get_apparence_equipee(),
                           theme=theme)


@app.route("/timer")
def fullscreen():
    if "nom_utilisateur" not in session:
        return redirect(url_for("login"))
    theme = get_theme_equipe()
    timer = _get_timer(session["user_id"])
    return render_template(
        "fullscreen.html",
        temps_restant=timer.get_temps_restant(),
        phase=timer.phase,
        poissons=get_poissons(),
        apparence=get_apparence_equipee(),
        theme=theme,
    )


@app.route("/aide")
def aide():
    apparence = get_apparence_equipee() if "nom_utilisateur" in session else build_apparence_dict(CATALOGUE_SKINS[0]) if CATALOGUE_SKINS else {"id": 1, "lien_image": "/static/Skin_de_base.png", "hauteur": 45, "largeur": 45, "zoom": 1.0}
    theme     = get_theme_equipe()      if "nom_utilisateur" in session else CATALOGUE_THEMES[0]
    return render_template("aide.html",
                           nom_utilisateur=session.get("nom_utilisateur", ""),
                           poissons=get_poissons(),
                           apparence=apparence,
                           theme=theme,
                           logged_in="nom_utilisateur" in session)


@app.route("/cheat/<int:montant>")
def cheat(montant):
    user_id = session.get("user_id")
    if not user_id:
        return "Non connecté", 403
    modifier_en_bdd("Poissons", f"nbr_poisson = {montant}", f"id_utilisateur = {user_id}")
    return f"✅ Tu as maintenant {montant} poissons !", 200


if __name__ == "__main__":
    app.run(port=5555, debug=True)
