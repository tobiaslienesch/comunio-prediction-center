# Projekt-Steckbrief: Comunio Prediction-Modell

> **Zweck dieser Datei:** Dies ist mein fester Projekt-Kontext für Claude Code. Ich gebe dir diese Datei zu Beginn jeder Session. Beziehe dich immer darauf, damit ich mich nicht wiederholen muss. Ich bin Anfänger ohne Programmier-Erfahrung – erkläre alles verständlich und arbeite in kleinen, überprüfbaren Schritten.

---

## 1. Worum es geht (in einem Satz)
Ich baue ein regelbasiertes Prognose-Modell für den Bundesliga-Fantasy-Manager **Comunio**, das mir wöchentlich die **optimale Aufstellung** und **Transfer-Empfehlungen** (Kaufen / Verkaufen) berechnet und auf einer einfachen **Webseite** anzeigt.

## 2. Wer ich bin (technisches Level)
- Anfänger, kaum Coding-Erfahrung.
- Bitte alles wie für einen Nicht-Programmierer erklären.
- Immer nur einen Schritt auf einmal, jeweils testbar, bevor es weitergeht.

## 3. Zielgruppe & Umfang
- Kleine Gruppe: Freunde / meine Comunio-Liga.
- Kein öffentliches Produkt, keine Nutzer-Accounts nötig.
- Zugriff über einen simplen Link, mobil-tauglich (Handy zuerst).

## 4. Was das Modell ausgeben soll
1. **Empfohlene Startelf diese Woche** (innerhalb meines Budgets / Kaders).
2. **Kauf-Empfehlungen** (unterbewertete / formstarke Spieler).
3. **Verkauf-Empfehlungen** (Spieler mit sinkender Erwartung / überteuert).

## 5. Modell-Ansatz: REGELBASIERT (bewusst kein Machine Learning zum Start)

**Endergebnis:** Eine gespeicherte **Liste ALLER relevanten Spieler**, jeder mit einer **klaren Handlungsempfehlung** (z.B. KAUFEN / HALTEN / VERKAUFEN / BEOBACHTEN). Die Liste muss sich **filtern und sortieren** lassen (nach jedem der Kriterien unten, nach Position, Verein, Preis, Gesamt-Score, Empfehlung).

**Bewertungskriterien je Spieler (regelbasiertes Scoring):**
1. **Form** – Durchschnitt der Comunio-Punkte der letzten 5 Spiele.
2. **Gegnerstärke** – Schwierigkeit der nächsten 4 Spiele (leicht/schwer).
3. **Marktwert-/Punkte-Verhältnis** – wie viel "Punkte pro Euro Marktwert" (Preis-Leistung).
4. **Varianz** – wie stark schwanken die Punkte über das letzte Jahr (konstant vs. Zockerspieler).
5. **Marktwerttrend** – steigt oder fällt der Marktwert (Kauf-/Verkaufsdruck).
6. **Verletzung / Sperre** – aktueller Ausfall-Status (spielt er überhaupt?).
7. **Externe Informationen** – Stammplatz-Wahrscheinlichkeit, Wechselgerüchte, Trainer-Aussagen, Rotation etc. (aus frei verfügbaren Quellen; zum Start ggf. als manuell pflegbares Feld).

**Scoring-Logik:** Jedes Kriterium wird in eine Zahl übersetzt (z.B. 0–100) und gewichtet zu einem **Gesamt-Score** kombiniert. Aus dem Gesamt-Score plus Verletzungs-Status leitet sich automatisch die **Handlungsempfehlung** ab. Die Gewichtungen sollen leicht anpassbar sein (an einer zentralen Stelle im Code), damit ich sie später feinjustieren kann.

**Wichtig für den Anfang:** Kriterien schrittweise einbauen (erst Form, dann eins nach dem anderen), nicht alle auf einmal. Kriterium 7 (externe Infos) ist das schwierigste – zuerst als einfaches manuelles Feld lösen, Automatisierung später.

→ **ML bewusst weglassen.** Erst wenn die regelbasierte Version stabil läuft, denken wir über Lernen aus historischen Daten nach.

## 6. Daten
- **Quelle:** Comunio-Daten (Kader, Marktwerte, Punkte) + eine kostenlose Bundesliga-Daten-Quelle für Spielplan, Gegner, Aufstellungen, Verletzungen.
- **Wichtig:** Comunio hat keine einfache offizielle API. Erste Aufgabe ist daher, gemeinsam zu klären, WIE ich zuverlässig an meine Comunio-Daten komme (z.B. Export, öffentliche Quellen, oder manuelle Eingabe meines Kaders als Übergangslösung).
- Alle Daten werden **live** gezogen und **wöchentlich** aktualisiert.
- **WICHTIG – Datenquellen:** Ich gebe dir die konkreten Quellen für alle Informationen im Laufe des Codings selbst vor. **Suche NICHT eigenständig nach Quellen** und nimm keine an. Wenn dir für einen Schritt eine Quelle fehlt, frag mich und warte auf meine Angabe.

## 7. Automatische Aktualisierung
- Wöchentlicher automatischer Lauf (geplant über GitHub Actions), z.B. jeden Montag.
- Mein Rechner soll dafür NICHT laufen müssen.

## 8. Tech-Stack (alles kostenlos)
- **Sprache:** Python
- **Modell:** regelbasiertes Punkte-Scoring + Aufstellungs-Optimierung
- **Webseite:** schlanke, mobil-taugliche Web-App
- **Code-Verwaltung & Automatisierung:** GitHub + GitHub Actions
- **Hosting:** kostenloses Web-Hosting (Free-Tier)
- **Zielkosten:** 0 EUR

## 9. Randbedingungen
- Kostenlos bleiben (Free-Tiers bevorzugen).
- Token-/aufwandssparend: klein anfangen, ein Feature nach dem anderen fertigstellen.
- Datenquelle zuerst sichern, bevor Zeit ins Modell fliesst.

## 10. Aktueller Stand (hier trage ich den Fortschritt ein)
- [ ] Phase 1: Comunio-Datenquelle geklärt und Test-Abruf funktioniert
- [ ] Phase 2: Regelbasiertes Scoring + Aufstellungs-Empfehlung
- [ ] Phase 3: Webseite zeigt Empfehlungen an
- [ ] Phase 4: Wöchentliche Automatisierung läuft
- [ ] Phase 5: Link geteilt, Feinschliff

## 11. So arbeiten wir zusammen (Regeln für Claude Code)
- Immer einen Schritt, dann kurz erklären, wie ich ihn teste.
- Bei Fehlern: ich kopiere dir die Fehlermeldung + was ich gemacht habe; du gibst mir die Lösung kompakt.
- Keine unnötige Komplexität. Wenn es eine einfachere Lösung gibt, nimm die.
