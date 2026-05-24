from base_de_donnees_fonction import *
from classe_projet import *


# ══════════════════════════════════════════════════════════════════
#              PAGE D'INSCRIPTION / CONNEXION
# ══════════════════════════════════════════════════════════════════

def connexion(utilisateur: Utilisateur):
    """Tente de connecter l'utilisateur en vérifiant ses identifiants en BDD.

    Appelle recuperer_information() qui charge toutes les données du compte
    si le couple (nom_utilisateur, mot_de_passe) est valide.

    Returns:
        True  → connexion réussie (les attributs de l'objet sont remplis).
        False → identifiants incorrects ou compte inexistant.
    """
    return utilisateur.recuperer_information() != False


def inscription(utilisateur: Utilisateur):
    """Inscrit un nouvel utilisateur dans la base de données.

    Appelle sauvegarde() qui crée les lignes nécessaires dans toutes les tables.

    Returns:
        True  → inscription réussie (nouveau compte créé).
        False → le compte existait déjà (sauvegarde() a retourné False).
    """
    return utilisateur.sauvegarde() != False


# ══════════════════════════════════════════════════════════════════
#                        STATISTIQUES
# ══════════════════════════════════════════════════════════════════

def calcul_temps_total(id_utilisateur: int):
    """Calcule le temps de travail total de l'utilisateur depuis la création du compte.

    Récupère toutes les durées de sessions en BDD, distingue les sessions
    courtes (30 min = 1800 s) des longues (55 min = 3300 s) et convertit
    le total en heures + minutes.

    Returns:
        Chaîne formatée de la forme "Xh0Y" (ex: "3h45", "1h00").
    """
    data = lire_en_bdd(nom_table_session, "duree", f"id_utilisateur = {id_utilisateur}")
    cmpt_courte = 0  # Nombre de sessions de 30 minutes
    cmpt_longue = 0  # Nombre de sessions de 55 minutes

    if not data:
        return "0h00"

    for session in data:
        if int(session) == 1800:
            cmpt_courte += 1
        elif int(session) == 3300:
            cmpt_longue += 1

    total_secondes = cmpt_courte * 1800 + cmpt_longue * 3300
    total   = total_secondes // 3600          # Partie entière = heures
    minutes = (total_secondes % 3600) // 60   # Reste = minutes

    # Formatage pour garantir deux chiffres pour les minutes (ex: "2h05" et non "2h5")
    if len(str(minutes)) == 1:
        minutes = "0" + str(minutes)
    else:
        minutes = str(minutes)

    return f'{total}h{minutes}'


def jour_de_la_semaine():
    """Construit la liste des 7 derniers jours du lundi au dimanche, centrée sur aujourd'hui.

    Le dernier élément est toujours le jour actuel, le premier est il y a 6 jours.
    Utilisée pour l'axe des abscisses des graphes en barres.

    Returns:
        Liste de 7 chaînes de type ["Mer", "Jeu", "Ven", "Sam", "Dim", "Lun", "Mar"]
        (exemple si aujourd'hui est mardi).
    """
    semaine = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    dernier_jour = datetime.datetime.now().date()
    result = []

    # On part d'il y a 6 jours (i=6) jusqu'à aujourd'hui (i=0)
    for i in range(6, -1, -1):
        # timedelta permet de soustraire i jours à la date d'aujourd'hui
        result.append(semaine[(dernier_jour - datetime.timedelta(days=i)).weekday()])

    return result


