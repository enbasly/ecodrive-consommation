"""
Téléchargement du Vehicle Energy Dataset (VED).
Source : G. S. Oh, D. J. LeBlanc, H. Peng, "Vehicle Energy Dataset (VED)", IEEE Transactions on ITS, 2020.
Dépôt : https://github.com/gsoh/VED (licence Apache 2.0)

Usage : python data/download_ved.py   (nécessite py7zr pour décompresser)
Si le téléchargement échoue : récupérer à la main sur le dépôt GitHub (dossier Data/)
  VED_Static_Data_ICE&HEV.xlsx, VED_DynamicData_Part1.7z, VED_DynamicData_Part2.7z
et les décompresser dans data/raw/.
"""
from pathlib import Path
import urllib.request

RAW = Path(__file__).resolve().parent / "raw"
RAW.mkdir(parents=True, exist_ok=True)
BASE = "https://github.com/gsoh/VED/raw/master/Data/"
FICHIERS = ["VED_Static_Data_ICE&HEV.xlsx", "VED_DynamicData_Part1.7z", "VED_DynamicData_Part2.7z"]

for nom in FICHIERS:
    if not (RAW / nom).exists():
        print("téléchargement :", nom)
        urllib.request.urlretrieve(BASE + urllib.request.quote(nom), RAW / nom)

try:
    import py7zr
    for nom in FICHIERS:
        if nom.endswith(".7z"):
            with py7zr.SevenZipFile(RAW / nom, "r") as z:
                z.extractall(RAW)
except ImportError:
    print("py7zr absent : décompresser les .7z à la main dans data/raw/")

# ne pas mélanger avec les données de démonstration
for f in list(RAW.glob("VED_demo_part*.csv")) + [RAW / "VED_Static_Data_ICE&HEV.csv"]:
    if f.exists():
        f.unlink()
print("OK. Ensuite : python src/prepare_trips.py")
