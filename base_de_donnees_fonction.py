from sqlite3 import *

# Nom du fichier de la base de données SQLite.
# Modifier cette variable si tu changes de base de données.
base_de_donnee = "bdd_projet_test.db"

# ── Noms des tables de la BDD ─────────────────────────────────────────────────
# Centralisés ici pour éviter les fautes de frappe dans le reste du code.
nom_table_tache               = "Tache"
nom_table_utilisateur         = "Utilisateurs"
nom_table_session             = "Session"
nom_table_apparence_deblock   = "Apparence_debloque"
nom_table_apparence__dispo    = "Apparence_disponible"
nom_table_apparence_equipe    = "Apparence_equipe"
nom_table_poisson             = "Poissons"


def ajouter_en_bdd(table: str, values: list):
    """Insère une ou plusieurs lignes dans la table indiquée.

    Args:
        table  : Nom de la table cible (str).
        values : Liste de tuples, chaque tuple représentant une ligne à insérer.

    Note:
        Le nombre de '?' dans le INSERT doit correspondre exactement au nombre
        de colonnes de la table. Chaque table a son propre schéma, géré par le
        bloc if/elif ci-dessous.
    """
    co = connect(base_de_donnee)
    curseur = co.cursor()

    # On sélectionne le bon nombre de placeholders selon la table cible.
    if table == "Utilisateurs":
        curseur.executemany(f"INSERT INTO {table} VALUES(?,?,?,?,?,?)", values)
    elif table == "Session":
        curseur.executemany(f"INSERT INTO {table} VALUES(?,?,?,?,?)", values)
    elif table == "Tache":
        curseur.executemany(f"INSERT INTO {table} VALUES(?,?,?,?,?,?,?,?)", values)
    elif table == "Apparence_disponible":
        curseur.executemany(f"INSERT INTO {table} VALUES(?,?,?,?,?,?,?,?)", values)
    elif table == "Poissons" or table == "Apparence_equipe":
        curseur.executemany(f"INSERT INTO {table} VALUES(?,?,?,?)", values)
    else:
        # Tables à 2 colonnes : Apparence_debloque, etc.
        curseur.executemany(f"INSERT INTO {table} VALUES(?,?)", values)

    co.commit()
    co.close()


def modifier_en_bdd(table: str, ajout: str, condition=None,
                    table_lie=None, condition_lie=None,
                    name_join_principal=None, name_join_second=None):
    """Met à jour des lignes d'une table, avec ou sans sous-requête de jointure.

    Cas simple (sans jointure) :
        UPDATE table SET ajout WHERE condition

    Cas avec jointure (sous-requête) :
        UPDATE table
        SET ajout
        WHERE name_join_principal IN (
            SELECT name_join_second FROM table_lie WHERE condition_lie
        )

    Args:
        table                : Nom de la table à mettre à jour.
        ajout                : Clause SET sous forme de chaîne (ex: "score = 10").
        condition            : Clause WHERE pour le UPDATE simple (ou la sous-requête).
        table_lie            : Table liée utilisée dans la sous-requête (jointure).
        condition_lie        : Condition de la sous-requête SELECT.
        name_join_principal  : Colonne de la table principale servant de clé de jointure.
        name_join_second     : Colonne de la table liée servant de clé de jointure.
    """
    co = connect(base_de_donnee)
    curseur = co.cursor()

    if table_lie is None:
        # Mise à jour simple, sans jointure
        requete = f"UPDATE {table} SET {ajout}"
        if condition:
            requete += f" WHERE {condition}"
        curseur.execute(requete)
    else:
        # Mise à jour avec sous-requête (simule un JOIN sur UPDATE)
        curseur.execute(f"""UPDATE {table}
                            SET {ajout}
                            WHERE {name_join_principal}
                            IN (SELECT {name_join_second}
                                FROM {table_lie}
                                WHERE {condition_lie})
                        """)

    co.commit()
    co.close()


def supprimer_en_bdd(table: str, condition: str,
                     table_lie=None, condition_lie=None,
                     name_join_principal=None, name_join_second=None):
    """Supprime des lignes d'une table, avec ou sans sous-requête de jointure.

    Cas simple :
        DELETE FROM table WHERE condition

    Cas avec jointure :
        DELETE FROM table
        WHERE name_join_principal IN (
            SELECT name_join_second FROM table_lie WHERE condition_lie
        )

    Args:
        table                : Nom de la table où supprimer.
        condition            : Condition WHERE pour la suppression ou la sous-requête.
        table_lie            : Table liée utilisée dans la sous-requête (optionnel).
        condition_lie        : Condition de la sous-requête SELECT (optionnel).
        name_join_principal  : Colonne clé dans la table principale (optionnel).
        name_join_second     : Colonne clé dans la table liée (optionnel).

    Exemple :
        >>> supprimer_en_bdd("Utilisateurs", "id", "Poissons",
        ...                  "nbr_poissons_total = 33", "id_utilisateur")
        # Équivaut à :
        # DELETE FROM Utilisateurs
        # WHERE id IN (SELECT id_utilisateur FROM Poissons WHERE nbr_poissons_total = 33)
    """
    co = connect(base_de_donnee)
    curseur = co.cursor()

    if table_lie is None:
        curseur.execute(f"""DELETE
                            FROM {table}
                            WHERE {condition}
                        """)
    else:
        # Suppression via sous-requête pour simuler un DELETE avec JOIN
        curseur.execute(f"""DELETE
                            FROM {table}
                            WHERE {name_join_principal}
                            IN (SELECT {name_join_second}
                                FROM {table_lie}
                                WHERE {condition_lie})
                        """)

    co.commit()
    co.close()


def lire_en_bdd(table: str, selection: str, condition: str,
                lien=None, table_lie=None):
    """Lit des données depuis la BDD avec une requête SELECT simple ou avec JOIN.

    Cas simple :
        SELECT selection FROM table WHERE condition

    Cas avec jointure :
        SELECT selection FROM table JOIN table_lie ON lien WHERE condition

    Args:
        table     : Table principale de la requête.
        selection : Colonnes à sélectionner (ex: "*", "id, nom").
        condition : Clause WHERE (ex: "id = 5").
        lien      : Condition ON du JOIN (ex: "Table.col = AutreTable.col").
        table_lie : Nom de la table à joindre.

    Returns:
        - Si chaque ligne ne contient qu'une seule colonne : liste de valeurs brutes.
        - Sinon : liste de tuples (résultats bruts de fetchall).
    """
    co = connect(base_de_donnee)
    curseur = co.cursor()

    if lien is None:
        curseur.execute(f"""SELECT {selection}
                            FROM {table}
                            WHERE {condition}
                        """)
    else:
        curseur.execute(f"""SELECT {selection}
                            FROM {table}
                            JOIN {table_lie}
                            ON {lien}
                            WHERE {condition}
                        """)

    resultats = curseur.fetchall()
    co.close()

    # Si la sélection ne porte que sur une colonne, on "aplatit" les tuples
    # pour renvoyer une liste simple (ex: [1, 2, 3] au lieu de [(1,), (2,), (3,)])
    if resultats and len(resultats[0]) == 1:
        return [row[0] for row in resultats]

    return resultats
