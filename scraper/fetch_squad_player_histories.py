"""
Holt die Saison-2025/26-Spieltagshistorie fuer alle Spieler aus dem
aktuellsten Kader (neueste Datei in data/squads/) und speichert sie
einzeln als CSV. Laeuft immer fuer ALLE Spieler aller 18 Vereine -
gehoert in den woechentlichen Automatisierungs-Lauf, da sich die
Spieltagsdaten nur nach einem Spieltag aendern.

Die Spieler-Liste (Namen + IDs) kommt aus der Kader-CSV
(scraper/fetch_squad.py), die Profil-URL wird daraus gebaut - der
Name im Link ist egal, nur die ID zaehlt (getestet).
"""

import csv
import glob
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(__file__))
from test_player_history_fetch import fetch_profile, parse_season_history, save_to_csv

SQUADS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "squads")
PROFILE_URL_TEMPLATE = "https://stats.comunio.de/profile/2026/{player_id}-x"


def latest_squad_csv():
    files = sorted(glob.glob(os.path.join(SQUADS_DIR, "*.csv")))
    if not files:
        raise FileNotFoundError(f"Keine Kader-CSV gefunden in {SQUADS_DIR}")
    return files[-1]


def main():
    squad_path = latest_squad_csv()
    with open(squad_path, encoding="utf-8") as f:
        players = list(csv.DictReader(f))
    print(f"{len(players)} Spieler in {os.path.basename(squad_path)} gefunden.\n")

    for player in players:
        player_id = player["spieler_id"]
        name = player["name"]
        url = PROFILE_URL_TEMPLATE.format(player_id=player_id)

        profile_html = fetch_profile(url)
        season_label, matches = parse_season_history(profile_html)

        if season_label is None:
            print(f"{name} (ID {player_id}): keine Spieltagsdaten vorhanden")
            time.sleep(0.5)
            continue

        filepath = save_to_csv(season_label, player_id, name, matches)
        print(f"{name} (ID {player_id}): {len(matches)} Spieltage -> {filepath}")

        time.sleep(0.5)  # kurze Pause, um die Seite nicht zu ueberlasten


if __name__ == "__main__":
    main()
