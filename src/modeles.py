"""Fonctions réutilisables : pipeline, baseline métier, métriques, détection, coûts."""
import json
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from config import NUM_FEATURES, CAT_FEATURES, RESULTS


def pipeline(modele):
    """Toute la préparation dans le pipeline -> ajustée sur le train uniquement (pas de fuite)."""
    num = Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())])
    cat = Pipeline([("imp", SimpleImputer(strategy="most_frequent")), ("ohe", OneHotEncoder(handle_unknown="ignore"))])
    return Pipeline([("prep", ColumnTransformer([("num", num, NUM_FEATURES), ("cat", cat, CAT_FEATURES)])),
                     ("model", modele)])


class MoyenneParVehicule(BaseEstimator, RegressorMixin):
    """Règle actuelle : conso moyenne de la catégorie du véhicule (type x classe x cylindrée)."""

    def __init__(self, cles=("type_vehicule", "classe", "cylindree_l")):
        self.cles = cles

    def fit(self, X, y):
        d = X[list(self.cles)].astype(str).assign(y=np.asarray(y))
        self.table_ = d.groupby(list(self.cles))["y"].mean()
        self.global_ = float(np.mean(y))
        return self

    def predict(self, X):
        idx = pd.MultiIndex.from_frame(X[list(self.cles)].astype(str))
        return self.table_.reindex(idx).fillna(self.global_).to_numpy()


def metriques(y, p):
    return {"MAE": mean_absolute_error(y, p), "RMSE": mean_squared_error(y, p) ** 0.5, "R2": r2_score(y, p)}


def contexte(df):
    """Type de trajet, pour comparer à contexte égal."""
    return np.where(df.part_autoroute > .4, "autoroute", np.where(df.part_arret > .05, "ville", "mixte"))


def blocs(veh_id, taille):
    """Blocs de `taille` trajets consécutifs par véhicule (données triées par date)."""
    s = pd.Series(veh_id)
    return s.astype(str).to_numpy() + "_" + (s.groupby(s).cumcount().to_numpy() // taille).astype(str)


def injecter_defauts(y, bloc, frac=0.10, seed=0):
    """Simule un défaut (+15 à +40 % de conso) sur une part des blocs : tous les trajets du bloc sont touchés."""
    rng = np.random.default_rng(seed)
    ub = np.unique(bloc)
    touches = {b: 1 + rng.uniform(.15, .40) for b in ub[rng.random(len(ub)) < frac]}
    y = np.asarray(y, float) * np.array([touches.get(b, 1.0) for b in bloc])
    return y, pd.Series({b: int(b in touches) for b in ub})


def ecart_par_bloc(y_obs, y_pred, bloc, dist):
    """(litres réels - litres prévus) / litres prévus, par bloc."""
    d = pd.DataFrame({"b": bloc, "o": np.asarray(y_obs) * dist, "p": np.asarray(y_pred) * dist}).groupby("b").sum()
    return (d.o - d.p) / d.p


def compter(ecart, labels, seuils):
    lab = labels.reindex(ecart.index).to_numpy(); e = ecart.to_numpy()
    return pd.DataFrame([{"seuil": s, "TP": int(((e > s) & (lab == 1)).sum()), "FP": int(((e > s) & (lab == 0)).sum()),
                          "FN": int(((e <= s) & (lab == 1)).sum()), "n_normaux": int((lab == 0).sum())} for s in seuils])


def sauver(cle, valeur):
    """Les chiffres du rapport et des slides sont lus ici (= ceux produits par le code)."""
    d = json.loads(RESULTS.read_text()) if RESULTS.exists() else {}
    d[cle] = valeur
    texte = json.dumps(d, indent=2, ensure_ascii=False, default=float)
    RESULTS.write_text(texte.replace(": NaN", ": null"))      # JSON valide
