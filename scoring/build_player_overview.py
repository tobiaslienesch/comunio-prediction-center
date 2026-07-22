"""
Fuehrt alle bisherigen Kriterien-Dateien zu einer Datenquelle fuer die
Webseite zusammen: eine JSON-Datei mit einem Eintrag pro Spieler,
inklusive des gewichteten Gesamtscores pro Marktwert-Kategorie.
"""

import csv
import glob
import json
import os
import re
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SQUADS_DIR = os.path.join(DATA_DIR, "squads")
SCORING_DIR = os.path.join(DATA_DIR, "scoring")
PLAYER_HISTORY_DIR = os.path.join(DATA_DIR, "player_history", "season_2025_26")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "website", "data", "players.json")

# Vereinsnamen sind bei Comunio und sofascore leicht unterschiedlich
# geschrieben. Diese Tabelle wird erweitert, sobald weitere Vereine
# dazukommen.
CLUB_NAME_COMUNIO_TO_SOFASCORE = {
    "1. FC Bayern München": "FC Bayern München",
    "Borussia Dortmund": "Borussia Dortmund",
    "RB Leipzig": "RB Leipzig",
    "Bayer 04 Leverkusen": "Bayer 04 Leverkusen",
    "VfB Stuttgart": "VfB Stuttgart",
    "TSG Hoffenheim": "TSG Hoffenheim",
    "Sport-Club Freiburg": "SC Freiburg",
    "Eintracht Frankfurt": "Eintracht Frankfurt",
    "FC Augsburg": "FC Augsburg",
    "1. FSV Mainz 05": "1. FSV Mainz 05",
    "1. FC Union Berlin": "1. FC Union Berlin",
    "SV Werder Bremen": "SV Werder Bremen",
    "1. FC Köln": "1. FC Köln",
    "Borussia M'gladbach": "Borussia M'gladbach",
    "Hamburger SV": "Hamburger SV",
    "FC Schalke 04": "FC Schalke 04",
    "SV Elversberg": "SV 07 Elversberg",
    "SC Paderborn": "SC Paderborn 07",
}

# Marktwert-Grenzen fuer die Sektionen (in Euro)
STARS_MIN = 6_500_000
PUNKTEHAMSTER_MIN = 3_000_000

TREND_PATTERN = re.compile(r"^(steigend|fallend) \(Staerke (\d+)\)$")


def parse_trend(text):
    if not text:
        return None, None, None
    match = TREND_PATTERN.match(text)
    if match:
        richtung, staerke = match.group(1), int(match.group(2))
        sort_value = staerke if richtung == "steigend" else -staerke
        return richtung, staerke, sort_value
    if text == "stabil":
        return "stabil", 0, 0
    return "unbekannt", None, None


# Kriterium -> (Feldname in "detail", Richtung: "high" = hoeher ist
# besser, "low" = niedriger ist besser)
ALL_CRITERIA = {
    "punkte": ("punkte_saison", "high"),
    "punkte_pro_spiel": ("punkte_pro_spiel", "high"),
    "gewichtete_punkte_pro_spiel": ("gewichtete_punkte_pro_spiel", "high"),
    "mw_pro_punkt": ("mw_pro_punkt", "low"),
    "marktwert": ("marktwert_raw", "low"),
    "form": ("form", "high"),
    "gespielt": ("gespielte_spiele_letzte_5_pct", "high"),
    "anteil_spiele_saison": ("anteil_spiele_saison_pct", "high"),
    "std_abweichung": ("standardabweichung", "low"),
    "gegnerstaerke": ("gegnerstaerke_score", "high"),
    "trend": ("trend_sort_value", "high"),
    "news_count_7d": ("news_count_7d", "high"),
    "transfernews": ("transfer_news_flag", "high"),
    "stammplatznews": ("stammplatz_news_flag", "high"),
}

# Zwei-Ebenen-Scoring: KPIs werden zu vier benannten Kategorien
# gebuendelt (dieselbe KPI darf in mehreren Kategorien auftauchen).
# Jede Marktwert-Kategorie (bzw. Players to Watch) gewichtet dann
# diese vier Kategorien unterschiedlich. Die beiden Ebenen werden
# rechnerisch zu einer effektiven KPI-Gewichtung verdichtet (siehe
# flatten_weights) - mathematisch identisch zu einer flachen
# Gewichtung, aber deutlich einfacher zu pflegen und zu verstehen.
KATEGORIEN = {
    "preis_leistung": {
        "punkte": 0.30, "punkte_pro_spiel": 0.30, "mw_pro_punkt": 0.30,
        "form": 0.10,
    },
    "konstanz": {
        "gespielt": 0.20, "anteil_spiele_saison": 0.20, "std_abweichung": 0.40,
        "punkte_pro_spiel": 0.20,
    },
    "leistungspotenzial": {
        "form": 0.30, "gegnerstaerke": 0.30, "gewichtete_punkte_pro_spiel": 0.30,
        "trend": 0.10,
    },
    "mw_entwicklung": {
        "news_count_7d": 0.05, "transfernews": 0.25, "stammplatznews": 0.25,
        "trend": 0.30, "form": 0.15,
    },
}

