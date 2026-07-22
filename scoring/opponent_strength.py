"""
Kriterium 2 - Gegnerstaerke: pro Verein die durchschnittliche
Schwierigkeits-Punktzahl der naechsten 4 Gegner.

Punkteverteilung (je hoeher, desto leichter der Gegner):
Platz 1-2 = 1, 3-6 = 2, 7-10 = 3, 11-14 = 4, 15-18 = 5

Nutzt automatisch die jeweils neueste Tabellen- und Spielplan-CSV.
Baut nur diese eine Spalte auf, kein Gesamtscore.
"""

import csv
import glob
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TABLES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "tables")
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "fixtures")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "scoring")


def latest_csv(folder):
    files = sorted(glob.glob(os.path.join(folder, "*.csv")))
    if not files:
        raise FileNotFoundError(f"Keine CSV-Datei gefunden in {folder}")
    return files[-1]


def difficulty_score(rang):
    rang = int(rang)
    if rang <= 2:
        return 1
    if rang <= 6:
        return 2
    if rang <= 10:
        return 3
    if rang <= 14:
        return 4
    return 5


def load_table(filepath):
    with open(filepath, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {row["verein"]: difficulty_score(row["rang"]) for row in rows}


def load_fixtures(filepath):
    with open(filepath, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def next_opponents(club, fixtures):
    opponents = []
    for row in fixtures:
        spieltag = int(row["spieltag"])
        if row["heimverein"] == club:
            opponents.append((spieltag, row["gastverein"]))
        elif row["gastverein"] == club:
            opponents.append((spieltag, row["heimverein"]))

    opponents.sort(key=lambda x: x[0])
    return [o[1] for o in opponents]


def main():
    table_path = latest_csv(TABLES_DIR)
    fixtures_path = latest_csv(FIXTURES_DIR)

    difficulty_by_club = load_table(table_path)
    fixtures = load_fixtures(fixtures_path)

    results = []
    for club in sorted(difficulty_by_club.keys()):
        opponents = next_opponents(club, fixtures)
        scores = [difficulty_by_club[o] for o in opponents if o in difficulty_by_club]
        avg_score = round(sum(scores) / len(scores), 2) if scores else None

        results.append({
            "verein": club,
            "naechste_gegner": ", ".join(opponents),
            "gegnerstaerke_score": avg_score,
        })

    date_str = os.path.basename(table_path).removesuffix(".csv")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"gegnerstaerke_{date_str}.csv")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["verein", "naechste_gegner", "gegnerstaerke_score"])
        writer.writeheader()
        writer.writerows(results)

    print(f"Tabelle: {table_path}")
    print(f"Spielplan: {fixtures_path}\n")
    for r in results:
        print(f"{r['verein']:<22} | Score: {str(r['gegnerstaerke_score']):>5} | Gegner: {r['naechste_gegner']}")

    print(f"\nGespeichert unter: {output_path}")


if __name__ == "__main__":
    main()
