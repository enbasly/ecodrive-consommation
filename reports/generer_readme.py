# -*- coding: utf-8 -*-
"""Genere README.md depuis reports/resultats.json en restant robuste aux accents."""
from pathlib import Path
import json, unicodedata

ROOT = Path(__file__).resolve().parents[1]
R = json.loads((ROOT / "reports" / "resultats.json").read_text(encoding="utf-8"))


def norm(s):
    s = str(s).replace("²", "2").replace("€", "eur")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().replace("_", " ").split())


def get(d, *names, default=None):
    if not isinstance(d, dict): return default
    nd = {norm(k): v for k, v in d.items()}
    for n in names:
        if norm(n) in nd: return nd[norm(n)]
    return default


def f(x, d=2):
    if x is None: return "-"
    try: return f"{float(x):.{d}f}".replace(".", ",")
    except Exception: return str(x)

G = get(R, "regression", default={}) or {}
D = get(R, "decision", default={}) or {}
mt = get(G, "test_modele", default={}) or {}
mr = get(G, "test_regle", default={}) or {}
styles = get(D, "styles", default=[]) or []
roi = get(D, "roi", default=[]) or []
central = next((x for x in roi if str(get(x,"scenario",default="")).startswith("Central (")), {})
ecarts = [get(x,"ecart nerveux / calme","écart nerveux / calme") for x in styles]
ecarts = [float(x) for x in ecarts if x is not None]
style_txt = f"+{f(min(ecarts)*100,0)} à +{f(max(ecarts)*100,0)} %" if ecarts else "voir notebook 03"

texte = f'''# EcoDrive — prédire la consommation de carburant d'une flotte

Équipe : Enzo BASLY, Guillaume, Rayan

## Objectif
EcoDrive prédit la consommation normale d'un trajet afin de repérer les surconsommations et de comparer les styles de conduite. Le cas d'usage retenu est une flotte professionnelle.

## Résultats principaux
> IMPORTANT : si le projet tourne encore sur les données de démonstration, remplacer cette version par les résultats VED réels avant le rendu final.

- MAE du modèle sur le test : **{f(get(mt,"MAE"))} L/100 km**
- MAE de la règle actuelle : **{f(get(mr,"MAE"))} L/100 km**
- Seuil d'alerte : **+{f(float(get(D,"seuil",default=0))*100,0)} %**, choisi sur le train
- Recall sur le test : **{f(float(get(D,"recall",default=0))*100,0)} %**
- Fausses alertes estimées : **{f(float(get(D,"FP/an","fp_an",default=0))/52,1)} par semaine**
- Conduite nerveuse vs calme à trajet égal : **{style_txt} de consommation**
- Gain annuel, scénario central : **{f(get(central,"gain annuel (eur)","gain annuel (€)"),0)} €**
- Coût première année : **{f(get(central,"cout an 1 (eur)","coût an 1 (€)"),0)} €**
- ROI à 3 ans, scénario central : **{f(get(central,"ROI 3 ans (%)"),0)} %**

## Reproduire le projet
```bash
pip install -r requirements.txt
python data/download_ved.py
python src/prepare_trips.py
```
Puis exécuter dans l'ordre :
1. `notebooks/01_cadrage_eda.ipynb`
2. `notebooks/02_modelisation.ipynb`
3. `notebooks/03_decision_roi.ipynb`

Enfin :
```bash
python reports/generer_rapport.py
python reports/generer_readme.py
```

## Structure
- `data/` : téléchargement et préparation des données
- `src/` : configuration, pipeline et fonctions communes
- `notebooks/` : analyse, modélisation, décision et ROI
- `reports/` : figures, résultats, rapport et support oral

## Données
Vehicle Energy Dataset (VED), G. S. Oh, D. J. LeBlanc, H. Peng, 2020. Licence Apache 2.0.

## Répartition
- Enzo : cadrage, données, analyse exploratoire
- Guillaume : modèles, validation et résultats
- Rayan : alertes, styles de conduite et ROI

## Usage de l'IA générative
Microsoft Copilot a été utilisé pour aider à structurer le code et la rédaction. Les analyses ont été exécutées dans les notebooks et doivent pouvoir être expliquées par l'équipe.
'''
(ROOT / "README.md").write_text(texte, encoding="utf-8")
print("README OK ->", ROOT / "README.md")
