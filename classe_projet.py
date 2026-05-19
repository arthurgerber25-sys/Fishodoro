import datetime
from base_de_donnees_fonction import *


class Utilisateur():
    """Représente un utilisateur de l'application.

    À la création, l'objet est initialisé avec des valeurs par défaut.
    Les vraies données (id BDD, poissons, etc.) sont chargées ensuite
    via recuperer_information() lors de la connexion, ou sauvegardées
    via sauvegarde() lors de l'inscription.
    """

    def __init__(self, nom_utilisateur=None, mot_de_passe=0000):
        # Identifiant temporaire basé sur les microsecondes (remplacé par l'id BDD après connexion)
        self.id_utilisateur   = datetime.datetime.now().microsecond
        self.nom_utilisateur  = nom_utilisateur
        self.mot_de_passe     = mot_de_passe
        self.date_de_creation = datetime.datetime.now().isoformat()
        self.poisson_utilisateur = 0   # Solde de poissons disponibles
        self.poissons_depense    = 0   # Total de poissons dépensés en boutique
        # Récupère le skin de base depuis la BDD pour l'équiper par défaut
        self.apparence_equipee = lire_en_bdd(nom_table_apparence__dispo, "*", "nom = 'skin_de_base'")
        self.nbr_tache   = 0
        self.nbr_session = 0

        # Si aucun nom fourni, on génère un pseudo invité unique
        if self.nom_utilisateur is None:
            self.nom_utilisateur = f'guest_{str(self.id_utilisateur)}'

    def recuperer_information(self):
        """Charge les données de l'utilisateur depuis la BDD lors de la connexion.

        Vérifie que le couple (nom_utilisateur, mot_de_passe) existe dans la BDD,
        puis remplit tous les attributs de l'objet avec les données persistées.

        Returns:
            False si les identifiants ne correspondent à aucun compte.
            None (implicite) si la récupération a réussi.
        """
        result = lire_en_bdd(
            nom_table_utilisateur, "id",
            f"nom_utilisateur = '{self.nom_utilisateur}' AND mot_de_passe = '{self.mot_de_passe}'"
        )

        if len(result) == 1:
            # Mise à jour de l'id avec la vraie clé primaire BDD
            self.id_utilisateur = result[0]

            # Chargement du solde de poissons depuis la table Poissons
            self.poisson_utilisateur = lire_en_bdd(
                nom_table_poisson, "nbr_poisson", f"id_utilisateur = {self.id_utilisateur}"
            )[0]
            self.poissons_depense = lire_en_bdd(
                nom_table_poisson, "poissons_depense", f"id_utilisateur = {self.id_utilisateur}"
            )[0]

            # Chargement de la date d'inscription
            self.date_de_creation = lire_en_bdd(
                nom_table_utilisateur, "date_inscription", f"id = {self.id_utilisateur}"
            )[0]

            # Chargement de l'apparence actuellement équipée
            self.apparence_equipee = lire_en_bdd(
                nom_table_apparence_equipe, "*", f"id_utilisateur = {self.id_utilisateur}"
            )

            # Compteurs de tâches et sessions pour les statistiques
            self.nbr_tache = lire_en_bdd(
                nom_table_tache, "COUNT(*)", f"id_utilisateur = {self.id_utilisateur}"
            )[0]
            self.nbr_session = lire_en_bdd(
                nom_table_session, "COUNT(*)", f"id_utilisateur = {self.id_utilisateur}"
            )[0]
        else:
            return False  # Identifiants incorrects → connexion refusée

    def ajouter_poissons(self, nbr_poisson_ajouter: int):
        """Ajoute des poissons au solde de l'utilisateur (en mémoire uniquement).

        La persistance en BDD est gérée séparément via modifier_en_bdd.
        """
        self.poisson_utilisateur += nbr_poisson_ajouter

    def depenser_poissons(self, nbr_poisson_depense):
        """Déduit des poissons du solde et les comptabilise dans les dépenses."""
        self.poisson -= nbr_poisson_depense          # Note : attribut mal nommé (devrait être self.poisson_utilisateur)
        self.poisson_depense += nbr_poisson_depense  # Note : attribut mal nommé (devrait être self.poissons_depense)

    def equiper_apparence(self, apparence):
        """Équipe une apparence et la sauvegarde ou met à jour en BDD.

        Si l'utilisateur a déjà une apparence équipée, on fait un UPDATE.
        Sinon, on INSERT une nouvelle ligne dans Apparence_equipe.
        """
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
                [(apparence.prix, apparence.id_apparence, self.id_utilisateur, apparence.type)]
            )

    def sauvegarde(self):
        """Sauvegarde l'utilisateur en BDD lors de l'inscription.

        - Si le compte n'existe pas encore : INSERT de l'utilisateur, ses poissons
          et son apparence de base.
        - Si le compte existe déjà : UPDATE des compteurs et de l'apparence,
          et INSERT d'une nouvelle ligne Poissons (comportement à revoir si
          l'utilisateur a déjà une ligne Poissons).

        Returns:
            True  → nouvel utilisateur créé.
            False → utilisateur déjà existant, données mises à jour.
        """
        verif_id = lire_en_bdd(
            nom_table_utilisateur, "id",
            f"nom_utilisateur = '{self.nom_utilisateur}' AND mot_de_passe = '{self.mot_de_passe}'"
        )

        if verif_id == []:
            # Nouveau compte → insertion dans toutes les tables liées
            ajouter_en_bdd(nom_table_poisson,
                           [(self.poisson_utilisateur, self.poisson_utilisateur,
                             self.id_utilisateur, self.poissons_depense)])
            ajouter_en_bdd(nom_table_utilisateur,
                           [(self.id_utilisateur, self.nom_utilisateur, self.date_de_creation,
                             self.mot_de_passe, self.nbr_tache, self.nbr_session)])
            ajouter_en_bdd(nom_table_apparence_equipe,
                           [self.apparence_equipe[2], self.apparence_equipee[0],
                            self.id_utilisateur, self.apparence_equipee[1]])
            return True
        else:
            # Compte existant → mise à jour des compteurs et de l'apparence
            ajouter_en_bdd(nom_table_poisson,
                           [(self.poisson_utilisateur, self.poisson_utilisateur,
                             self.id_utilisateur, self.poissons_depense)])
            modifier_en_bdd(nom_table_utilisateur,
                            f"nbr_session = {self.nbr_session}, nbr_tache = {self.nbr_tache}",
                            f"id = {self.id_utilisateur}")
            modifier_en_bdd(nom_table_apparence_equipe,
                            f"prix = {self.apparence_equipee[2]}, id_apparence = {self.apparence_equipee[0]}, type = {self.apparence_equipee[1]}",
                            f"id = {self.id_utilisateur}")
            return False


