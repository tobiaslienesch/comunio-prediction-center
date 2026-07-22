"""
Ruft eine Comunio-Vereinsseite ab und speichert die Spielertabelle
als wochentliche CSV unter data/squads/<datum>.csv. Mehrere Vereine
landen in derselben Wochen-Datei (Spalte "verein") - dafuer dieses
Skript einfach mit angepassten SQUAD_URL/CLUB_NAME pro Verein erneut
ausfuehren.
"""

import csv
import os
import sys
from datetime import date

import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SQUAD_URL = "https://stats.comunio.de/squad/81-SC+Paderborn"
CLUB_NAME = "SC Paderborn"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "squads")


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


def save_to_csv(players, club_name):
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, f"{date.today().isoformat()}.csv")
    file_exists = os.path.isfile(filepath)

    fieldnames = [
        "verein", "spieler_id", "name", "position", "punkte",
        "einsaetze", "punkte_pro_spiel", "marktwert", "trend",
    ]

    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        for p in players:
            writer.writerow({
                "verein": club_name,
                "spieler_id": p["player_id"],
                "name": p["name"],
                "position": p["position"],
                "punkte": p["points"],
                "einsaetze": p["appearances"],
                "punkte_pro_spiel": p["points_per_game"],
                "marktwert": p["market_value"],
                "trend": interpret_trend(p["trend_raw"]),
            })

    return filepath


if __name__ == "__main__":
    html = fetch_squad(SQUAD_URL)
    players = parse_squad(html)

    print(f"{len(players)} Spieler gefunden:\n")
    for p in players:
        print(
            f"{p['name']:<20} | {p['position']:<10} | "
            f"Pkt: {p['points']:>4} | Einsaetze: {p['appearances']:>8} | "
            f"PPS: {p['points_per_game']:>5} | "
            f"Marktwert: {p['market_value']:>10} | "
            f"Trend: {interpret_trend(p['trend_raw'])}"
        )

    filepath = save_to_csv(players, CLUB_NAME)
    print(f"\nGespeichert unter: {filepath}")
