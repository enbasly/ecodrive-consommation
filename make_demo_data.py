"""
Génère un jeu de données de DÉMONSTRATION au même format que le Vehicle Energy Dataset (VED).
Sert uniquement à tester la chaîne complète sans télécharger le vrai VED.
Les résultats du rapport final doivent être produits sur le VRAI dataset (data/download_ved.py).

Usage : python data/make_demo_data.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
RAW = Path(__file__).resolve().parent / "raw"
RAW.mkdir(parents=True, exist_ok=True)
N_ICE, N_HEV, DT = 70, 15, 3.0

moteurs = [("I4 GAS 1.6L", 2500, "Car"), ("I4 GAS 2.0L", 3000, "Car"), ("I4 GAS 2.5L", 3500, "SUV"),
           ("V6 GAS 3.5L", 4000, "SUV"), ("V8 GAS 5.3L", 5000, "Pickup Truck")]
rows = []
for i in range(N_ICE + N_HEV):
    hev = i >= N_ICE
    m = moteurs[RNG.choice(5, p=[.22, .30, .22, .16, .10])] if not hev else moteurs[RNG.choice(3)]
    rows.append({"VehId": i + 1, "Vehicle Type": "HEV" if hev else "ICE", "Vehicle Class": m[2],
                 "Engine Configuration & Displacement": m[0].replace("GAS", "HEV") if hev else m[0],
                 "Transmission": RNG.choice(["5-SPEED AT", "6-SPEED AT", "CVT"]),
                 "Drive Wheels": RNG.choice(["FWD", "AWD", "4WD"], p=[.6, .25, .15]), "Generalized_Weight": m[1]})
static = pd.DataFrame(rows)
static.to_csv(RAW / "VED_Static_Data_ICE&HEV.csv", index=False)

style = RNG.choice([0.7, 1.0, 1.45], size=len(static), p=[.30, .45, .25]) * RNG.normal(1, .08, len(static))


def profil_vitesse(tt, duree, ag):
    n = int(duree / DT); v = np.zeros(n)
    cible = {"urbain": 45, "mixte": 70, "autoroute": 110}[tt]
    target = cible * RNG.uniform(.8, 1.1) * (1 + .08 * (ag - 1))
    for k in range(1, n):
        if RNG.random() < {"urbain": .05, "mixte": .02, "autoroute": .003}[tt]:
            target = 0
        elif target == 0 and RNG.random() < .25:
            target = cible * RNG.uniform(.7, 1.15)
        dv = np.clip(target - v[k - 1], -1.8 * ag * 3.6 * DT, 1.2 * ag * 3.6 * DT) * RNG.uniform(.6, 1)
        v[k] = max(0, v[k - 1] + dv + RNG.normal(0, 1))
    v[-1] = 0
    return v


def conso(v_kmh, masse, cyl, hev, ag, oat):
    v = v_kmh / 3.6; a = np.gradient(v, DT)
    p = masse * np.clip(a, 0, None) * v + 0.45 * v ** 3 + 0.012 * masse * 9.81 * v
    lh = p * 3600 / ((0.36 if hev else 0.27 - 0.01 * (cyl - 2)) * 32e6)
    if hev:
        lh *= np.where(v < 3.3, 0.2, 1.0)
    lh += 0 if hev else 0.35 * cyl
    t = np.arange(len(v)) * DT
    froid = 1 + np.where((oat < 5) & (t < 400), 0.35, 0)
    return lh * froid * (1 + 0.25 * (ag - 1)) * RNG.normal(1, .04, len(v)).clip(.85, 1.15)


frames, trip = [], 0
for _, veh in static.iterrows():
    i = veh.VehId - 1; hev = veh["Vehicle Type"] == "HEV"
    cyl = float(veh["Engine Configuration & Displacement"].split()[-1].rstrip("L"))
    masse = veh.Generalized_Weight * 0.4536 + 80
    sans_fuel_rate = RNG.random() < .7          # dans VED, Fuel Rate est souvent absent -> on passe par le MAF
    for d in np.sort(RNG.integers(1, 365, RNG.integers(20, 32))):
        trip += 1
        tt = RNG.choice(["urbain", "mixte", "autoroute"], p=[.45, .35, .20])
        duree = {"urbain": RNG.uniform(240, 1200), "mixte": RNG.uniform(400, 1500), "autoroute": RNG.uniform(600, 2000)}[tt]
        oat = 10 - 14 * np.cos(2 * np.pi * (d - 15) / 365) + RNG.normal(0, 3)
        v = profil_vitesse(tt, duree, style[i])
        fuel = conso(v, masse, cyl, hev, style[i], oat) * RNG.lognormal(0, .08)
        n = len(v)
        t_ms = np.cumsum(RNG.uniform(.6, 1.4, n) * DT * 1000); t_ms -= t_ms[0]
        h = RNG.choice([7.5, 8.5, 12.5, 17.5, 18.5]) + RNG.normal(0, .5)
        rpm = (700 + v * (28 + 4 * (style[i] - 1)) * RNG.normal(1, .05, n)).clip(650, 6000)
        df = pd.DataFrame({"DayNum": d + h / 24 + t_ms / 864e5, "VehId": veh.VehId, "Trip": trip,
                           "Timestamp(ms)": t_ms.round(), "Vehicle Speed[km/h]": v.round(1),
                           "MAF[g/sec]": (fuel * 745 / 3600 * 14.7).round(2),
                           "Engine RPM[RPM]": rpm.round(), "Absolute Load[%]": (20 + fuel * 4).clip(0, 100).round(1),
                           "OAT[DegC]": round(oat) if RNG.random() > .03 else np.nan,
                           "Fuel Rate[L/hr]": np.nan if sans_fuel_rate else fuel.round(3)})
        df.loc[RNG.random(n) < .01, "Vehicle Speed[km/h]"] = np.nan     # capteur qui décroche
        frames.append(df)
dyn = pd.concat(frames, ignore_index=True)
for k, part in enumerate(np.array_split(np.arange(len(dyn)), 2)):
    dyn.iloc[part].to_csv(RAW / f"VED_demo_part{k + 1}.csv", index=False)
print(f"Démo : {dyn.Trip.nunique()} trajets, {len(dyn):,} mesures, {len(static)} véhicules")