class Tache:
    """Représente une tâche créée par un utilisateur.

    Une tâche a un titre, une description, une date de fin optionnelle,
    une priorité (0 = très haute … 5 = basse) et un statut ("A faire" / "Fait").
    """

    def __init__(self, titre_tache: str, description_tache: str,
                 date_fin: datetime.datetime, id_utilisateur: int, priorite: int):
        # ID unique basé sur le timestamp en millisecondes, tronqué à 5 chiffres
        self.id_tache          = int(datetime.datetime.now().timestamp() * 1000) % 100000
        self.titre_tache       = titre_tache
        self.description_tache = description_tache
        self.date_creation     = datetime.datetime.now().isoformat()
        self.date_fin          = date_fin if date_fin else None
        self.id_utilisateur    = id_utilisateur
        self.priorite          = priorite
        self.statut            = "A faire"  # Statut initial par défaut


class ListeTache:
    """Gère la liste en mémoire des tâches et leur synchronisation avec la BDD."""

    def __init__(self):
        self.taches = []  # Liste d'objets Tache

    def ajouter_tache(self, tache: Tache):
        """Ajoute une tâche en mémoire et la persiste en BDD."""
        self.taches.append(tache)
        valeurs = [(tache.id_tache, tache.titre_tache,
                    tache.date_fin, tache.priorite, tache.statut,
                    tache.date_creation, tache.id_utilisateur, tache.description_tache)]
        ajouter_en_bdd("Tache", valeurs)

    def supprimer_tache(self, id_tache: int):
        """Marque une tâche comme "Fait" en BDD et la retire de la liste mémoire."""
        self.taches = [t for t in self.taches if t.id_tache != id_tache]
        modifier_en_bdd(nom_table_tache, "statut = 'Fait'", f"id = {id_tache}")

    def lister_taches(self):
        """Retourne les tâches en filtrant celles déjà marquées 'Fait'."""
        for i in range(len(self.taches)):
            if self.taches[i].statut == "Fait":
                self.taches.pop(i)
        return self.taches

    def sauvegarde(self, utilisateur: Utilisateur):
        """Sauvegarde ou met à jour une tâche en BDD (méthode peu utilisée dans le flux actuel)."""
        if lire_en_bdd(nom_table_tache, "*", f"id = {self.id_tache}") is None:
            ajouter_en_bdd(nom_table_tache,
                           [(self.id_tache, self.titre_tache, self.date_fin,
                             self.priorite, self.statut, utilisateur.id_utilisateur, self.description)])
        else:
            modifier_en_bdd(nom_table_tache,
                            f"({self.id_tache}, {self.titre_tache}, {self.date_fin}, "
                            f"{self.priorite}, {self.statut}, {utilisateur.id_utilisateur}, {self.description})")


