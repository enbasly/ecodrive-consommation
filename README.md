# EcoDrive — prédire la consommation de carburant d'une flotte

Équipe : Enzo BASLY, Guillaume, Rayan

## Objectif
EcoDrive prédit la consommation normale d'un trajet afin de repérer les surconsommations et de comparer les styles de conduite. Le cas d'usage retenu est une flotte professionnelle.

## Résultats principaux
> IMPORTANT : si le projet tourne encore sur les données de démonstration, remplacer cette version par les résultats VED réels avant le rendu final.

- MAE du modèle sur le test : **0,72 L/100 km**
- MAE de la règle actuelle : **1,27 L/100 km**
- Seuil d'alerte : **+15 %**, choisi sur le train
- Recall sur le test : **96 %**
- Fausses alertes estimées : **5,8 par semaine**
- Conduite nerveuse vs calme à trajet égal : **+13 à +23 % de consommation**
- Gain annuel, scénario central : **6130 €**
- Coût première année : **10800 €**
- ROI à 3 ans, scénario central : **-15 %**

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
