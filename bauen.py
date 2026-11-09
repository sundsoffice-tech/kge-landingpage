#!/usr/bin/env python3
"""Baut die HTML-Seiten der Landingpage aus einer Schale und je einer Inhaltsdatei.

Warum: Kopf, Fuß, Callbar und Skripte stehen genau einmal in vorlagen/schale.html. Drei Kopien derselben Seite
sind schon einmal auseinandergedriftet (docs/60-LEKTIONEN.md, A2). Die fertigen HTML-Dateien liegen trotzdem
im Repo, weil GitHub Pages sie direkt ausliefert.

Aufruf: python bauen.py            schreibt alle Seiten
        python bauen.py --pruefen  Exit 1, wenn eine Seite im Repo nicht dem Bauergebnis entspricht

NOINDEX: True bis zum Go-Live auf unfall-mg.de (DEPLOY.md), danach False setzen und neu bauen.
"""
import pathlib
import sys

HIER = pathlib.Path(__file__).resolve().parent
NOINDEX = True

SEITEN = {
    "index.html": {
        "titel": "Kfz-Gutachter Mönchengladbach · Unfallgutachten vor Ort · Kfz Gutachter Es",
        "beschreibung": "Kfz-Sachverständiger Cihan Es, Mönchengladbach: Unfallgutachten mit Besichtigung vor Ort oder auf der Hebebühne Karstraße 25. Bei unverschuldetem Unfall zahlt die gegnerische Versicherung das Gutachten. Telefon 02161 622 57 68.",
        "kanonisch": "./",
        "nav": "",
        "skripte": '<script src="formular.js" defer></script>',
    },
    "umland.html": {
        "titel": "Kfz-Gutachter für Viersen, Willich, Neuss, Kaarst, Korschenbroich, Grevenbroich · Kfz Gutachter Es",
        "beschreibung": "Unfall im Umland von Mönchengladbach? Kfz-Sachverständiger Cihan Es kommt zur Besichtigung nach Viersen, Willich, Korschenbroich, Neuss, Kaarst und Grevenbroich. Bei unverschuldetem Unfall zahlt die gegnerische Versicherung das Gutachten.",
        "kanonisch": "umland.html",
        "nav": "",
        "skripte": '<script src="formular.js" defer></script>',
    },
    "ablauf.html": {
        "titel": "So läuft ein Unfallgutachten ab · Kfz Gutachter Es, Mönchengladbach",
        "beschreibung": "Vom Anruf zur Besichtigung zum Gutachten: der Ablauf in drei Schritten, die ersten Schritte direkt nach dem Unfall und was im Gutachten steht. Kfz-Sachverständiger Cihan Es, Mönchengladbach.",
        "kanonisch": "ablauf.html",
        "nav": "index.html",
        "skripte": "",
    },
    "kosten.html": {
        "titel": "Was kostet ein Unfallgutachten? Honorar nach BVSK · Kfz Gutachter Es",
        "beschreibung": "Wer zahlt das Gutachten nach einem Unfall, was bei Teilschuld, Bagatellschaden und Kasko gilt und wie Kfz-Sachverständige nach der BVSK-Honorarbefragung 2024 abrechnen. Kfz Gutachter Es, Mönchengladbach.",
        "kanonisch": "kosten.html",
        "nav": "index.html",
        "skripte": "",
    },
    "nachts-wochenende.html": {
        "titel": "Unfall nachts oder am Wochenende · Kfz Gutachter Es, Mönchengladbach",
        "beschreibung": "Unfall außerhalb der Bürozeiten: was Sie jetzt tun können, wie Sie uns erreichen und wann wir zurückrufen. Kfz-Sachverständiger Cihan Es, Mönchengladbach.",
        "kanonisch": "nachts-wochenende.html",
        "nav": "index.html",
        "skripte": "",
    },
    "impressum.html": {
        "titel": "Impressum · Kfz Gutachter Es, Mönchengladbach",
        "beschreibung": "Anbieterkennzeichnung der Seite von Kfz Gutachter Es, Cihan Es, Mönchengladbach.",
        "kanonisch": "impressum.html",
        "nav": "index.html",
        "skripte": "",
    },
    "datenschutz.html": {
        "titel": "Datenschutzerklärung · Kfz Gutachter Es, Mönchengladbach",
        "beschreibung": "Welche Daten diese Seite verarbeitet: Aufruf, Rückruf-Formular, Anruf, WhatsApp, Google Ads Conversion-Messung mit Einwilligung.",
        "kanonisch": "datenschutz.html",
        "nav": "index.html",
        "skripte": "",
    },
}


def bauen(name, meta):
    schale = (HIER / "vorlagen" / "schale.html").read_text(encoding="utf-8")
    inhalt = (HIER / "inhalte" / name).read_text(encoding="utf-8")
    werte = dict(meta)
    werte["inhalt"] = inhalt.strip()
    werte["noindex"] = '<meta name="robots" content="noindex">' if NOINDEX else ""
    seite = schale
    for schluessel, wert in werte.items():
        seite = seite.replace("{{" + schluessel + "}}", wert)
    if "{{" in seite:
        sys.exit(f"{name}: Platzhalter offen: {seite[seite.index('{{'):seite.index('{{') + 30]}")
    return seite


def main():
    pruefen = "--pruefen" in sys.argv
    abweichungen = 0
    for name, meta in SEITEN.items():
        neu = bauen(name, meta)
        ziel = HIER / name
        if pruefen:
            alt = ziel.read_text(encoding="utf-8") if ziel.exists() else ""
            if alt != neu:
                print(f"ABWEICHUNG {name}")
                abweichungen += 1
        else:
            ziel.write_text(neu, encoding="utf-8", newline="\n")
            print(f"{name}: {len(neu.encode('utf-8'))} Bytes")
    if pruefen:
        print("alle Seiten entsprechen dem Bauergebnis" if not abweichungen else f"{abweichungen} Abweichungen")
        sys.exit(1 if abweichungen else 0)


if __name__ == "__main__":
    main()
