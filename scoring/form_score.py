"""
Kriterium 1 - Form: berechnet fuer jeden Spieler
- den Form-Wert (Punkteschnitt der letzten 5 GESPIELTEN Spieltage,
  unbewertete/nicht gespielte Spieltage zaehlen nicht mit)
- den Anteil gespielter Spiele bezogen auf die letzten 5 Spieltage
  der Liga (z.B. nur 1 von 5 gespielt = 20%), inkl. Ampel-Farbe

Baut nur diese beiden Spalten auf. Der gewichtete Gesamtscore kommt
erst am Ende, wenn alle Kriterien fertig sind.
"""

import csv
import glob
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PLAYER_HISTORY_DIR = os.path.join(
    os.path.dirname(__file__), "..", "data", "player_history", "season_2025_26"
)
OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "scoring", "season_2025_26.csv"
)


def load_player_matches(filepath):
    with open(filepath, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        row["spieltag"] = int(row["spieltag"])
        row["punkte"] = float(row["punkte"]) if row["punkte"] else 0.0

    rows.sort(key=lambda r: r["spieltag"])
    return rows


def form_value(rows, n=5):
    last_rows = rows[-n:]
    if not last_rows:
        return None
    return round(sum(r["punkte"] for r in last_rows) / len(last_rows), 2)


def played_percentage(rows, last_n_matchdays):
    played = {r["spieltag"] for r in rows}
    hits = sum(1 for md in last_n_matchdays if md in played)
    return round(hits / len(last_n_matchdays) * 100)


def ampel(pct):
    if pct >= 80:
        return "gruen"
    if pct >= 40:
        return "gelb"
    return "rot"


def main():
    files = glob.glob(os.path.join(PLAYER_HISTORY_DIR, "*.csv"))

    players = []
    global_max_spieltag = 0
    for filepath in files:
        rows = load_player_matches(filepath)
        if rows:
            global_max_spieltag = max(global_max_spieltag, rows[-1]["spieltag"])

        filename = os.path.basename(filepath).removesuffix(".csv")
        player_id, name = filename.split("_", 1)
        players.append({"player_id": player_id, "name": name, "rows": rows})

    last_5_matchdays = list(range(global_max_spieltag - 4, global_max_spieltag + 1))

    results = []
    for p in players:
        rows = p["rows"]
        pct = played_percentage(rows, last_5_matchdays)
        results.append({
            "spieler_id": p["player_id"],
            "name": p["name"],
            "form": form_value(rows),
            "gespielte_spiele_letzte_5_pct": pct,
            "gespielte_spiele_ampel": ampel(pct),
        })

    results.sort(key=lambda r: r["name"])

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "spieler_id", "name", "form",
            "gespielte_spiele_letzte_5_pct", "gespielte_spiele_ampel",
        ])
        writer.writeheader()
        writer.writerows(results)

    print(f"Letzte 5 Spieltage der Liga: {last_5_matchdays}")
    print(f"{len(results)} Spieler verarbeitet\n")
    for r in results:
        print(
            f"{r['name']:<20} | Form: {str(r['form']):>6} | "
            f"Letzte 5 gespielt: {r['gespielte_spiele_letzte_5_pct']:>3}% "
            f"({r['gespielte_spiele_ampel']})"
        )

    print(f"\nGespeichert unter: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
