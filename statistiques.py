import matplotlib
matplotlib.use('Agg')  # Moteur de rendu sans interface graphique (génération en mémoire)
import matplotlib.pyplot as plt
import io
from base_de_donnees_fonction import *
from fonctions import *
from matplotlib.patches import Patch
import matplotlib.ticker as ticker
import matplotlib.dates as mdates


# Couleur de fond utilisée pour tous les graphes (correspond au bleu-ardoise du thème)
BG = "#284C65"


# ══════════════════════════════════════════════════════════════════
#   GRAPHE 1 — Temps total travaillé (barres)
# ══════════════════════════════════════════════════════════════════

def format_heures(heures, pos):
    """Formateur personnalisé pour l'axe Y du graphe des heures travaillées.

    Convertit un flottant (heures décimales) en chaîne lisible :
        0.5  → "30min"
        1.0  → "1h"
        1.5  → "1h30"

    Args:
        heures : Valeur en heures (float), fournie automatiquement par matplotlib.
        pos    : Position du tick sur l'axe (inutilisé ici, requis par l'API matplotlib).
    """
    if heures < 1:
        return f"{int(heures * 60)}min"    # Moins d'une heure → affiche les minutes
    elif int(heures) == heures:
        return f"{int(heures)}h"           # Heure entière → "2h"
    else:
        h = int(heures)
        m = int((heures - h) * 60)
        return f"{h}h{m}"                  # Heure + minutes → "1h30"


def temps_total_travailles(id_utilisateur: int):
    """Génère un graphe en barres du temps travaillé sur les 7 derniers jours.

    Chaque barre représente le total d'heures de sessions Pomodoro pour un jour donné.
    Le graphe est rendu en SVG (chaîne de caractères) pour être injecté directement
    dans le HTML sans fichier temporaire.

    Returns:
        Chaîne SVG complète du graphe.
    """
    heures = graphe_temps_total(id_utilisateur)          # Liste de 7 flottants (heures par jour)
    jour_temp_total_travailles = jour_de_la_semaine()    # Liste de 7 noms de jours

    fig, ax = plt.subplots(facecolor=BG)

    ax.bar(jour_temp_total_travailles, heures, color='#3DD968')  # Barres vertes
    ax.set_facecolor(BG)

    # Graduations de l'axe Y toutes les 30 minutes (0.5 heure)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.5))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(format_heures))

    # Suppression des bordures superflues (top et droite) pour un look épuré
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_edgecolor("white")
    ax.spines["bottom"].set_edgecolor("white")
    ax.spines["bottom"].set_linewidth(3)
    ax.spines["left"].set_linewidth(3)

    # Style des graduations (labels blancs, ticks épais)
    ax.tick_params(axis='both', which='major',
                   labelsize=12, labelcolor='white',
                   colors='white', width=2, length=6)

    # Sauvegarde en mémoire au format SVG (transparent=True pour fond transparent)
    buf2 = io.StringIO()
    plt.savefig(buf2, transparent=True, format='svg')
    svg_str = buf2.getvalue()
    plt.close()  # Libère la figure matplotlib pour éviter les fuites mémoire
    buf2.close()

    return svg_str


# ══════════════════════════════════════════════════════════════════
#   GRAPHE 2 — Camembert des priorités de tâches
# ══════════════════════════════════════════════════════════════════

def camembert_tache(id_utilisateur: int):
    """Génère un camembert montrant la répartition des tâches par niveau de priorité.

    Chaque tranche correspond à un niveau de priorité (0 à 5), avec une couleur
    distincte et un pourcentage affiché. Une légende externe liste toutes les priorités.

    Returns:
        Chaîne SVG complète du graphe (avec fond coloré, pas transparent).
    """
    # Palette de couleurs fixe pour chaque niveau de priorité
    colors = {
        "priorité 0": "#8785A7",
        "priorité 1": "#40B057",
        "priorité 2": "#6DD4F9",
        "priorité 3": "#FFB550",
        "priorité 4": "#FF8E47",
        "priorité 5": "#FF4744"
    }
    donnees = camembert_donnees(id_utilisateur)  # [(label, pourcentage), ...]

    # On filtre les couleurs pour ne garder que celles des priorités présentes
    couleurs_filtre = [colors[donnee[0]] for donnee in donnees]

    fig, ax = plt.subplots(facecolor=BG, subplot_kw=dict(aspect="equal"))

    wedges, texts, autotexts = ax.pie(
        [donnee[1] for donnee in donnees],
        colors=couleurs_filtre,
        autopct='%1.1f%%',               # Affiche les pourcentages avec 1 décimale
        textprops=dict(color="#FFEEB9"),  # Couleur du texte des pourcentages
        radius=1.2                        # Rayon légèrement agrandi
    )

    # Décale le camembert vers la gauche pour laisser de la place à la légende
    ax.set_position([0.05, 0.05, 0.7, 0.9])
    ax.set_facecolor(BG)

    # Légende externe avec toutes les priorités (même celles absentes dans les données)
    legende = [Patch(facecolor=colors[cle], label=cle) for cle in colors.keys()]
    leg = ax.legend(
        handles=legende,
        loc='center left',
        bbox_to_anchor=(1, 0.5),   # Positionné à droite du camembert
        title='Priorités',
        labelcolor="#FFEEB9",
        facecolor=BG,
        framealpha=0.8,
        fontsize=9,
        fancybox=True
    )
    leg.get_title().set_color("#FFEEB9")
    leg.get_title().set_fontsize(10)
    plt.setp(autotexts, size=9, weight='bold')

    buf3 = io.StringIO()
    plt.savefig(buf3, format="svg")  # Pas de fond transparent ici (fond BG visible)
    svg_str2 = buf3.getvalue()
    plt.close()
    buf3.close()

    return svg_str2