# Gewichtung der vier Kategorien je Marktwert-Kategorie (muss je
# Marktwert-Kategorie 100% ergeben).
KATEGORIE_GEWICHTUNG = {
    "stars": {
        "preis_leistung": 0.65, "konstanz": 0.25,
        "leistungspotenzial": 0.05, "mw_entwicklung": 0.05,
    },
    "punktehamster": {
        "preis_leistung": 0.25, "konstanz": 0.60,
        "leistungspotenzial": 0.10, "mw_entwicklung": 0.05,
    },
    "schnaeppchen": {
        "preis_leistung": 0.10, "konstanz": 0.10,
        "leistungspotenzial": 0.50, "mw_entwicklung": 0.30,
    },
}

WATCH_MARKTWERT_MAX = 8_000_000

WATCH_KATEGORIE_GEWICHTUNG = {
    "preis_leistung": 0.15, "konstanz": 0.05,
    "leistungspotenzial": 0.30, "mw_entwicklung": 0.50,
}


def flatten_weights(kategorie_gewichtung):
    """Verdichtet Kategorie-Gewichte x KPI-Gewichte je Kategorie zu
    einer effektiven KPI-Gewichtung (mathematisch gleichwertig zu
    einer zweistufigen Berechnung, da beides gewichtete Summen sind)."""
    effective = defaultdict(float)
    for kategorie, kat_weight in kategorie_gewichtung.items():
        for kpi, kpi_weight in KATEGORIEN[kategorie].items():
            effective[kpi] += kat_weight * kpi_weight
    return dict(effective)


SCORE_WEIGHTS = {section: flatten_weights(kg) for section, kg in KATEGORIE_GEWICHTUNG.items()}
WATCH_WEIGHTS = flatten_weights(WATCH_KATEGORIE_GEWICHTUNG)


def print_effective_weights():
    sections = list(SCORE_WEIGHTS) + ["players_to_watch"]
    all_weights = dict(SCORE_WEIGHTS, players_to_watch=WATCH_WEIGHTS)
    kpis = sorted(ALL_CRITERIA)

    print("\nEffektive KPI-Gewichtung (Kategorie x KPI verdichtet):")
    header = f"{'KPI':<26}" + "".join(f"{s:>18}" for s in sections)
    print(header)
    for kpi in kpis:
        row = f"{kpi:<26}"
        for s in sections:
            row += f"{all_weights[s].get(kpi, 0) * 100:>17.2f}%"
        print(row)
    print()
    for s in sections:
        print(f"Summe {s}: {sum(all_weights[s].values()) * 100:.1f}%")
    print()


