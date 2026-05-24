from base_de_donnees_fonction import *
from classe_projet import *


def connexion(utilisateur: Utilisateur):
    return utilisateur.recuperer_information() != False


def inscription(utilisateur: Utilisateur):
    return utilisateur.sauvegarde() != False


def calcul_temps_total(id_utilisateur: int):
    # duree est TEXT dans la BDD → on convertit en int avant de comparer
    data = lire_en_bdd(nom_table_session, "duree", f"id_utilisateur = {id_utilisateur}")
    cmpt_courte = 0
    cmpt_longue = 0

    if not data:
        return "0h00"

    for session in data:
        try:
            val = int(session)
        except (ValueError, TypeError):
            continue
        if val == 1800:
            cmpt_courte += 1
        elif val == 3300:
            cmpt_longue += 1

    total_secondes = cmpt_courte * 1800 + cmpt_longue * 3300
    total   = total_secondes // 3600
    minutes = (total_secondes % 3600) // 60

    if len(str(minutes)) == 1:
        minutes = "0" + str(minutes)
    else:
        minutes = str(minutes)

    return f'{total}h{minutes}'


def jour_de_la_semaine():
    semaine = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    dernier_jour = datetime.datetime.now().date()
    result = []
    for i in range(6, -1, -1):
        result.append(semaine[(dernier_jour - datetime.timedelta(days=i)).weekday()])
    return result


def graphe_temps_total(id_utilisateur: int):
    dico = {}
    result = []

    data = lire_en_bdd(nom_table_session, 'duree, date_fait', f"id_utilisateur = {id_utilisateur}")
    data = [(session[0], datetime.datetime.strptime(session[1], "%Y-%m-%d %H:%M:%S").date())
            for session in data]
    date_triee = sorted(data, key=lambda x: x[1], reverse=True)
    dernier_jour = datetime.datetime.now().date()

    for i in range(6, -1, -1):
        dico[dernier_jour - datetime.timedelta(days=i)] = 0

    for i in range(len(date_triee)):
        if date_triee[i][1] in dico:
            try:
                dico[date_triee[i][1]] += int(date_triee[i][0])
            except (ValueError, TypeError):
                pass

    for cle in dico.keys():
        result.append(round(dico[cle] / 3600, 2))

    return result


def graphe_nbr_session(id_utilisateur: int):
    temp = []
    dico = {}
    result = []

    data = lire_en_bdd(nom_table_session, "date_fait", f"id_utilisateur = {id_utilisateur}")
    data = [datetime.datetime.strptime(session, "%Y-%m-%d %H:%M:%S").date() for session in data]
    now = datetime.datetime.now().date()

    for session in data:
        if session in dico:
            dico[session] += 1
        else:
            dico[session] = 1

    if now not in dico:
        dico[now] = 0

    for cle in dico.keys():
        temp.append((cle, dico[cle]))
    temp = sorted(temp, key=lambda x: x[0])

    total = 0
    for date in temp:
        result.append((date[0], total + date[1]))
        total += date[1]

    result = result[-7:]
    result = [(session[0].strftime("%d/%m"), session[1]) for session in result]

    return result


def max_session_compteur(id_utilisateur: int):
    data = lire_en_bdd(nom_table_session, 'id', f"id_utilisateur = {id_utilisateur}")
    return len(data)


def max_tache_compteur(id_utilisateur: int):
    data = lire_en_bdd(nom_table_tache, "id", f"id_utilisateur = {id_utilisateur}")
    return len(data)


def graphe_tache_liste(id_utilisateur: int):
    dico = {}
    result = []

    data = lire_en_bdd(nom_table_tache, "date_creation", f"id_utilisateur = {id_utilisateur}")
    now = datetime.datetime.now().date()

    parsed = []
    for tache in data:
        try:
            # Format avec microsecondes
            parsed.append(datetime.datetime.strptime(tache, "%Y-%m-%dT%H:%M:%S.%f").date())
        except ValueError:
            try:
                # Format sans microsecondes
                parsed.append(datetime.datetime.strptime(tache, "%Y-%m-%dT%H:%M:%S").date())
            except ValueError:
                pass

    for i in range(6, -1, -1):
        dico[now - datetime.timedelta(days=i)] = 0

    for tache in parsed:
        if tache in dico:
            dico[tache] += 1
        else:
            dico[tache] = 1

    total = 0
    temp = [(cle, dico[cle]) for cle in dico.keys()]
    for tache in temp:
        result.append((tache[0], total + tache[1]))
        total += tache[1]

    result = sorted(result, key=lambda x: x[0])
    result = result[-7:]
    result = [(tache[0].strftime("%d/%m"), tache[1]) for tache in result]

    return result


def camembert_donnees(id_utilisateur: int):
    colors = {
        "priorité 0": "#8785A7",
        "priorité 1": "#40B057",
        "priorité 2": "#6DD4F9",
        "priorité 3": "#FFB550",
        "priorité 4": "#FF8E47",
        "priorité 5": "#FF4744"
    }
    data = lire_en_bdd(nom_table_tache, "priorite", f"id_utilisateur = {id_utilisateur}")
    dico = {}

    if not data:
        return []

    maxi = len(data)

    for tache in data:
        if tache in dico:
            dico[tache] += 1
        else:
            dico[tache] = 1

    for cle in dico.keys():
        dico[cle] = (dico[cle] / maxi) * 100

    cles = sorted([cle for cle in dico.keys()])
    legende = ["priorité " + str(cle) for cle in cles]
    donnees = [dico[cle] for cle in cles]
    donnees = [(legende[i], donnees[i]) for i in range(len(donnees))]

    return donnees


def recup_apparence():
    """Charge tous les skins depuis la BDD.
    Schéma Apparence_disponible : (id_apparence, type, prix, nom, hauteur, largeur, lien_image, zoom)
    indices :                       [0]           [1]   [2]  [3]  [4]      [5]      [6]         [7]
    """
    apparences = lire_en_bdd(nom_table_apparence__dispo, "*", "1 + 1 = 2")
    result = []

    for apparence in apparences:
        dico = {}
        dico["id"]      = apparence[0]
        dico["type"]    = apparence[1]
        dico["prix"]    = apparence[2]
        dico["nom"]     = apparence[3]
        dico["hauteur"] = apparence[4]
        dico["largeur"] = apparence[5]
        dico["lien"]    = apparence[6]   # colonne lien_image dans ta BDD
        dico["zoom"]    = apparence[7]
        result.append(dico)

    return result
