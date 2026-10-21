"""
Transforme les mesures capteurs (1 ligne = 1 mesure OBD) en table « 1 ligne = 1 trajet ».
Entrée : data/raw/   Sortie : data/processed/trips.csv
Usage : python src/prepare_trips.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"
AFR, DENSITE, DT_MAX = 14.7, 745.0, 10.0   # rapport air/essence, densité essence (g/L), trou capteur max (s)


def _col(df, cle):
    return next((c for c in df.columns if cle.lower() in c.lower()), None)


def agreger(path):
    df = pd.read_csv(path, low_memory=False)
    ren = {"DayNum": "day", "VehId": "veh", "Trip": "trip", "Timestamp": "t_ms", "Vehicle Speed": "v",
           "MAF": "maf", "Engine RPM": "rpm", "OAT": "oat", "Fuel Rate": "fuel_rate"}
    df = df.rename(columns={_col(df, k): v for k, v in ren.items() if _col(df, k)})
    for c in ren.values():
        if c not in df:
            df[c] = np.nan
    df = df[list(ren.values())].sort_values(["veh", "trip", "t_ms"]).reset_index(drop=True)
    key = [df.veh, df.trip]
    df["v"] = df.groupby(["veh", "trip"])["v"].transform(lambda s: s.interpolate(limit_direction="both"))
    dt = df.groupby(["veh", "trip"])["t_ms"].diff().fillna(0) / 1000
    df["dt"] = dt.where(dt <= DT_MAX, 0).clip(lower=0)
    vms = df.v / 3.6
    df["a"] = (vms.groupby(key).diff() / df.dt.replace(0, np.nan)).fillna(0).clip(-6, 6)
    # carburant : Fuel Rate si présent, sinon reconstruit depuis le débit d'air (MAF)
    fuel_lh = df.fuel_rate.where(df.fuel_rate.notna(), df.maf * 3600 / (AFR * DENSITE))
    w = df.dt
    agg = pd.DataFrame({
        "veh": df.veh, "trip": df.trip, "day": df.day, "dt": w, "dist": df.v * w / 3600, "v": df.v,
        "arret": (df.v < 3) * w, "autoroute": (df.v > 90) * w, "acc_f": (df.a > 1.5) * w, "frein_f": (df.a < -2) * w,
        "a_pos": df.a.clip(lower=0) * w, "a_pos_n": (df.a > 0.1) * w, "rpm_w": df.rpm * w,
        "oat_w": df.oat * w, "oat_ok": df.oat.notna() * w, "fuel_l": fuel_lh * w / 3600, "fuel_ok": fuel_lh.notna() * w,
        "rpa": df.a.clip(lower=0) * vms * w,
        "depart": ((df.v >= 3) & (df.v.groupby(key).shift(1) < 3)).astype(int),
    }).groupby(["veh", "trip"]).agg(
        jour=("day", "min"), duree=("dt", "sum"), dist=("dist", "sum"), vmax=("v", "max"), vstd=("v", "std"),
        arret=("arret", "sum"), autoroute=("autoroute", "sum"), acc_f=("acc_f", "sum"), frein_f=("frein_f", "sum"),
        a_pos=("a_pos", "sum"), a_pos_n=("a_pos_n", "sum"), rpm_w=("rpm_w", "sum"), oat_w=("oat_w", "sum"),
        oat_ok=("oat_ok", "sum"), fuel_l=("fuel_l", "sum"), fuel_ok=("fuel_ok", "sum"), rpa=("rpa", "sum"),
        departs=("depart", "sum")).reset_index()
    return agg


def construire():
    fichiers = sorted(RAW.rglob("VED_*week*.csv")) + sorted(RAW.glob("VED_demo_part*.csv"))
    if not fichiers:
        raise FileNotFoundError("data/raw vide : lancer data/download_ved.py (ou data/make_demo_data.py)")
    t = pd.concat([agreger(f) for f in fichiers], ignore_index=True)
    t = t.sort_values("duree").drop_duplicates(["veh", "trip"], keep="last")   # trajet coupé entre 2 fichiers
    d = t.duree.replace(0, np.nan)
    trips = pd.DataFrame({
        "veh_id": t.veh, "trip_id": t.trip, "jour": t.jour, "duree_min": d / 60, "distance_km": t.dist,
        "vitesse_moy": t.dist / (d / 3600), "vitesse_max": t.vmax, "vitesse_std": t.vstd,
        "part_arret": t.arret / d, "part_autoroute": t.autoroute / d,
        "part_accel_forte": t.acc_f / d, "part_freinage_fort": t.frein_f / d,
        "accel_moy_pos": t.a_pos / t.a_pos_n.replace(0, np.nan), "rpm_moy": t.rpm_w / d,
        "temp_ext": (t.oat_w / t.oat_ok.replace(0, np.nan)),
        # variables construites
        "rpa": t.rpa / (t.dist * 1000).replace(0, np.nan), "arrets_par_km": t.departs / t.dist.replace(0, np.nan),
        # CIBLE (connue seulement après le trajet)
        "conso_l100": t.fuel_l / t.dist * 100, "couverture": t.fuel_ok / d})
    xl = RAW / "VED_Static_Data_ICE&HEV.xlsx"
    st = pd.read_excel(xl) if xl.exists() else pd.read_csv(RAW / "VED_Static_Data_ICE&HEV.csv")
    st.columns = [c.strip() for c in st.columns]
    st = st.replace(["NO DATA", "No Data", "-"], np.nan)
    st["cylindree_l"] = st["Engine Configuration & Displacement"].astype(str).str.extract(r"(\d+\.\d+)\s*L")[0].astype(float)
    st["poids_kg"] = pd.to_numeric(st["Generalized_Weight"], errors="coerce") * 0.4536
    st = st.rename(columns={"VehId": "veh_id", "Vehicle Type": "type_vehicule", "Vehicle Class": "classe",
                            "Drive Wheels": "transmission_roues"})
    st = st[["veh_id", "type_vehicule", "classe", "cylindree_l", "poids_kg", "transmission_roues"]]
    return trips.merge(st, on="veh_id", how="inner")     # ICE + HEV (les électriques n'ont pas de carburant)


def nettoyer(t):
    n0 = len(t)
    t = t[(t.distance_km >= 1) & (t.duree_min >= 2) & (t.couverture >= .8)
          & t.conso_l100.between(1, 40) & (t.vitesse_moy < 150)]
    print(f"nettoyage : {n0} -> {len(t)} trajets")
    return t.drop(columns="couverture").reset_index(drop=True)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    trips = nettoyer(construire())
    trips.to_csv(OUT / "trips.csv", index=False)
    print(f"OK : {trips.shape[0]} trajets x {trips.shape[1]} colonnes -> data/processed/trips.csv")