def to_float(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    value = str(value).strip()
    if value in ("", "-"):
        return None
    return float(value.replace(",", "."))


def scaled_score(val, rng, direction):
    if val is None or rng is None:
        return 1.0  # fehlender Wert = schlechtestmoeglicher Fall
    if rng[0] == rng[1]:
        return 5.5  # kein Unterschied zwischen den Spielern moeglich
    if direction == "high":
        return 1 + 9 * (val - rng[0]) / (rng[1] - rng[0])
    return 1 + 9 * (rng[1] - val) / (rng[1] - rng[0])


# Einige KPIs werden nicht mehr relativ zu den anderen Spielern der
# Gruppe bewertet, sondern auf einer fixen, absoluten Skala (0-10):
# Wert <= Minimum -> 0, Wert >= Maximum -> 10, dazwischen linear
# interpoliert. z.B. gegnerstaerke: 1 -> 0, 5 -> 10, 3 -> 5.
ABSOLUTE_SCALES = {
    "form": (0, 8),
    "gespielt": (0, 100),
    "anteil_spiele_saison": (0, 100),
    "gegnerstaerke": (1, 5),
}


def absolute_score(val, scale):
    if val is None:
        return 0.0  # fehlender Wert = schlechtestmoeglicher Fall (0 auf dieser Skala)
    lo, hi = scale
    score = (val - lo) / (hi - lo) * 10
    return max(0.0, min(10.0, score))


def score_for_kpi(key, val, rng, direction):
    if key in ABSOLUTE_SCALES:
        return absolute_score(val, ABSOLUTE_SCALES[key])
    return scaled_score(val, rng, direction)


def ampel_for(total):
    if total > 7:
        return "gruen"
    if total >= 3:
        return "gelb"
    return "rot"


def compute_weighted_score(group, criteria, weights):
    """Berechnet fuer jeden Spieler in group einen gewichteten
    1-10-Score, normiert relativ zu den anderen Spielern in group."""
    raw_values = {key: {} for key in criteria}
    for p in group:
        for key, (detail_key, _) in criteria.items():
            raw_values[key][p["spieler_id"]] = to_float(p["detail"].get(detail_key))

    ranges = {}
    for key in criteria:
        values = [v for v in raw_values[key].values() if v is not None]
        ranges[key] = (min(values), max(values)) if values else None

    scores = {}
    for p in group:
        total = 0.0
        for key, (_, direction) in criteria.items():
            weight = weights.get(key, 0)
            if weight == 0:
                continue
            total += weight * score_for_kpi(key, raw_values[key][p["spieler_id"]], ranges[key], direction)
        scores[p["spieler_id"]] = round(total, 1)

    return scores


def compute_kategorie_breakdown(group):
    """Score (1-10) je der vier Kategorien selbst, unabhaengig von deren
    Gewicht im Gesamtscore - nutzt je Kategorie nur deren eigene
    KPI-Gewichte (die zusammen bereits 100% ergeben)."""
    scores_by_kategorie = {}
    for kategorie, kpi_weights in KATEGORIEN.items():
        criteria_subset = {kpi: ALL_CRITERIA[kpi] for kpi in kpi_weights}
        scores_by_kategorie[kategorie] = compute_weighted_score(group, criteria_subset, kpi_weights)
    return scores_by_kategorie


def apply_kategorie_breakdown(group, score_field, ampel_field):
    breakdown = compute_kategorie_breakdown(group)
    for p in group:
        pid = p["spieler_id"]
        p[score_field] = {kat: breakdown[kat][pid] for kat in KATEGORIEN}
        p[ampel_field] = {kat: ampel_for(breakdown[kat][pid]) for kat in KATEGORIEN}


def compute_kpi_scores(group):
    """Skalierter (1-10) Einzel-Score je KPI, unabhaengig von der
    Kategorie-Zugehoerigkeit - Basis fuer die aufklappbare
    KPI-Detailansicht auf der Webseite."""
    raw_values = {key: {} for key in ALL_CRITERIA}
    for p in group:
        for key, (detail_key, _) in ALL_CRITERIA.items():
            raw_values[key][p["spieler_id"]] = to_float(p["detail"].get(detail_key))

    ranges = {}
    for key in ALL_CRITERIA:
        values = [v for v in raw_values[key].values() if v is not None]
        ranges[key] = (min(values), max(values)) if values else None

    scores = {}
    for p in group:
        pid = p["spieler_id"]
        scores[pid] = {}
        for key, (_, direction) in ALL_CRITERIA.items():
            scores[pid][key] = round(score_for_kpi(key, raw_values[key][pid], ranges[key], direction), 1)
    return scores


def apply_kpi_breakdown(group, score_field, ampel_field):
    kpi_scores = compute_kpi_scores(group)
    for p in group:
        pid = p["spieler_id"]
        p[score_field] = kpi_scores[pid]
        p[ampel_field] = {kpi: ampel_for(v) for kpi, v in kpi_scores[pid].items()}


def compute_gesamtscores(players):
    by_section = defaultdict(list)
    for p in players:
        if p["marktwert_sektion"] in SCORE_WEIGHTS:
            by_section[p["marktwert_sektion"]].append(p)

    for section, group in by_section.items():
        scores = compute_weighted_score(group, ALL_CRITERIA, SCORE_WEIGHTS[section])
        for p in group:
            p["gesamtscore"] = scores[p["spieler_id"]]
            p["gesamtscore_ampel"] = ampel_for(p["gesamtscore"])
        apply_kategorie_breakdown(group, "kategorie_scores", "kategorie_scores_ampel")
        apply_kpi_breakdown(group, "kpi_scores", "kpi_scores_ampel")


def compute_watch_scores(players):
    group = [p for p in players if p["marktwert"] is not None and p["marktwert"] < WATCH_MARKTWERT_MAX]
    scores = compute_weighted_score(group, ALL_CRITERIA, WATCH_WEIGHTS)
    for p in group:
        p["watch_score"] = scores[p["spieler_id"]]
        p["watch_score_ampel"] = ampel_for(p["watch_score"])
    apply_kategorie_breakdown(group, "watch_kategorie_scores", "watch_kategorie_scores_ampel")
    apply_kpi_breakdown(group, "watch_kpi_scores", "watch_kpi_scores_ampel")


def rated_appearances(einsaetze_text):
    """'22 (22)' -> 22, '1 (0)' -> 0, '-' -> 0."""
    if not einsaetze_text or einsaetze_text == "-":
        return 0
    match = re.search(r"\((\d+)\)", einsaetze_text)
    return int(match.group(1)) if match else 0


def compute_global_max_spieltag():
    """Hoechster Spieltag ueber alle Spieler-Historien - entspricht dem
    aktuellen Ligastand (34 bei einer abgeschlossenen Saison, sonst
    der aktuelle Spieltag)."""
    max_spieltag = 0
    for filepath in glob.glob(os.path.join(PLAYER_HISTORY_DIR, "*.csv")):
        with open(filepath, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                spieltag = row.get("spieltag")
                if spieltag and spieltag.isdigit():
                    max_spieltag = max(max_spieltag, int(spieltag))
    return max_spieltag


def load_player_points(player_id, name):
    """Punkte je gewertetem Spieltag fuer einen Spieler, neueste
    zuerst. Leere Liste, wenn keine Historie-Datei existiert."""
    filepath = os.path.join(PLAYER_HISTORY_DIR, f"{player_id}_{name}.csv")
    if not os.path.isfile(filepath):
        return []

    with open(filepath, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    rows.sort(key=lambda r: int(r["spieltag"]), reverse=True)
    return [to_float(r["punkte"]) for r in rows if r.get("punkte")]


def mean(values):
    return sum(values) / len(values)


def compute_weighted_pps(points_newest_first):
    """Gewichteter Punkteschnitt, der zuletzt gespielte Spiele hoeher
    gewichtet:
    - ab 20 gewerteten Spielen: letzte 10 = 50%, Spiele 11-20 = 30%,
      Rest = 20%
    - ab 10 bis unter 20 Spielen: letzte 10 = 70%, Rest = 30%
    - unter 10 Spielen: alle Spiele = 100% (einfacher Schnitt)
    Falls ein Fenster (z.B. bei genau 20 Spielen der "Rest") leer ist,
    wird dessen Gewicht auf die uebrigen, nicht-leeren Fenster verteilt."""
    n = len(points_newest_first)
    if n == 0:
        return None
    if n < 10:
        return mean(points_newest_first)

    if n < 20:
        buckets = [
            (points_newest_first[:10], 0.70),
            (points_newest_first[10:], 0.30),
        ]
    else:
        buckets = [
            (points_newest_first[:10], 0.50),
            (points_newest_first[10:20], 0.30),
            (points_newest_first[20:], 0.20),
        ]

    active = [(values, weight) for values, weight in buckets if values]
    total_weight = sum(weight for _, weight in active)
    return sum(mean(values) * weight for values, weight in active) / total_weight


def gegnerstaerke_label(score):
    if score is None:
        return None
    score = float(score)
    if score < 2:
        return "Schwer"
    if score < 3:
        return "Mittel"
    if score < 4:
        return "Leicht"
    return "Sehr leicht"


def latest_csv(folder):
    files = sorted(glob.glob(os.path.join(folder, "*.csv")))
    if not files:
        raise FileNotFoundError(f"Keine CSV-Datei gefunden in {folder}")
    return files[-1]


def read_csv(filepath):
    with open(filepath, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def index_by(rows, key):
    return {row[key]: row for row in rows}


def market_value_section(marktwert):
    if marktwert is None:
        return None
    if marktwert > STARS_MIN:
        return "stars"
    if marktwert >= PUNKTEHAMSTER_MIN:
        return "punktehamster"
    return "schnaeppchen"


def main():
    squad = read_csv(latest_csv(SQUADS_DIR))

    form_by_id = index_by(read_csv(os.path.join(SCORING_DIR, "season_2025_26.csv")), "spieler_id")
    varianz_by_id = index_by(read_csv(os.path.join(SCORING_DIR, "varianz_season_2025_26.csv")), "spieler_id")
    mw_ratio_by_id = index_by(read_csv(latest_csv_matching(SCORING_DIR, "marktwert_punkte_verhaeltnis_*.csv")), "spieler_id")
    news_by_id = index_by(read_csv(latest_csv_matching(SCORING_DIR, "ligainsider_news_*.csv")), "spieler_id")
    gegner_by_club = index_by(read_csv(latest_csv_matching(SCORING_DIR, "gegnerstaerke_*.csv")), "verein")

    global_max_spieltag = compute_global_max_spieltag()

    players = []
    for p in squad:
        pid = p["spieler_id"]
        form = form_by_id.get(pid, {})
        varianz = varianz_by_id.get(pid, {})
        mw_ratio = mw_ratio_by_id.get(pid, {})
        news = news_by_id.get(pid, {})

        sofascore_club = CLUB_NAME_COMUNIO_TO_SOFASCORE.get(p["verein"], p["verein"])
        gegner = gegner_by_club.get(sofascore_club, {})

        marktwert = int(p["marktwert"]) if p["marktwert"] else None
        gegnerstaerke_score = gegner.get("gegnerstaerke_score") or None
        trend_richtung, trend_staerke, trend_sort_value = parse_trend(p["trend"])

        # Punkte pro Spiel bei weniger als 5 gewerteten Spielen auf 0
        # setzen - sonst verzerren Ausreisser mit 1-2 Spielen (z.B.
        # 6,0 Punkte/Spiel nach nur einem Einsatz) das Bild.
        punkte_pro_spiel = p["punkte_pro_spiel"] or None
        rated = rated_appearances(p["einsaetze"])
        if rated < 5:
            punkte_pro_spiel = "0"

        # Anteil Spiele: gewertete Einsaetze / bisherige Ligaspieltage.
        anteil_spiele_saison_pct = (
            round(rated / global_max_spieltag * 100, 1) if global_max_spieltag else None
        )

        # Gewichtete Punkte pro Spiel: juengere Spiele zaehlen mehr
        # (siehe compute_weighted_pps).
        player_points = load_player_points(pid, p["name"])
        gewichtete_pps = compute_weighted_pps(player_points)

        players.append({
            "spieler_id": pid,
            "name": p["name"],
            "verein": p["verein"],
            "position": p["position"],
            "marktwert": marktwert,
            "marktwert_sektion": market_value_section(marktwert),
            "gesamtscore": None,
            "gesamtscore_ampel": None,
            "kategorie_scores": None,
            "kategorie_scores_ampel": None,
            "kpi_scores": None,
            "kpi_scores_ampel": None,
            "watch_score": None,
            "watch_score_ampel": None,
            "watch_kategorie_scores": None,
            "watch_kategorie_scores_ampel": None,
            "watch_kpi_scores": None,
            "watch_kpi_scores_ampel": None,
            "detail": {
                "punkte_saison": p["punkte"] or None,
                "punkte_pro_spiel": punkte_pro_spiel,
                "gewichtete_punkte_pro_spiel": round(gewichtete_pps, 2) if gewichtete_pps is not None else None,
                "marktwert_raw": marktwert,
                "anteil_spiele_saison_pct": anteil_spiele_saison_pct,
                "einsaetze": p["einsaetze"] or None,
                "form": form.get("form") or None,
                "gespielte_spiele_letzte_5_pct": form.get("gespielte_spiele_letzte_5_pct") or None,
                "gespielte_spiele_ampel": form.get("gespielte_spiele_ampel") or None,
                "gegnerstaerke_score": gegnerstaerke_score,
                "gegnerstaerke_label": gegnerstaerke_label(gegnerstaerke_score),
                "naechste_gegner": gegner.get("naechste_gegner") or None,
                "mw_pro_punkt": mw_ratio.get("mw_pro_punkt") or None,
                "mw_pro_punkteschnitt": mw_ratio.get("mw_pro_punkteschnitt") or None,
                "standardabweichung": varianz.get("standardabweichung") or None,
                "variationskoeffizient_pct": varianz.get("variationskoeffizient_pct") or None,
                "trend_richtung": trend_richtung,
                "trend_staerke": trend_staerke,
                "trend_sort_value": trend_sort_value,
                "news_headline": news.get("news_headline") or None,
                "news_link": news.get("news_link") or None,
                "news_count_7d": news.get("news_count_7d") or "0",
                "transfer_news_flag": news.get("transfer_news_flag") or "0",
                "stammplatz_news_flag": news.get("stammplatz_news_flag") or "0",
            },
        })

    compute_gesamtscores(players)
    compute_watch_scores(players)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(players, f, ensure_ascii=False, indent=2)

    print(f"{len(players)} Spieler zusammengefuehrt.")
    print(f"Gespeichert unter: {OUTPUT_PATH}")
    print_effective_weights()


def latest_csv_matching(folder, pattern):
    files = sorted(glob.glob(os.path.join(folder, pattern)))
    if not files:
        raise FileNotFoundError(f"Keine Datei gefunden fuer {pattern} in {folder}")
    return files[-1]


if __name__ == "__main__":
    main()
