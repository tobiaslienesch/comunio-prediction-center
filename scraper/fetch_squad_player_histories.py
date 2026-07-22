"""
Holt die Saison-2025/26-Spieltagshistorie fuer alle Spieler im
aktuellen Kader (SQUAD_URL aus fetch_squad.py) und speichert sie
einzeln als CSV.

Die Spieler-Liste (Namen + IDs) kommt von der Vereinsseite
(fetch_squad.py), die Profil-URL wird daraus gebaut - der Name im
Link ist egal, nur die ID zaehlt (getestet).
"""

import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from fetch_squad import SQUAD_URL, fetch_squad, parse_squad
from test_player_history_fetch import fetch_profile, parse_season_history, save_to_csv

PROFILE_URL_TEMPLATE = "https://stats.comunio.de/profile/2026/{player_id}-x"


def main():
    squad_html = fetch_squad(SQUAD_URL)
    players = parse_squad(squad_html)
    print(f"{len(players)} Spieler im Kader gefunden.\n")

    for player in players:
        player_id = player["player_id"]
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
