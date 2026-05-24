import datetime
from base_de_donnees_fonction import *


class Utilisateur():
    """Représente un utilisateur de l'application."""

    def __init__(self, nom_utilisateur=None, mot_de_passe=0000):
        self.id_utilisateur   = datetime.datetime.now().microsecond
        self.nom_utilisateur  = nom_utilisateur
        self.mot_de_passe     = mot_de_passe
        self.date_de_creation = datetime.datetime.now().isoformat()
        self.poisson_utilisateur = 0
        self.poissons_depense    = 0
        self.apparence_equipee = lire_en_bdd(nom_table_apparence__dispo, "*", "nom = 'skin_de_base'")
        self.nbr_tache   = 0
        self.nbr_session = 0

        if self.nom_utilisateur is None:
            self.nom_utilisateur = f'guest_{str(self.id_utilisateur)}'

    def recuperer_information(self):
        """Charge les données depuis la BDD. Schéma Utilisateurs : (id, nom_utilisateur, date_inscription, mot_de_passe)"""
        result = lire_en_bdd(
            nom_table_utilisateur, "id",
            f"nom_utilisateur = '{self.nom_utilisateur}' AND mot_de_passe = '{self.mot_de_passe}'"
        )

        if len(result) == 1:
            self.id_utilisateur = result[0]

            # Poissons — ordre BDD : (nbr_poissons_total, nbr_poisson, id_utilisateur, poissons_depense)
            self.poisson_utilisateur = lire_en_bdd(
                nom_table_poisson, "nbr_poisson", f"id_utilisateur = {self.id_utilisateur}"
            )[0]
            self.poissons_depense = lire_en_bdd(
                nom_table_poisson, "poissons_depense", f"id_utilisateur = {self.id_utilisateur}"
            )[0]

            self.date_de_creation = lire_en_bdd(
                nom_table_utilisateur, "date_inscription", f"id = {self.id_utilisateur}"
            )[0]

            self.apparence_equipee = lire_en_bdd(
                nom_table_apparence_equipe, "*", f"id_utilisateur = {self.id_utilisateur}"
            )

            self.nbr_tache = lire_en_bdd(
                nom_table_tache, "COUNT(*)", f"id_utilisateur = {self.id_utilisateur}"
            )[0]
            self.nbr_session = lire_en_bdd(
                nom_table_session, "COUNT(*)", f"id_utilisateur = {self.id_utilisateur}"
            )[0]
        else:
            return False

    def ajouter_poissons(self, nbr_poisson_ajouter: int):
        self.poisson_utilisateur += nbr_poisson_ajouter

    def depenser_poissons(self, nbr_poisson_depense):
        self.poisson_utilisateur -= nbr_poisson_depense
        self.poissons_depense += nbr_poisson_depense

    def equiper_apparence(self, apparence):
        self.apparence_equipee = apparence
        existe = lire_en_bdd(
            nom_table_apparence_equipe, 'id_utilisateur',
            f'id_utilisateur = {self.id_utilisateur}'
        )
        if existe:
            modifier_en_bdd(
                nom_table_apparence_equipe,
                f"prix={apparence.prix}, id_apparence='{apparence.id_apparence}', type='{apparence.type}'",
                f"id_utilisateur = {self.id_utilisateur}"
            )
        else:
            ajouter_en_bdd(
                nom_table_apparence_equipe,
                [(self.id_utilisateur, apparence.id_apparence, apparence.prix, apparence.type)]
            )

    def sauvegarde(self):
        """Sauvegarde l'utilisateur. Schéma Utilisateurs : (id, nom_utilisateur, date_inscription, mot_de_passe)
        — sans nbr_tache/nbr_session qui n'existent pas dans la BDD réelle."""
        verif_id = lire_en_bdd(
            nom_table_utilisateur, "id",
            f"nom_utilisateur = '{self.nom_utilisateur}' AND mot_de_passe = '{self.mot_de_passe}'"
        )

        if verif_id == []:
            # Utilisateurs : seulement 4 colonnes dans ta BDD
            ajouter_en_bdd(nom_table_utilisateur,
                           [(self.id_utilisateur, self.nom_utilisateur,
                             self.date_de_creation, self.mot_de_passe)])
            # Poissons — ordre BDD : (nbr_poissons_total, nbr_poisson, id_utilisateur, poissons_depense)
            ajouter_en_bdd(nom_table_poisson,
                           [(self.poisson_utilisateur, self.poisson_utilisateur,
                             self.id_utilisateur, self.poissons_depense)])
            return True
        else:
            return False


class Tache:
    """Représente une tâche. Schéma BDD : statut est INTEGER (0=A faire, 1=Fait)."""

    def __init__(self, titre_tache: str, description_tache: str,
                 date_fin: datetime.datetime, id_utilisateur: int, priorite: int):
        self.id_tache          = int(datetime.datetime.now().timestamp() * 1000) % 100000
        self.titre_tache       = titre_tache
        self.description_tache = description_tache
        self.date_creation     = datetime.datetime.now().isoformat()
        self.date_fin          = date_fin if date_fin else None
        self.id_utilisateur    = id_utilisateur
        self.priorite          = priorite
        self.statut            = 0  # 0 = A faire (INTEGER dans la BDD)