def graphe_temps_total(id_utilisateur: int):
    """Retourne le temps de travail (en heures) pour chacun des 7 derniers jours.

    Construit un dictionnaire date → total de secondes travaillées ce jour-là,
    puis convertit les valeurs en heures décimales arrondies au centième.

    Returns:
        Liste de 7 flottants (heures), du jour le plus ancien au plus récent.
        Exemple: [0.5, 0, 1.83, 0, 0.5, 0, 1.0]
    """
    dico = {}   # {date: secondes_totales}
    result = []

    data = lire_en_bdd(nom_table_session, 'duree, date_fait', f"id_utilisateur = {id_utilisateur}")
    # Conversion : on garde seulement la date (sans l'heure) pour regrouper par jour
    data = [(session[0], datetime.datetime.strptime(session[1], "%Y-%m-%d %H:%M:%S").date())
            for session in data]
    date_triee = sorted(data, key=lambda x: x[1], reverse=True)
    dernier_jour = datetime.datetime.now().date()

    # Initialise le dictionnaire pour les 7 derniers jours à 0
    for i in range(6, -1, -1):
        dico[dernier_jour - datetime.timedelta(days=i)] = 0

    # Remplit le dictionnaire avec les durées des sessions de la semaine
    for i in range(len(date_triee)):
        if date_triee[i][1] in dico:
            dico[date_triee[i][1]] += int(date_triee[i][0])

    # Conversion secondes → heures pour chaque jour
    for cle in dico.keys():
        result.append(round(dico[cle] / 3600, 2))

    return result


def graphe_nbr_session(id_utilisateur: int):
    """Retourne l'évolution cumulée du nombre de sessions sur les 7 derniers jours.

    Chaque point représente le total cumulé de sessions depuis la création du compte,
    à la date indiquée (courbe croissante).

    Returns:
        Liste de tuples (date_str, total_cumulé) sur 7 jours max.
        Exemple: [("28/04", 12), ("29/04", 14), ..., ("03/05", 20)]
    """
    temp = []
    dico = {}   # {date: nombre de sessions ce jour}
    result = []

    data = lire_en_bdd(nom_table_session, "date_fait", f"id_utilisateur = {id_utilisateur}")
    # On ne garde que la date (sans heure)
    data = [datetime.datetime.strptime(session, "%Y-%m-%d %H:%M:%S").date() for session in data]
    now = datetime.datetime.now().date()

    # Comptage du nombre de sessions par jour
    for session in data:
        if session in dico:
            dico[session] += 1
        else:
            dico[session] = 1

    # S'assurer que le jour actuel est présent même sans session
    if now not in dico:
        dico[now] = 0

    # Conversion du dict en liste de tuples triée par date
    for cle in dico.keys():
        temp.append((cle, dico[cle]))
    temp = sorted(temp, key=lambda x: x[0])

    # Calcul du total cumulé : chaque point = total de toutes les sessions jusqu'à ce jour
    total = 0
    for date in temp:
        result.append((date[0], total + date[1]))
        total += date[1]

    # On ne garde que les 7 derniers jours et on formate les dates en "JJ/MM"
    result = result[-7:]
    result = [(session[0].strftime("%d/%m"), session[1]) for session in result]

    return result


def max_session_compteur(id_utilisateur: int):
    """Retourne le nombre total de sessions enregistrées par l'utilisateur.

    Utilisé pour afficher le compteur global sur la page statistiques
    et pour ajuster le pas de l'axe Y des graphes.

    Returns:
        Entier représentant le nombre de sessions.
    """
    data = lire_en_bdd(nom_table_session, 'id', f"id_utilisateur = {id_utilisateur}")
    return len(data)


def max_tache_compteur(id_utilisateur: int):
    """Retourne le nombre total de tâches créées par l'utilisateur.

    Utilisé pour afficher le compteur global et calibrer l'axe Y du graphe de tâches.

    Returns:
        Entier représentant le nombre de tâches.
    """
    data = lire_en_bdd(nom_table_tache, "id", f"id_utilisateur = {id_utilisateur}")
    return len(data)


