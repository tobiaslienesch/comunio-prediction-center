"""
Holt zwei Dinge von sofascore.com (per echtem Browser via Playwright,
da einfache Anfragen dort blockiert werden):

1. Die Bundesliga-Tabelle -> data/tables/<datum>.csv
   Solange die aktuelle Saison 2026/27 noch keine Ergebnisse hat,
   wird stattdessen die Tabelle der Saison 2025/26 verwendet - mit den
   letzten drei Plaetzen ersetzt durch die Aufsteiger (Schalke 04,
   Elversberg, Paderborn). Sobald die aktuelle Saison losgeht, wird
   automatisch auf die echten aktuellen Daten umgeschaltet.

2. Die naechsten 4 Spielpaarungen -> data/fixtures/<datum>.csv
   Der aktuelle Spieltag wird aus der "Spiele"-Zahl der aktuellen
   Saison-Tabelle abgeleitet (gespielte Spiele + 1 = naechster
   Spieltag).
"""

import csv
import os
from datetime import date

from playwright.sync_api import sync_playwright

TOURNAMENT_URL = "https://www.sofascore.com/de/football/tournament/germany/bundesliga/35#id:97464"
TOURNAMENT_ID = 35
CURRENT_SEASON_ID = 97464
FALLBACK_SEASON_ID = 77333  # Saison 2025/26

# Reihenfolge wie vorgegeben: Platz 16 = Schalke, 17 = Elversberg, 18 = Paderborn
PROMOTED_TEAMS = {
    16: "FC Schalke 04",
    17: "SV 07 Elversberg",
    18: "SC Paderborn 07",
}

TABLES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "tables")
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "fixtures")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def fetch_json(page, path):
    return page.evaluate(f"() => fetch('https://www.sofascore.com/api/v1/{path}').then(r => r.json())")


def get_standings(page, season_id):
    data = fetch_json(page, f"unique-tournament/{TOURNAMENT_ID}/season/{season_id}/standings/total")
    return data["standings"][0]["rows"]


def build_table_rows(page):
    current_rows = get_standings(page, CURRENT_SEASON_ID)
    total_matches = sum(r.get("matches", 0) for r in current_rows)

    if total_matches > 0:
        return [
            {
                "rang": r["position"],
                "verein": r["team"]["name"],
                "spiele": r["matches"],
                "punkte": r["points"],
            }
            for r in current_rows
        ], current_rows

    fallback_rows = get_standings(page, FALLBACK_SEASON_ID)
    table = []
    for r in fallback_rows:
        rang = r["position"]
        if rang in PROMOTED_TEAMS:
            table.append({"rang": rang, "verein": PROMOTED_TEAMS[rang], "spiele": None, "punkte": None})
        else:
            table.append({"rang": rang, "verein": r["team"]["name"], "spiele": r["matches"], "punkte": r["points"]})

    return table, current_rows


def get_next_fixtures(page, current_rows, n=4):
    matches_played = max((r.get("matches", 0) for r in current_rows), default=0)
    next_rounds = range(matches_played + 1, matches_played + 1 + n)

    fixtures = []
    for round_number in next_rounds:
        data = fetch_json(page, f"unique-tournament/{TOURNAMENT_ID}/season/{CURRENT_SEASON_ID}/events/round/{round_number}")
        for event in data.get("events", []):
            fixtures.append({
                "spieltag": round_number,
                "heimverein": event["homeTeam"]["name"],
                "gastverein": event["awayTeam"]["name"],
            })

    return fixtures


def save_csv(folder, filename_prefix, fieldnames, rows):
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, f"{date.today().isoformat()}.csv")

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return filepath


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(user_agent=USER_AGENT)
        page.goto(TOURNAMENT_URL, wait_until="networkidle", timeout=30000)

        table_rows, current_rows = build_table_rows(page)
        fixtures = get_next_fixtures(page, current_rows)

        browser.close()

    table_path = save_csv(TABLES_DIR, "table", ["rang", "verein", "spiele", "punkte"], table_rows)
    print(f"Tabelle ({len(table_rows)} Vereine) gespeichert unter: {table_path}")
    for row in table_rows:
        print(f"  {row['rang']:>2}. {row['verein']:<22} Spiele: {row['spiele']}  Punkte: {row['punkte']}")

    fixtures_path = save_csv(FIXTURES_DIR, "fixtures", ["spieltag", "heimverein", "gastverein"], fixtures)
    print(f"\n{len(fixtures)} Spielpaarungen gespeichert unter: {fixtures_path}")
    for f in fixtures:
        print(f"  Spt. {f['spieltag']}: {f['heimverein']} - {f['gastverein']}")


if __name__ == "__main__":
    main()