class ListeTache:
    """Gère la liste en mémoire des tâches."""

    def __init__(self):
        self.taches = []

    def ajouter_tache(self, tache: Tache):
        self.taches.append(tache)
        valeurs = [(tache.id_tache, tache.titre_tache,
                    tache.date_fin, tache.priorite, tache.statut,
                    tache.date_creation, tache.id_utilisateur, tache.description_tache)]
        ajouter_en_bdd("Tache", valeurs)

    def supprimer_tache(self, id_tache: int):
        self.taches = [t for t in self.taches if t.id_tache != id_tache]
        # statut = 1 (INTEGER) pour "Fait"
        modifier_en_bdd(nom_table_tache, "statut = 1", f"id = {id_tache}")

    def lister_taches(self):
        self.taches = [t for t in self.taches if t.statut != 1]
        return self.taches

    def sauvegarde(self, utilisateur: Utilisateur):
        if lire_en_bdd(nom_table_tache, "*", f"id = {self.id_tache}") is None:
            ajouter_en_bdd(nom_table_tache,
                           [(self.id_tache, self.titre_tache, self.date_fin,
                             self.priorite, self.statut, utilisateur.id_utilisateur, self.description)])
        else:
            modifier_en_bdd(nom_table_tache,
                            f"({self.id_tache}, {self.titre_tache}, {self.date_fin}, "
                            f"{self.priorite}, {self.statut}, {utilisateur.id_utilisateur}, {self.description})")


class Session():
    """Gestion d'une session Pomodoro."""

    PAUSE_COURTE          = 5 * 60
    PAUSE_LONGUE          = 15 * 60
    SESSIONS_AVANT_LONGUE = 4

    def __init__(self, duree_session: int):
        self.id_session      = datetime.datetime.now().microsecond
        self.duree_session   = duree_session
        self.temps_restant   = duree_session
        self.sessions_en_cours = False
        self.debut           = None
        self.phase               = "travail"
        self.compteur_sessions   = 0
        self.session_completee   = False

    def _duree_phase_actuelle(self):
        if self.phase == "travail":
            return self.duree_session
        elif self.phase == "pause_longue":
            return self.PAUSE_LONGUE
        else:
            return self.PAUSE_COURTE

    def _sync_temps_restant(self):
        if self.sessions_en_cours and self.debut:
            ecoule = (datetime.datetime.now() - self.debut).total_seconds()
            self.temps_restant = max(0, self._duree_phase_actuelle() - ecoule)

    def get_temps_restant(self):
        self._sync_temps_restant()
        return int(self.temps_restant)

    def demarrer_chronometre(self):
        if not self.sessions_en_cours:
            if self.temps_restant <= 0:
                self.temps_restant = self._duree_phase_actuelle()
            self.debut = datetime.datetime.now() - datetime.timedelta(
                seconds=self._duree_phase_actuelle() - self.temps_restant
            )
            self.sessions_en_cours = True
            self.session_completee = False

    def pause_chronometre(self):
        if self.sessions_en_cours:
            self._sync_temps_restant()
            self.sessions_en_cours = False
            self.debut = None

    def arret_chronometre(self):
        self.sessions_en_cours = False
        self.debut = None
        self.temps_restant = self.duree_session
        self.phase = "travail"
        self.session_completee = False

    def terminer_session_travail(self):
        if self.phase != "travail":
            self.phase = "travail"
            self.temps_restant = self.duree_session
            self.sessions_en_cours = False
            self.debut = None
            self.session_completee = False
            return False

        self.compteur_sessions += 1
        self.session_completee = True

        if self.compteur_sessions % self.SESSIONS_AVANT_LONGUE == 0:
            self.phase = "pause_longue"
            self.temps_restant = self.PAUSE_LONGUE
        else:
            self.phase = "pause_courte"
            self.temps_restant = self.PAUSE_COURTE

        self.sessions_en_cours = False
        self.debut = None
        return True

    def changer_duree_chronometre(self, nouvelle_duree_minutes: int):
        self.sessions_en_cours = False
        self.debut = None
        self.duree_session = int(nouvelle_duree_minutes) * 60
        self.temps_restant = self.duree_session
        self.phase = "travail"
        self.session_completee = False


class Apparence():
    """Représente un skin ou un thème visuel."""

    def __init__(self, nom_apparence: str, prix_apparence: int, lien_image: str,
                 hauteur: float, largeur: float, type: str, zoom: float):
        self.id_apparence  = datetime.datetime.now().microsecond
        self.nom_apparence = nom_apparence
        self.prix          = prix_apparence
        self.lien_image    = lien_image
        self.hauteur       = hauteur
        self.largeur       = largeur
        self.type          = type
        self.zoom          = zoom
