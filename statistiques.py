import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np            
import io
from base_de_donnees_fonction import * 
from fonctions import *
import matplotlib.dates as mdates


BG = "#284C65"
day = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

#----------------------------------------------------

def temps_total_travailles(id_utilisateur):
        heures = graphe_temps_total(id_utilisateur)
        jour_temp_total_travailles = jour_de_la_semaine(id_utilisateur)
        fig, ax = plt.subplots(facecolor = BG)  

        ax.bar(jour_temp_total_travailles, heures, color='#3DD968')
        ax.set_facecolor(BG)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_edgecolor("white")
        ax.spines["bottom"].set_edgecolor("white")
        ax.spines["bottom"].set_linewidth(3)
        ax.spines["left"].set_linewidth(3)
        # Taille et couleur des graduations
        ax.tick_params(axis='both',
                which='major',
                labelsize=14,      # taille des labels
                labelcolor='white', # couleur des labels
                colors='white',    # couleur des ticks
                width=2,           # épaisseur des ticks
                length=6)          # longueur des ticks


        buf2 = io.StringIO()
        plt.savefig(buf2, transparent = True, format = 'svg')
        svg_str = buf2.getvalue()

        return svg_str

# ------------------------------------------------

def graphe_poissons(id_utilisateur):

        poissons = [0, 23, 73, 237, 53, 84, 18]
        jour_poissons = jour_de_la_semaine(id_utilisateur)

        fig2, ax2 = plt.subplots(facecolor = BG)
        ax2.plot(jour_poissons, poissons,
                color = "#E82161",
                linewidth = 4,
                markerfacecolor = "#F02E6B",
                alpha = 0.8,
                marker = "o"
                )

        ax2.set_facecolor(BG)
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)
        ax2.spines["left"].set_edgecolor("white")
        ax2.spines["bottom"].set_edgecolor("white")
        ax2.spines["bottom"].set_linewidth(3)
        ax2.spines["left"].set_linewidth(3)
        # Taille et couleur des graduations
        ax2.tick_params(axis='both',
                which='major',
                labelsize=14,      # taille des labels
                labelcolor='white', # couleur des labels
                colors='white',    # couleur des ticks
                width=2,           # épaisseur des ticks
                length=6)          # longueur des ticks

        plt.fill_between(jour_poissons, poissons, alpha=0.3, color="#F02E6B")


        buf3 = io.StringIO()
        plt.savefig(buf3, transparent = True, format = "svg")
        svg_str2 = buf3.getvalue()

        return svg_str2

#-------------------------------------------

def graphe_session_pomodoro(id_utilisateur):
        data = graphe_nbr_session(id_utilisateur)

        jour_pomodoro = [session[0] for session in data]
        pomodoro = [session[1] for session in data]

        fig3, ax3 = plt.subplots(facecolor = BG)
        ax3.set_facecolor(BG)
        ax3.plot(jour_pomodoro, pomodoro,
                color = "#FF9500",
                linewidth = 4,
                markerfacecolor = "#CC7D0F",
                alpha = 0.8,
                marker = "o"
                )
        plt.fill_between(jour_pomodoro, pomodoro, alpha=0.5, color="#E6A040")

        ax3.spines["top"].set_visible(False)
        ax3.spines["right"].set_visible(False)
        ax3.spines["left"].set_edgecolor("white")
        ax3.spines["bottom"].set_edgecolor("white")
        ax3.spines["bottom"].set_linewidth(3)
        ax3.spines["left"].set_linewidth(3)

        # Taille et couleur des graduations
        ax3.tick_params(axis='both',
                which='major',
                labelsize= 12,      # taille des labels
                labelcolor='white', # couleur des labels
                colors='white',    # couleur des ticks
                width=2,           # épaisseur des ticks
                length=6)          # longueur des ticks

        buf4 = io.StringIO()
        plt.savefig(buf4, transparent = True, format = "svg")
        svg_str3 = buf4.getvalue()

        return svg_str3

#-------------------------------------------

tache = [0, 2, 5, 5, 9, 6, 8]

fig4, ax4 = plt.subplots(facecolor = BG)
ax4.set_facecolor(BG)
ax4.plot(day, tache,
        color = "#37A5FF",
        linewidth = 4,
        markerfacecolor = "#35ACFC",
        alpha = 0.8,
        marker = "o"
        )
plt.fill_between(day, tache, alpha=0.2, color="#37A5FF")

ax4.spines["top"].set_visible(False)
ax4.spines["right"].set_visible(False)
ax4.spines["left"].set_edgecolor("white")
ax4.spines["bottom"].set_edgecolor("white")
ax4.spines["bottom"].set_linewidth(3)
ax4.spines["left"].set_linewidth(3)
# Taille et couleur des graduations
ax4.tick_params(axis='both',
            which='major',
               labelsize=14,      # taille des labels
               labelcolor='white', # couleur des labels
               colors='white',    # couleur des ticks
               width=2,           # épaisseur des ticks
               length=6)          # longueur des ticks

buf5 = io.StringIO()
plt.savefig(buf5, transparent = True, format = "svg")
svg_str4 = buf5.getvalue()


