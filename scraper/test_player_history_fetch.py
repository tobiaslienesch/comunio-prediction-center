"""
Test-Skript: Ruft die Spieltagsdaten eines Spielers (hier: Kane, Saison
2025/26) ab und speichert sie als CSV unter data/player_history/.
Diese Saison ist abgeschlossen, die Daten aendern sich nicht mehr -
deshalb reicht ein einmaliger Abruf.
"""

import csv
import os

import requests
from bs4 import BeautifulSoup

PLAYER_ID = "33838"
PLAYER_NAME = "Kane"
PROFILE_URL = f"https://stats.comunio.de/profile/2026/{PLAYER_ID}-{PLAYER_NAME}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "player_history")


def fetch_profile(url):
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.text


def to_number(text):
    text = text.strip()
    if text == "" or text == "-":
        return None
    return text.replace(",", ".")


def parse_season_history(html):
    soup = BeautifulSoup(html, "html.parser")

    heading = soup.find(
        lambda tag: tag.name == "h2" and tag.text.strip().startswith("Spieltagsdaten Saison")
    )
    if heading is None:
        return None, []

    season_label = heading.text.strip().replace("Spieltagsdaten Saison ", "")

    table = heading.find_parent("div", class_="folded").find_next_sibling(
        "div", class_="tableContainer"
    ).find("table")

    rows = table.find_all("tr")[1:]  # erste Zeile ist die Kopfzeile

    matches = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 11:
            continue

        opponent_img = cells[6].find("img")
        points_span = cells[5].find("span")

        matches.append({
            "spieltag": int(cells[0].text.strip()),
            "tore": len(cells[1].find_all("img", class_="icon-goal")),
            "punkte": to_number(points_span.text if points_span else cells[5].text),
            "gegner": opponent_img.get("title") if opponent_img else None,
            "heim_auswaerts": cells[7].text.strip(),
            "ergebnis": cells[8].get_text(strip=True),
            "punkte_gesamt": to_number(cells[9].text),
            "punkte_schnitt": to_number(cells[10].text),
        })

    matches.sort(key=lambda m: m["spieltag"])
    return season_label, matches


def save_to_csv(season_label, player_id, player_name, matches):
    season_folder = "season_" + season_label.replace("/", "_")
    folder = os.path.join(DATA_DIR, season_folder)
    os.makedirs(folder, exist_ok=True)

    filepath = os.path.join(folder, f"{player_id}_{player_name}.csv")
    fieldnames = [
        "spieltag", "tore", "punkte", "gegner",
        "heim_auswaerts", "ergebnis", "punkte_gesamt", "punkte_schnitt",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matches)

    return filepath


if __name__ == "__main__":
    html = fetch_profile(PROFILE_URL)
    season_label, matches = parse_season_history(html)

    print(f"Saison {season_label}: {len(matches)} Spieltage gefunden\n")
    for m in matches:
        print(
            f"Spt. {m['spieltag']:>2} | Tore: {m['tore']} | Pkt: {m['punkte']:>5} | "
            f"Gegner: {m['gegner']:<20} ({m['heim_auswaerts']}) | "
            f"Erg.: {m['ergebnis']:<6} | Gesamt: {m['punkte_gesamt']:>4} | "
            f"Schnitt: {m['punkte_schnitt']}"
        )

    filepath = save_to_csv(season_label, PLAYER_ID, PLAYER_NAME, matches)
    print(f"\nGespeichert unter: {filepath}")
