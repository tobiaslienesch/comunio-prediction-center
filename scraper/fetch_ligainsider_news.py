"""
Kriterium 6 - Verletzung/Sperre (Startversion): letzte News-Headline
und Link pro Spieler von ligainsider.de, plus fuer "Players to Watch":
Anzahl der News der letzten 7 Tage und zwei einfache Schlagwort-Flags
(Transfer-News, Stammplatz-News). Noch keine tiefere Inhaltsanalyse -
nur ein regelbasierter Abgleich mit festen Schlagworten in den
Ueberschriften, passend zum regelbasierten Ansatz des Projekts.

Ligainsider hat eigene Spieler-IDs, keine gemeinsame ID mit Comunio.
Deshalb: einmal die Vereins-Kaderseite abrufen (liefert alle
Spieler-Links dieses Vereins), dann pro Comunio-Spieler per
Namensabgleich den passenden Link finden.
"""

import csv
import glob
import os
import re
import sys
import time
import unicodedata
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests
from bs4 import BeautifulSoup

NEWS_DATE_PATTERN = re.compile(r"(\d{2}\.\d{2}\.\d{4}) - \d{2}:\d{2}")

TRANSFER_KEYWORDS = [
    "wechsel", "transfer", "leihe", "verpflicht", "gerücht", "-poker",
    "interessiert", "abschied", "verkauf", "umworben", "wirbt",
]
STAMMPLATZ_KEYWORDS = ["stammplatz", "startelf", "stammspieler", "gesetzt"]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
BASE_URL = "https://www.ligainsider.de"
CLUB_KADER_URL = "https://www.ligainsider.de/sc-paderborn-07/1249/kader/"
CLUB_NAME = "SC Paderborn"

SQUADS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "squads")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "scoring")

SLUG_PATTERN = re.compile(r'href="(/([a-z0-9-]+)_(\d+)/)"')

FIELDNAMES = [
    "spieler_id", "name", "verein", "news_headline", "news_link",
    "news_count_7d", "transfer_news_flag", "stammplatz_news_flag",
]


def normalize(text):
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def latest_csv(folder):
    files = sorted(glob.glob(os.path.join(folder, "*.csv")))
    if not files:
        raise FileNotFoundError(f"Keine CSV-Datei gefunden in {folder}")
    return files[-1]


def fetch_player_slugs(kader_url):
    response = requests.get(kader_url, headers=HEADERS, timeout=10)
    response.raise_for_status()

    slugs = {}
    for path, slug, player_id in SLUG_PATTERN.findall(response.text):
        slugs[path] = slug.replace("-", " ")
    return slugs


def match_player(comunio_name, slugs):
    target = normalize(comunio_name)
    pattern = re.compile(r"\b" + re.escape(target) + r"\b")
    for path, full_name in slugs.items():
        if pattern.search(normalize(full_name)):
            return path
    return None


def contains_keyword(text, keywords):
    text = normalize(text)
    return any(keyword in text for keyword in keywords)


def fetch_player_news(player_path):
    response = requests.get(BASE_URL + player_path, headers=HEADERS, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    news_rows = soup.find_all("div", class_="news_row")
    if not news_rows:
        return None, None, 0, 0, 0

    first = news_rows[0]
    link_tag = first.find("h3").find("a") if first.find("h3") else None
    headline = link_tag.text.strip() if link_tag else None
    link = BASE_URL + link_tag.get("href") if link_tag else None

    now = datetime.now()
    count_7d = 0
    transfer_flag = 0
    stammplatz_flag = 0

    for row in news_rows:
        date_span = row.find("div", class_="news_column_mid")
        if date_span is None:
            continue
        date_match = NEWS_DATE_PATTERN.search(date_span.get_text())
        if not date_match:
            continue
        news_date = datetime.strptime(date_match.group(1), "%d.%m.%Y")
        if (now - news_date).days > 7:
            continue

        count_7d += 1
        row_link_tag = row.find("h3").find("a") if row.find("h3") else None
        row_headline = row_link_tag.text.strip() if row_link_tag else ""

        if contains_keyword(row_headline, TRANSFER_KEYWORDS):
            transfer_flag = 1
        if contains_keyword(row_headline, STAMMPLATZ_KEYWORDS):
            stammplatz_flag = 1

    return headline, link, count_7d, transfer_flag, stammplatz_flag


def process_club(club_kader_url, club_name):
    """Holt die News fuer alle Spieler eines Vereins und speichert sie
    (ersetzt vorhandene Zeilen fuer denselben Verein, behaelt die
    anderer Vereine - so bleibt ein erneuter Lauf ueberschneidungsfrei)."""
    squad_path = latest_csv(SQUADS_DIR)
    with open(squad_path, encoding="utf-8") as f:
        all_squads = list(csv.DictReader(f))

    squad = [p for p in all_squads if p["verein"] == club_name]
    if not squad:
        raise ValueError(f"Kein Spieler mit verein == '{club_name}' in {squad_path} gefunden.")

    slugs = fetch_player_slugs(club_kader_url)
    print(f"{len(slugs)} Spieler-Profile auf ligainsider fuer {club_name} gefunden.\n")

    results = []
    for p in squad:
        player_path = match_player(p["name"], slugs)

        headline, link, count_7d, transfer_flag, stammplatz_flag = (None, None, 0, 0, 0)
        if player_path:
            headline, link, count_7d, transfer_flag, stammplatz_flag = fetch_player_news(player_path)
            time.sleep(0.3)

        results.append({
            "spieler_id": p["spieler_id"],
            "name": p["name"],
            "verein": p["verein"],
            "news_headline": headline,
            "news_link": link,
            "news_count_7d": count_7d,
            "transfer_news_flag": transfer_flag,
            "stammplatz_news_flag": stammplatz_flag,
        })

        status = (
            f"{headline} | News (7 Tage): {count_7d} | Transfer: {transfer_flag} | Stammplatz: {stammplatz_flag}"
            if headline
            else f"keine News gefunden / kein Profil zugeordnet | News (7 Tage): {count_7d}"
        )
        print(f"{p['name']:<20} | {status}")

    date_str = os.path.basename(squad_path).removesuffix(".csv")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"ligainsider_news_{date_str}.csv")

    existing_rows = []
    if os.path.isfile(output_path):
        with open(output_path, encoding="utf-8") as f:
            existing_rows = [row for row in csv.DictReader(f) if row["verein"] != club_name]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(existing_rows)
        writer.writerows(results)

    print(f"\nGespeichert unter: {output_path}")
    return output_path


def main():
    process_club(CLUB_KADER_URL, CLUB_NAME)


if __name__ == "__main__":
    main()
