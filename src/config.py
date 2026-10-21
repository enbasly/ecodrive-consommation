"""Paramètres communs : chemins, variables, hypothèses métier."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "trips.csv"
FIG = ROOT / "reports" / "figures"
RESULTS = ROOT / "reports" / "resultats.json"
RANDOM_STATE = 42
TARGET = "conso_l100"

# Variables connues à la fin du trajet SANS mesurer le carburant
NUM_FEATURES = ["duree_min", "distance_km", "vitesse_moy", "vitesse_max", "vitesse_std", "part_arret",
                "part_autoroute", "part_accel_forte", "part_freinage_fort", "accel_moy_pos", "rpm_moy",
                "temp_ext", "rpa", "arrets_par_km", "cylindree_l", "poids_kg"]
CAT_FEATURES = ["type_vehicule", "classe", "transmission_roues"]

# Audit de fuite
EXCLUES = {
    "MAF, Fuel Rate": "servent à CALCULER la cible : les garder = donner la réponse au modèle",
    "Absolute Load, Fuel Trims": "charge moteur et corrections d'injection ≈ débit de carburant",
    "veh_id, trip_id": "identifiants : le modèle apprendrait un véhicule par cœur",
    "jour": "sert uniquement au découpage chronologique train / test",
}

# Variables de style que le conducteur peut changer (scénario « et s'il conduisait calmement ? »)
STYLE_MODIFIABLE = ["rpa", "accel_moy_pos", "part_accel_forte", "part_freinage_fort", "rpm_moy"]

# HYPOTHÈSES métier (axes 6-7) : posées par l'équipe, à valider avec le client
HYP = {
    "flotte_vehicules": 100,
    "km_par_an": 20000,
    "prix_carburant": 1.80,          # €/L : hypothèse, à vérifier sur prix-carburants.gouv.fr avant le rendu
    "trajets_par_vehicule_an": 440,  # 2 trajets par jour ouvré
    "taille_bloc": 10,               # chaque lundi : les 10 derniers trajets du véhicule
    "anomalies_par_an": 12,          # défauts (pneus, filtre, sonde...) par an sur la flotte
    "cout_fausse_alerte": 15,        # € : 20 min du gestionnaire
    "cout_vraie_alerte": 90,         # € : diagnostic atelier
    "cout_anomalie_ratee": 400,      # € : surconsommation jusqu'à la révision + usure
    "abonnement_mois": 4,            # € / véhicule / mois
    "integration": 3000,             # € : boîtiers + paramétrage (année 1)
    "cout_coaching": 120,            # € / conducteur coaché
    "part_a_coacher": 0.25,          # on coache le quart des conducteurs au plus fort potentiel
    "turnover": 0.2,                 # part des conducteurs à re-former chaque année
    "capture_coaching": 0.5,         # part du potentiel rattrapée par un conducteur coaché
    "capture_appli": 0.2,            # part rattrapée grâce au score dans l'appli
}
