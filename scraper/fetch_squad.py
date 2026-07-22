"""
Ruft die Comunio-Kader-Seiten aller 18 Bundesliga-Vereine ab (siehe
scraper/clubs.py) und speichert alle Spieler zusammen in einer
CSV unter data/squads/<datum>.csv. Ein erneuter Lauf am selben Tag
ueberschreibt die Datei komplett neu (keine doppelten Zeilen bei
mehrfachem Ausfuehren, z.B. bei einem Actions-Retry).
"""

import csv
import os
import sys
import time
from datetime import date

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(__file__))
from clubs import CLUBS

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "squads")

FIELDNAMES = [
    "verein", "spieler_id", "name", "position", "punkte",
    "einsaetze", "punkte_pro_spiel", "marktwert", "trend",
]


def interpret_trend(trend_raw):
    # trend_raw sieht aus wie 'icon-trend_5', 'icon-trend_-4' oder 'icon-trend_' (leer)
    suffix = trend_raw.removeprefix("icon-trend_")
    if suffix == "":
        return "unbekannt"
    value = int(suffix)
    if value > 0:
        return f"steigend (Staerke {value})"
    if value < 0:
        return f"fallend (Staerke {abs(value)})"
    return "stabil"


def fetch_squad(url):
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.text


def parse_squad(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id="teamTable")
    rows = table.find("tbody").find_all("tr")

    players = []
    for row in rows:
        cells = row.find_all("td")

        name_cell = row.find("td", class_="playerName")
        name = name_cell.find("a").text.strip()
        player_id = name_cell.get("data-playerid")

        position_img = cells[0].find("img")
        position = position_img.get("title") if position_img else None

        points = cells[3].text.strip()
        appearances = cells[4].text.strip()
        points_per_game = cells[5].text.strip()

        market_value_cell = cells[9]
        market_value = market_value_cell.get("data-value")

        trend_img = cells[10].find("img")
        trend_class = trend_img.get("class") if trend_img else []
        trend_raw = trend_class[-1] if trend_class else None

        players.append({
            "player_id": player_id,
            "name": name,
            "position": position,
            "points": points,
            "appearances": appearances,
            "points_per_game": points_per_game,
            "market_value": market_value,
            "trend_raw": trend_raw,
        })

    return players


def fetch_all_clubs():
    """Holt die Kader aller Vereine aus clubs.py und gibt eine Liste
    aller Spieler-Zeilen zurueck (passend zu FIELDNAMES)."""
    all_rows = []
    for club in CLUBS:
        html = fetch_squad(club["comunio_url"])
        players = parse_squad(html)
        print(f"{club['name']}: {len(players)} Spieler gefunden.")

        for p in players:
            all_rows.append({
                "verein": club["name"],
                "spieler_id": p["player_id"],
                "name": p["name"],
                "position": p["position"],
                "punkte": p["points"],
                "einsaetze": p["appearances"],
                "punkte_pro_spiel": p["points_per_game"],
                "marktwert": p["market_value"],
                "trend": interpret_trend(p["trend_raw"]),
            })
        time.sleep(0.3)

    return all_rows


def save_to_csv(rows):
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, f"{date.today().isoformat()}.csv")

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    return filepath


def main():
    rows = fetch_all_clubs()
    filepath = save_to_csv(rows)
    print(f"\n{len(rows)} Spieler insgesamt gespeichert unter: {filepath}")


if __name__ == "__main__":
    main()
