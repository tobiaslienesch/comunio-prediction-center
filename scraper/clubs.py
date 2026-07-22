"""
Zentrale Liste aller 18 Bundesliga-Vereine mit ihrer Comunio- und
Ligainsider-Kader-URL. Einmal hier gepflegt, damit die Scraper alle
Vereine automatisch durchlaufen koennen (wichtig fuer die
automatisierten GitHub-Actions-Laeufe). Quelle der URLs:
- Comunio: https://stats.comunio.de/toplist/clubmv-Marktwerte_Top_Clubs
- Ligainsider: https://www.ligainsider.de/
"""

CLUBS = [
    {
        "name": "1. FC Bayern München",
        "comunio_url": "https://stats.comunio.de/squad/1-FC+Bayern+München",
        "ligainsider_url": "https://www.ligainsider.de/fc-bayern-muenchen/1/kader/",
    },
    {
        "name": "Borussia Dortmund",
        "comunio_url": "https://stats.comunio.de/squad/5-Borussia+Dortmund",
        "ligainsider_url": "https://www.ligainsider.de/borussia-dortmund/14/kader/",
    },
    {
        "name": "RB Leipzig",
        "comunio_url": "https://stats.comunio.de/squad/92-RB+Leipzig",
        "ligainsider_url": "https://www.ligainsider.de/rb-leipzig/1311/kader/",
    },
    {
        "name": "Bayer 04 Leverkusen",
        "comunio_url": "https://stats.comunio.de/squad/8-Bayer+04+Leverkusen",
        "ligainsider_url": "https://www.ligainsider.de/bayer-04-leverkusen/4/kader/",
    },
    {
        "name": "VfB Stuttgart",
        "comunio_url": "https://stats.comunio.de/squad/14-VfB+Stuttgart",
        "ligainsider_url": "https://www.ligainsider.de/vfb-stuttgart/12/kader/",
    },
    {
        "name": "TSG Hoffenheim",
        "comunio_url": "https://stats.comunio.de/squad/62-TSG+Hoffenheim",
        "ligainsider_url": "https://www.ligainsider.de/tsg-hoffenheim/10/kader/",
    },
    {
        "name": "Sport-Club Freiburg",
        "comunio_url": "https://stats.comunio.de/squad/21-Sport-Club+Freiburg",
        "ligainsider_url": "https://www.ligainsider.de/sc-freiburg/18/kader/",
    },
    {
        "name": "Eintracht Frankfurt",
        "comunio_url": "https://stats.comunio.de/squad/9-Eintracht+Frankfurt",
        "ligainsider_url": "https://www.ligainsider.de/eintracht-frankfurt/3/kader/",
    },
    {
        "name": "FC Augsburg",
        "comunio_url": "https://stats.comunio.de/squad/68-FC+Augsburg",
        "ligainsider_url": "https://www.ligainsider.de/fc-augsburg/21/kader/",
    },
    {
        "name": "1. FSV Mainz 05",
        "comunio_url": "https://stats.comunio.de/squad/18-1.+FSV+Mainz+05",
        "ligainsider_url": "https://www.ligainsider.de/1-fsv-mainz-05/17/kader/",
    },
    {
        "name": "1. FC Union Berlin",
        "comunio_url": "https://stats.comunio.de/squad/109-1.+FC+Union+Berlin",
        "ligainsider_url": "https://www.ligainsider.de/1-fc-union-berlin/1246/kader/",
    },
    {
        "name": "Borussia M'gladbach",
        "comunio_url": "https://stats.comunio.de/squad/3-Borussia+M'gladbach",
        "ligainsider_url": "https://www.ligainsider.de/borussia-moenchengladbach/5/kader/",
    },
    {
        "name": "Hamburger SV",
        "comunio_url": "https://stats.comunio.de/squad/4-Hamburger+SV",
        "ligainsider_url": "https://www.ligainsider.de/hamburger-sv/9/kader/",
    },
    {
        "name": "1. FC Köln",
        "comunio_url": "https://stats.comunio.de/squad/13-1.+FC+Köln",
        "ligainsider_url": "https://www.ligainsider.de/1-fc-koeln/15/kader/",
    },
    {
        "name": "SV Werder Bremen",
        "comunio_url": "https://stats.comunio.de/squad/6-SV+Werder+Bremen",
        "ligainsider_url": "https://www.ligainsider.de/sv-werder-bremen/2/kader/",
    },
    {
        "name": "FC Schalke 04",
        "comunio_url": "https://stats.comunio.de/squad/10-FC+Schalke+04",
        "ligainsider_url": "https://www.ligainsider.de/fc-schalke-04/13/kader/",
    },
    {
        "name": "SV Elversberg",
        "comunio_url": "https://stats.comunio.de/squad/118-SV+Elversberg",
        "ligainsider_url": "https://www.ligainsider.de/sv-07-elversberg/1331/kader/",
    },
    {
        "name": "SC Paderborn",
        "comunio_url": "https://stats.comunio.de/squad/81-SC+Paderborn",
        "ligainsider_url": "https://www.ligainsider.de/sc-paderborn-07/1249/kader/",
    },
]
