"""
Baut eine kompakte Zeitreihe des Marktwerts pro Spieler aus allen
taeglichen Kader-Schnappschuessen (data/squads/*.csv). Wird von der
Spieleranalyse-Seite genutzt (Verlaufsdiagramm + Kennzahlen wie
"Entwicklung vs. Vortag"). Alle Berechnungen (Vergleiche, Prognose,
Marktdurchschnitt) passieren clientseitig in app.js - dieses Skript
liefert nur die rohen Datenpunkte je Tag.
"""

import csv
import glob
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SQUADS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "squads")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "website", "data", "marktwert_history.json")


def main():
    history = {}

    files = sorted(glob.glob(os.path.join(SQUADS_DIR, "*.csv")))
    for filepath in files:
        datum = os.path.basename(filepath).removesuffix(".csv")
        with open(filepath, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if not row.get("marktwert"):
                    continue
                pid = row["spieler_id"]
                history.setdefault(pid, []).append({
                    "datum": datum,
                    "marktwert": int(row["marktwert"]),
                })

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False)

    total_points = sum(len(v) for v in history.values())
    print(f"{len(history)} Spieler, {total_points} Datenpunkte gespeichert unter: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