class Session():
    """Gestion d'une session Pomodoro avec alternance travail / pauses.

    Cycle Pomodoro :
        Travail (30 ou 55 min) → Pause courte (5 min) → ... (x4) → Pause longue (15 min)

    Phases possibles pour l'attribut `phase` :
        - "travail"      : session de travail active
        - "pause_courte" : pause de 5 minutes
        - "pause_longue" : pause de 15 minutes après 4 sessions de travail
    """

    PAUSE_COURTE          = 5 * 60   # 300 secondes
    PAUSE_LONGUE          = 15 * 60  # 900 secondes
    SESSIONS_AVANT_LONGUE = 4        # Nombre de sessions de travail avant une pause longue

    def __init__(self, duree_session: int):
        self.id_session      = datetime.datetime.now().microsecond

        self.duree_session   = duree_session   # Durée de travail en secondes (1800 ou 3300)
        self.temps_restant   = duree_session   # Temps restant sur la phase en cours
        self.sessions_en_cours = False         # True si le chronomètre tourne
        self.debut           = None            # datetime du dernier démarrage (pour calculer le temps écoulé)

        # État Pomodoro
        self.phase               = "travail"   # Phase courante
        self.compteur_sessions   = 0           # Nombre de sessions de travail complétées consécutivement
        self.session_completee   = False       # True si la dernière session s'est terminée naturellement

    # ── Méthodes privées ─────────────────────────────────────────────────────

    def _duree_phase_actuelle(self):
        """Retourne la durée en secondes de la phase en cours."""
        if self.phase == "travail":
            return self.duree_session
        elif self.phase == "pause_longue":
            return self.PAUSE_LONGUE
        else:
            return self.PAUSE_COURTE

    def _sync_temps_restant(self):
        """Recalcule le temps restant en fonction du temps réellement écoulé depuis self.debut.

        Utilisé pour avoir un temps exact même si le serveur n'a pas été interrogé
        à intervalles réguliers.
        """
        if self.sessions_en_cours and self.debut:
            ecoule = (datetime.datetime.now() - self.debut).total_seconds()
            self.temps_restant = max(0, self._duree_phase_actuelle() - ecoule)

    # ── API publique ─────────────────────────────────────────────────────────

    def get_temps_restant(self):
        """Retourne le temps restant à jour, en secondes (entier)."""
        self._sync_temps_restant()
        return int(self.temps_restant)

    def demarrer_chronometre(self):
        """Démarre ou reprend le chronomètre.

        Si le timer avait été mis en pause, il repart là où il s'était arrêté
        en recalculant self.debut pour que la synchronisation reste cohérente.
        """
        if not self.sessions_en_cours:
            if self.temps_restant <= 0:
                # Réinitialise si la phase précédente était déjà terminée
                self.temps_restant = self._duree_phase_actuelle()
            # On recule self.debut pour tenir compte du temps déjà écoulé
            self.debut = datetime.datetime.now() - datetime.timedelta(
                seconds=self._duree_phase_actuelle() - self.temps_restant
            )
            self.sessions_en_cours = True
            self.session_completee = False

    def pause_chronometre(self):
        """Met le chronomètre en pause en sauvegardant le temps restant."""
        if self.sessions_en_cours:
            self._sync_temps_restant()  # Sauvegarde du temps restant avant pause
            self.sessions_en_cours = False
            self.debut = None

    def arret_chronometre(self):
        """Arrête et réinitialise complètement le chronomètre (retour à l'état initial)."""
        self.sessions_en_cours = False
        self.debut = None
        self.temps_restant = self.duree_session
        self.phase = "travail"
        self.session_completee = False

    def terminer_session_travail(self):
        """Appelée quand le timer atteint 0. Gère la transition vers la prochaine phase.

        - Si on était en phase de travail : passe en pause (courte ou longue selon le compteur).
        - Si on était en pause : retourne en phase de travail.

        Returns:
            True  → c'était une session de travail → enregistrer en BDD et donner des poissons.
            False → c'était une pause → rien à enregistrer.
        """
        if self.phase != "travail":
            # Fin de pause → retour au travail
            self.phase = "travail"
            self.temps_restant = self.duree_session
            self.sessions_en_cours = False
            self.debut = None
            self.session_completee = False
            return False

        # Fin d'une session de travail
        self.compteur_sessions += 1
        self.session_completee = True

        # Toutes les 4 sessions → pause longue, sinon pause courte
        if self.compteur_sessions % self.SESSIONS_AVANT_LONGUE == 0:
            self.phase = "pause_longue"
            self.temps_restant = self.PAUSE_LONGUE
        else:
            self.phase = "pause_courte"
            self.temps_restant = self.PAUSE_COURTE

        self.sessions_en_cours = False
        self.debut = None
        return True  # Signal pour enregistrer la session en BDD

    def changer_duree_chronometre(self, nouvelle_duree_minutes: int):
        """Réinitialise le timer avec une nouvelle durée de travail.

        Args:
            nouvelle_duree_minutes : Nouvelle durée en minutes (ex: 30 ou 55).
        """
        self.sessions_en_cours = False
        self.debut = None
        self.duree_session = int(nouvelle_duree_minutes) * 60
        self.temps_restant = self.duree_session
        self.phase = "travail"
        self.session_completee = False


class Apparence():
    """Représente un skin ou un thème visuel disponible dans la boutique."""

    def __init__(self, nom_apparence: str, prix_apparence: int, lien_image: str,
                 hauteur: float, largeur: float, type: str, zoom: float):
        self.id_apparence  = datetime.datetime.now().microsecond  # ID temporaire
        self.nom_apparence = nom_apparence
        self.prix          = prix_apparence
        self.lien_image    = lien_image   # Chemin vers le sprite (image)
        self.hauteur       = hauteur      # Hauteur d'affichage en pixels
        self.largeur       = largeur      # Largeur d'affichage en pixels
        self.type          = type         # "skin" ou "theme"
        self.zoom          = zoom         # Facteur de zoom CSS appliqué au sprite
