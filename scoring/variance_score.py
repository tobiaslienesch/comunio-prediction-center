"""
Kriterium 4 - Varianz: wie stark schwanken die Punkte eines Spielers
um seinen eigenen Schnitt (ueber die ganze Saison, nur gespielte
Spieltage).

- standardabweichung: gleiche Einheit wie Punkte. Hoch = schwankt
  stark ("Zockerspieler"), niedrig = konstant.
- variationskoeffizient_pct: Standardabweichung im Verhaeltnis zum
  Punkteschnitt (in %). Macht Spieler mit unterschiedlichem Niveau
  fair vergleichbar.
"""

import csv
import glob
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import statistics

PLAYER_HISTORY_DIR = os.path.join(
    os.path.dirname(__file__), "..", "data", "player_history", "season_2025_26"
)
OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "scoring", "varianz_season_2025_26.csv"
)


def load_points(filepath):
    with open(filepath, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [float(row["punkte"]) for row in rows if row["punkte"]]


def main():
    files = glob.glob(os.path.join(PLAYER_HISTORY_DIR, "*.csv"))

    results = []
    for filepath in files:
        filename = os.path.basename(filepath).removesuffix(".csv")
        player_id, name = filename.split("_", 1)

        points = load_points(filepath)
        if not points:
            continue

        mean = statistics.mean(points)
        std = statistics.pstdev(points)
        cv_pct = round(std / mean * 100, 1) if mean else None

        results.append({
            "spieler_id": player_id,
            "name": name,
            "spiele_gezaehlt": len(points),
            "punkte_schnitt": round(mean, 2),
            "standardabweichung": round(std, 2),
            "variationskoeffizient_pct": cv_pct,
        })

    results.sort(key=lambda r: r["variationskoeffizient_pct"] or 0)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "spieler_id", "name", "spiele_gezaehlt",
            "punkte_schnitt", "standardabweichung", "variationskoeffizient_pct",
        ])
        writer.writeheader()
        writer.writerows(results)

    print(f"{len(results)} Spieler verarbeitet\n")
    for r in results:
        print(
            f"{r['name']:<20} | Spiele: {r['spiele_gezaehlt']:>2} | "
            f"Schnitt: {r['punkte_schnitt']:>6} | Std.abw.: {r['standardabweichung']:>6} | "
            f"VarKoeff: {str(r['variationskoeffizient_pct']):>6}%"
        )

    print(f"\nGespeichert unter: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