# ══════════════════════════════════════════════════════════════════
#   GRAPHE 3 — Évolution cumulée des sessions Pomodoro (courbe)
# ══════════════════════════════════════════════════════════════════

def graphe_session_pomodoro(id_utilisateur: int):
    """Génère une courbe de l'évolution cumulée du nombre de sessions Pomodoro.

    Le pas de l'axe Y s'adapte automatiquement selon le volume de sessions :
        ≤ 10 : pas de 1 | ≤ 20 : pas de 2 | ≤ 50 : pas de 5 | > 50 : pas de 10

    Returns:
        Chaîne SVG complète du graphe (fond transparent).
    """
    data = graphe_nbr_session(id_utilisateur)  # [(date_str, total_cumulé), ...]

    jour_pomodoro = [session[0] for session in data]  # Axe X : dates formatées
    pomodoro      = [session[1] for session in data]  # Axe Y : cumul de sessions

    fig3, ax3 = plt.subplots(facecolor=BG)
    ax3.set_facecolor(BG)

    # Ajustement dynamique du pas de l'axe Y selon le volume de données
    if max_tache_compteur(id_utilisateur) <= 10:
        ax3.yaxis.set_major_locator(ticker.MultipleLocator(1))
    elif 10 < max_tache_compteur(id_utilisateur) <= 20:
        ax3.yaxis.set_major_locator(ticker.MultipleLocator(2))
    elif 20 < max_tache_compteur(id_utilisateur) <= 50:
        ax3.yaxis.set_major_locator(ticker.MultipleLocator(5))
    else:
        ax3.yaxis.set_major_locator(ticker.MultipleLocator(10))

    # Tracé de la courbe avec marqueurs ronds et remplissage sous la courbe
    ax3.plot(jour_pomodoro, pomodoro,
             color="#FF9500", linewidth=4,
             markerfacecolor="#CC7D0F", alpha=0.8, marker="o")
    plt.fill_between(jour_pomodoro, pomodoro, alpha=0.5, color="#E6A040")

    ax3.spines["top"].set_visible(False)
    ax3.spines["right"].set_visible(False)
    ax3.spines["left"].set_edgecolor("white")
    ax3.spines["bottom"].set_edgecolor("white")
    ax3.spines["bottom"].set_linewidth(3)
    ax3.spines["left"].set_linewidth(3)

    ax3.tick_params(axis='both', which='major',
                    labelsize=12, labelcolor='white',
                    colors='white', width=2, length=6)

    buf4 = io.StringIO()
    plt.savefig(buf4, transparent=True, format="svg")
    svg_str3 = buf4.getvalue()
    plt.close()
    buf4.close()

    return svg_str3


# ══════════════════════════════════════════════════════════════════
#   GRAPHE 4 — Évolution cumulée des tâches créées (courbe)
# ══════════════════════════════════════════════════════════════════

def graphe_tache(id_utilisateur: int):
    """Génère une courbe de l'évolution cumulée du nombre de tâches créées.

    Similaire à graphe_session_pomodoro mais pour les tâches, avec une couleur
    bleue pour différencier visuellement les deux graphes.

    Le pas de l'axe Y s'adapte automatiquement selon le volume de tâches :
        ≤ 10 : pas de 1 | ≤ 20 : pas de 2 | ≤ 50 : pas de 5 | > 50 : pas de 10

    Returns:
        Chaîne SVG complète du graphe (fond transparent).
    """
    data  = graphe_tache_liste(id_utilisateur)  # [(date_str, total_cumulé), ...]
    tache = [tache[1] for tache in data]        # Axe Y : cumul de tâches
    jour  = [tache[0] for tache in data]        # Axe X : dates formatées

    fig4, ax4 = plt.subplots(facecolor=BG)

    # Ajustement dynamique du pas de l'axe Y
    if max_tache_compteur(id_utilisateur) <= 10:
        ax4.yaxis.set_major_locator(ticker.MultipleLocator(1))
    elif 10 < max_tache_compteur(id_utilisateur) <= 20:
        ax4.yaxis.set_major_locator(ticker.MultipleLocator(2))
    elif 20 < max_tache_compteur(id_utilisateur) <= 50:
        ax4.yaxis.set_major_locator(ticker.MultipleLocator(5))
    else:
        ax4.yaxis.set_major_locator(ticker.MultipleLocator(10))

    ax4.set_facecolor(BG)

    # Courbe bleue avec remplissage semi-transparent sous la courbe
    ax4.plot(jour, tache,
             color="#37A5FF", linewidth=4,
             markerfacecolor="#35ACFC", alpha=0.8, marker="o")
    plt.fill_between(jour, tache, alpha=0.2, color="#37A5FF")

    ax4.spines["top"].set_visible(False)
    ax4.spines["right"].set_visible(False)
    ax4.spines["left"].set_edgecolor("white")
    ax4.spines["bottom"].set_edgecolor("white")
    ax4.spines["bottom"].set_linewidth(3)
    ax4.spines["left"].set_linewidth(3)

    ax4.tick_params(axis='both', which='major',
                    labelsize=14, labelcolor='white',
                    colors='white', width=2, length=6)

    buf5 = io.StringIO()
    plt.savefig(buf5, transparent=True, format="svg")
    svg_str4 = buf5.getvalue()
    plt.close()
    buf5.close()

    return svg_str4