def graphe_tache_liste(id_utilisateur: int):
    """Retourne l'évolution cumulée du nombre de tâches créées sur les 7 derniers jours.

    Similaire à graphe_nbr_session mais pour les tâches.
    Le format de date en BDD pour les tâches est différent (ISO avec microsecondes).

    Returns:
        Liste de tuples (date_str, total_cumulé) sur 7 jours max.
        Exemple: [("28/04", 3), ("29/04", 5), ..., ("03/05", 11)]
    """
    dico = {}
    result = []

    data = lire_en_bdd(nom_table_tache, "date_creation", f"id_utilisateur = {id_utilisateur}")
    # Format de date différent des sessions : "YYYY-MM-DDTHH:MM:SS.ffffff"
    data = [datetime.datetime.strptime(tache, "%Y-%m-%dT%H:%M:%S.%f").date() for tache in data]
    now = datetime.datetime.now().date()

    # Initialise les 7 derniers jours
    for i in range(6, -1, -1):
        dico[now - datetime.timedelta(days=i)] = 0

    # Comptage des tâches par jour
    for tache in data:
        if tache in dico:
            dico[tache] += 1
        else:
            dico[tache] = 1

    # Calcul du total cumulé
    total = 0
    temp = [(cle, dico[cle]) for cle in dico.keys()]
    for tache in temp:
        result.append((tache[0], total + tache[1]))
        total += tache[1]

    # Tri, limitation aux 7 derniers jours et formatage
    result = sorted(result, key=lambda x: x[0])
    result = result[-7:]
    result = [(tache[0].strftime("%d/%m"), tache[1]) for tache in result]

    return result


def camembert_donnees(id_utilisateur: int):
    """Prépare les données pour le graphe camembert des priorités de tâches.

    Calcule la proportion (en %) de tâches pour chaque niveau de priorité (0 à 5).

    Returns:
        Liste de tuples (label, pourcentage) triés par priorité.
        Exemple: [("priorité 1", 40.0), ("priorité 2", 35.0), ("priorité 5", 25.0)]
        Retourne [] si l'utilisateur n'a aucune tâche.
    """
    data = lire_en_bdd(nom_table_tache, "priorite", f"id_utilisateur = {id_utilisateur}")
    dico = {}

    if not data:
        return []  # Pas de données → graphe vide

    maxi = len(data)  # Total des tâches pour calculer les pourcentages

    # Comptage des tâches par niveau de priorité
    for tache in data:
        if tache in dico:
            dico[tache] += 1
        else:
            dico[tache] = 1

    # Conversion en pourcentages
    for cle in dico.keys():
        dico[cle] = (dico[cle] / maxi) * 100

    # Construction de la liste finale triée par niveau de priorité
    cles = sorted([cle for cle in dico.keys()])
    legende = ["priorité " + str(cle) for cle in cles]
    donnees = [dico[cle] for cle in cles]
    donnees = [(legende[i], donnees[i]) for i in range(len(donnees))]

    return donnees


# ══════════════════════════════════════════════════════════════════
#               RÉCUPÉRATION DES APPARENCES
# ══════════════════════════════════════════════════════════════════

def recup_apparence():
    """Charge tous les skins disponibles depuis la table Apparence_disponible.

    Transforme les tuples bruts de la BDD en dictionnaires facilement exploitables
    dans les templates Jinja2 et la logique boutique.

    Returns:
        Liste de dictionnaires, chacun représentant un skin :
        {"id", "nom", "lien", "prix", "largeur", "hauteur", "zoom"}
    """
    apparences = lire_en_bdd(nom_table_apparence__dispo, "*", "1 + 1 = 2")  # Sélectionne tout (condition toujours vraie)
    result = []

    for apparence in apparences:
        dico = {}
        dico["id"]      = apparence[0]
        dico["nom"]     = apparence[3]
        dico["lien"]    = apparence[6]
        dico["prix"]    = apparence[2]
        dico["largeur"] = apparence[5]
        dico["hauteur"] = apparence[4]
        dico["zoom"]    = apparence[7]
        dico["type"]    = apparence[1]  # "skin" ou autre type d'apparence
        result.append(dico)

    return result
