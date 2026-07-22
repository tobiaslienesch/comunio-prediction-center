"""
Kriterium 3 - Marktwert-/Punkte-Verhaeltnis: zwei Werte pro Spieler.

1) mw_pro_punkt        = Marktwert / Gesamtpunkte
2) mw_pro_punkteschnitt = Marktwert / Punkte-pro-Spiel-Schnitt

Nutzt die Werte aus der wochentlichen Vereins-CSV (data/squads/).
Solange die neue Saison noch keine eigenen Punkte hat, zeigt Comunio
dort automatisch die Werte der Vorsaison an - genau wie gewuenscht.
Sobald die neue Saison laeuft, wechseln diese Werte von selbst um,
ohne dass wir etwas am Skript aendern muessen.
"""

import csv
import glob
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SQUADS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "squads")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "scoring")


def latest_csv(folder):
    files = sorted(glob.glob(os.path.join(folder, "*.csv")))
    if not files:
        raise FileNotFoundError(f"Keine CSV-Datei gefunden in {folder}")
    return files[-1]


def to_number(text):
    text = (text or "").strip()
    if text in ("", "-"):
        return None
    return float(text.replace(",", "."))


def main():
    squad_path = latest_csv(SQUADS_DIR)

    with open(squad_path, encoding="utf-8") as f:
        squad = list(csv.DictReader(f))

    results = []
    for p in squad:
        marktwert = to_number(p["marktwert"])
        punkte = to_number(p["punkte"])
        punkte_pro_spiel = to_number(p["punkte_pro_spiel"])

        mw_pro_punkt = round(marktwert / punkte) if marktwert and punkte else None
        mw_pro_punkteschnitt = round(marktwert / punkte_pro_spiel) if marktwert and punkte_pro_spiel else None

        results.append({
            "spieler_id": p["spieler_id"],
            "name": p["name"],
            "verein": p["verein"],
            "marktwert": p["marktwert"],
            "punkte": p["punkte"],
            "punkte_pro_spiel": p["punkte_pro_spiel"],
            "mw_pro_punkt": mw_pro_punkt,
            "mw_pro_punkteschnitt": mw_pro_punkteschnitt,
        })

    date_str = os.path.basename(squad_path).removesuffix(".csv")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"marktwert_punkte_verhaeltnis_{date_str}.csv")

    fieldnames = [
        "spieler_id", "name", "verein", "marktwert", "punkte",
        "punkte_pro_spiel", "mw_pro_punkt", "mw_pro_punkteschnitt",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Quelle: {squad_path}\n")
    for r in results:
        print(
            f"{r['name']:<20} | MW: {r['marktwert']:>10} | Pkt: {str(r['punkte']):>4} | "
            f"MW/Pkt: {str(r['mw_pro_punkt']):>9} | MW/Schnitt: {str(r['mw_pro_punkteschnitt']):>9}"
        )

    print(f"\nGespeichert unter: {output_path}")


if __name__ == "__main__":
    main()
