# %% [markdown]
# # EcoDrive — 01 · Cadrage et analyse des données
# **Équipe :** Enzo BASLY, Guillaume, Rayan
#
# **Décision à éclairer :** chaque lundi, le gestionnaire de flotte décide (1) quels véhicules envoyer en contrôle
# parce qu'ils consomment anormalement et (2) quels conducteurs inscrire à une formation éco-conduite.
#
# **Problématique (régression supervisée) :** prédire la consommation « normale » d'un trajet (L/100 km) à partir
# du trajet, des conditions et du véhicule. On s'en sert ensuite pour (1) alerter quand la conso réelle dépasse
# nettement la prévision et (2) comparer les styles de conduite.

# %%
import sys
sys.path.append("../src")
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from config import DATA, FIG, TARGET, NUM_FEATURES, EXCLUES
from modeles import sauver

plt.rcParams.update({"figure.dpi": 110, "axes.grid": True, "grid.alpha": .3})
FIG.mkdir(parents=True, exist_ok=True)
df = pd.read_csv(DATA)
print(df.shape)
df.head()

# %% [markdown]
# ## 1. Description
# Source : Vehicle Energy Dataset (VED), Oh, LeBlanc & Peng (2020), https://github.com/gsoh/VED, licence Apache 2.0.
# Les mesures capteurs ont été agrégées par trajet (`src/prepare_trips.py`) : **1 ligne = 1 trajet**.

# %%
pd.DataFrame({
    "variable": ["duree_min", "distance_km", "vitesse_moy / max / std", "part_arret", "part_autoroute",
                 "part_accel_forte / part_freinage_fort", "accel_moy_pos", "rpm_moy", "temp_ext", "rpa",
                 "arrets_par_km", "cylindree_l, poids_kg, type_vehicule, classe", "conso_l100"],
    "unité": ["min", "km", "km/h", "%", "%", "%", "m/s²", "tr/min", "°C", "m/s²", "1/km", "L, kg, -", "L/100 km"],
    "signification": ["durée", "distance", "vitesse", "temps < 3 km/h", "temps > 90 km/h",
                      "temps en accél. > 1,5 m/s² / freinage < -2 m/s²", "accélération moyenne quand on accélère",
                      "régime moteur moyen", "température extérieure", "énergie d'accélération par mètre (construite)",
                      "redémarrages par km (construite)", "véhicule", "CIBLE"]})

# %% [markdown]
# ## 2. Qualité

# %%
print("doublons :", df.duplicated(["veh_id", "trip_id"]).sum())
q = df.isna().mean().mul(100).round(1)
q[q > 0]

# %% [markdown]
# **Constat :** seule `temp_ext` a des manquants (capteur absent). **Décision :** imputation par la médiane dans le
# pipeline (ajustée sur le train uniquement). Les trajets < 1 km, < 2 min, sans signal carburant fiable ou avec une
# conso impossible ont été retirés dans `prepare_trips.py`.

# %%
sauver("donnees", {"n_trajets": len(df), "n_vehicules": int(df.veh_id.nunique()), "n_colonnes": df.shape[1],
                   "pct_temp_manquante": float(df.temp_ext.isna().mean() * 100),
                   "n_ice": int((df.type_vehicule == "ICE").sum()), "n_hev": int((df.type_vehicule == "HEV").sum()),
                   "conso_moy": float(df[TARGET].mean())})

# %% [markdown]
# ## 3. La cible

# %%
fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
sns.histplot(df, x=TARGET, hue="type_vehicule", bins=50, ax=ax[0])
ax[0].set(title="Distribution de la consommation par trajet", xlabel="L/100 km", ylabel="nb trajets")
sns.boxplot(df, x="classe", y=TARGET, hue="type_vehicule", ax=ax[1])
ax[1].set(title="Consommation selon le véhicule", xlabel="", ylabel="L/100 km")
plt.tight_layout(); plt.savefig(FIG / "01_cible.png", bbox_inches="tight"); plt.show()

# %% [markdown]
# **Lecture :** deux populations (hybrides / thermiques) et une queue à droite. Variable continue, connue sur tout
# l'historique → **régression**. Le type de véhicule doit être une variable explicative.

# %% [markdown]
# ## 4. Relations avec la cible

# %%
corr = df[NUM_FEATURES + [TARGET]].corr()[TARGET].drop(TARGET).sort_values()
fig, ax = plt.subplots(figsize=(7, 5))
corr.plot.barh(ax=ax, color=np.where(corr > 0, "#d9534f", "#2a9d8f"))
ax.set(title="Corrélation avec la consommation", xlabel="corrélation de Pearson")
plt.tight_layout(); plt.savefig(FIG / "01_correlations.png", bbox_inches="tight"); plt.show()

# %% [markdown]
# **Lecture :** le véhicule (cylindrée, poids) domine, puis le régime moteur et les accélérations fortes.

# %%
ice = df[df.type_vehicule == "ICE"]
fig, ax = plt.subplots(1, 3, figsize=(14, 3.8))
sns.scatterplot(ice, x="vitesse_moy", y=TARGET, hue="cylindree_l", s=10, ax=ax[0], palette="viridis")
ax[0].legend(title="cylindrée (L)", fontsize=7, title_fontsize=7, loc="upper right")
ax[0].set(title="Vitesse moyenne (thermiques)", xlabel="km/h", ylabel="L/100 km")
sns.scatterplot(ice, x="temp_ext", y=TARGET, s=10, alpha=.4, ax=ax[1])
ax[1].set(title="Température extérieure", xlabel="°C", ylabel="L/100 km")
sns.scatterplot(ice, x="rpm_moy", y=TARGET, s=10, alpha=.4, ax=ax[2])
ax[2].set(title="Régime moteur moyen", xlabel="tr/min", ylabel="L/100 km")
plt.tight_layout(); plt.savefig(FIG / "01_relations.png", bbox_inches="tight"); plt.show()

# %% [markdown]
# **Lecture :** effet non linéaire de la vitesse (ville et autoroute coûtent plus que le mixte), effet du froid et du
# régime : un modèle à arbres devrait faire mieux qu'un modèle linéaire.
#
# ## 5. Audit de fuite

# %%
pd.DataFrame({"variable écartée": list(EXCLUES), "raison": list(EXCLUES.values())})

# %% [markdown]
# ## 6. Variables construites
# - **rpa** = Σ(v·a⁺)·dt / distance : énergie dépensée à accélérer par mètre (indicateur classique d'éco-conduite).
# - **arrets_par_km** : chaque redémarrage relance 1,5 t de voiture.
#
# **Conséquences :** split **chronologique**, pipeline scikit-learn, MAE en L/100 km comme métrique principale.
