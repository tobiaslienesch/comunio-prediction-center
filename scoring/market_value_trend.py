"""
Kriterium 5 - Marktwerttrend: uebernimmt einfach die "trend"-Spalte,
die wir schon beim Vereins-Abruf berechnen (steigend/fallend/stabil/
unbekannt, inkl. Staerke). Keine neue Berechnung noetig.
"""

import csv
import glob
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SQUADS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "squads")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "scoring")


def latest_csv(folder):
    files = sorted(glob.glob(os.path.join(folder, "*.csv")))
    if not files:
        raise FileNotFoundError(f"Keine CSV-Datei gefunden in {folder}")
    return files[-1]


def main():
    squad_path = latest_csv(SQUADS_DIR)

    with open(squad_path, encoding="utf-8") as f:
        squad = list(csv.DictReader(f))

    results = [
        {
            "spieler_id": p["spieler_id"],
            "name": p["name"],
            "verein": p["verein"],
            "marktwerttrend": p["trend"],
        }
        for p in squad
    ]

    date_str = os.path.basename(squad_path).removesuffix(".csv")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"marktwerttrend_{date_str}.csv")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["spieler_id", "name", "verein", "marktwerttrend"])
        writer.writeheader()
        writer.writerows(results)

    print(f"Quelle: {squad_path}\n")
    for r in results:
        print(f"{r['name']:<20} | {r['marktwerttrend']}")

    print(f"\nGespeichert unter: {output_path}")


if __name__ == "__main__":
    main()
