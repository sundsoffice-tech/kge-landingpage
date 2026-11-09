#!/usr/bin/env python3
"""Baut die HTML-Seiten der Landingpage aus einer Schale und je einer Inhaltsdatei.

Warum: Kopf, Fuß, Callbar und Skripte stehen genau einmal in vorlagen/schale.html. Drei Kopien derselben Seite
sind schon einmal auseinandergedriftet (docs/60-LEKTIONEN.md, A2). Die fertigen HTML-Dateien liegen trotzdem
im Repo, weil GitHub Pages sie direkt ausliefert.

Aufruf: python bauen.py            schreibt alle Seiten
        python bauen.py --pruefen  Exit 1, wenn eine Seite im Repo nicht dem Bauergebnis entspricht

NOINDEX: True bis zum Go-Live auf unfall-mg.de (DEPLOY.md), danach False setzen und neu bauen. Der Bau bricht ab,
solange NOINDEX aus ist und konfig.js noch Platzhalter trägt (sonst ginge die Seite ohne Messung in den Index).

Werte, die auf mehreren Seiten stehen, stehen genau einmal hier (WhatsApp, Rückrufzusage, Fotoschalter).
Die FAQPage-Daten (JSON-LD) erzeugt der Bau aus den sichtbaren <details>-Fragen, damit sie wortgleich bleiben.
"""
import html
import json
import pathlib
import re
import sys

HIER = pathlib.Path(__file__).resolve().parent
NOINDEX = True

# WhatsApp: Anzeige und Link aus einer Quelle. Beleg 09.11.2026 an gutachten-es.de: wa.me/491771947271.
WHATSAPP_ANZEIGE = "0177 19 47 271"
WHATSAPP_TEXT = "Hallo%2C%20ich%20hatte%20einen%20Unfall%20und%20schicke%20Fotos%20von%20meinem%20Fahrzeug%20zur%20Ersteinsch%C3%A4tzung."

# Rückrufzusage: steht nur hier. Die Erreichbarkeit ist vom Kunden noch nicht bestätigt (Frage 4 an Herrn Es),
# deshalb ohne Stundenzahl. Nach seiner Bestätigung zum Beispiel:
#   RUECKRUF_WERKTAGS = "innerhalb einer Stunde"
#   RUECKRUF_SONST = "am nächsten Werktag bis 9 Uhr"
RUECKRUF_WERKTAGS = "zeitnah"
RUECKRUF_SONST = "am nächsten Werktag"

# Betriebsfotos: False blendet die Bildplätze (<!--FOTOS--> bis <!--/FOTOS--> in inhalte/) aus, bis echte
# Fotos vom Kunden da sind. True zeigt sie wieder; dann die <img> in den Platzhaltern eintragen.
FOTOS_ZEIGEN = False


def whatsapp_nummer():
    ziffern = re.sub(r"\D", "", WHATSAPP_ANZEIGE)
    if not ziffern.startswith("0"):
        sys.exit(f"WHATSAPP_ANZEIGE muss mit 0 beginnen: {WHATSAPP_ANZEIGE}")
    return "49" + ziffern[1:]


GLOBAL = {
    "wa_link": f"https://wa.me/{whatsapp_nummer()}?text={WHATSAPP_TEXT}",
    "wa_anzeige": WHATSAPP_ANZEIGE,
    "rueckruf_werktags": RUECKRUF_WERKTAGS,
    "rueckruf_sonst": RUECKRUF_SONST,
}


def sperre_noindex():
    """P2: Ohne noindex darf nur gebaut werden, wenn konfig.js echte Werte trägt."""
    if NOINDEX:
        return
    konfig = (HIER / "konfig.js").read_text(encoding="utf-8")
    # Nur die Werte prüfen, nicht die Kommentare (die nennen das Muster "AW-XXXXXXXXXX" als Beispiel).
    werte = re.findall(r'^\s*(?:googleTag|phone_click|whatsapp_click|form_submit):\s*"([^"]*)"', konfig, re.M)
    if len(werte) != 4 or any(not w or re.search(r"AW-X|X{4,}", w) for w in werte):
        sys.exit("NOINDEX ist aus, aber konfig.js trägt noch Platzhalter (AW-X…). Erst Messung eintragen, dann bauen.")


def nur_text(roh):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", roh)).split())


def faq_jsonld(seite):
    """P3: FAQPage aus den sichtbaren Fragen, Antworttext wortgleich mit der Anzeige."""
    paare = re.findall(r'<details>\s*<summary>(.*?)</summary>\s*<div class="antwort">(.*?)</div>\s*</details>', seite, re.S)
    if not paare:
        sys.exit("{{faq_jsonld}} ohne <details>-Fragen")
    zeilen = []
    for frage, antwort in paare:
        eintrag = {"@type": "Question", "name": nur_text(frage),
                   "acceptedAnswer": {"@type": "Answer", "text": nur_text(antwort)}}
        zeilen.append("    " + json.dumps(eintrag, ensure_ascii=False))
    kopf = '<script type="application/ld+json">\n{\n  "@context": "https://schema.org",\n  "@type": "FAQPage",\n  "mainEntity": [\n'
    return kopf + ",\n".join(zeilen) + "\n  ]\n}\n</script>"

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
    if FOTOS_ZEIGEN:
        inhalt = re.sub(r"[ \t]*<!--/?FOTOS-->\n?", "", inhalt)
    else:
        inhalt = re.sub(r"[ \t]*<!--FOTOS-->.*?<!--/FOTOS-->\n?", "", inhalt, flags=re.S)
    # Inhalt zuerst einsetzen, damit seine Platzhalter (WhatsApp, Rückruf) in der Schleife mit ersetzt werden.
    werte = {"inhalt": inhalt.strip()}
    werte.update(meta)
    werte["noindex"] = '<meta name="robots" content="noindex">' if NOINDEX else ""
    werte.update(GLOBAL)
    seite = schale
    for schluessel, wert in werte.items():
        seite = seite.replace("{{" + schluessel + "}}", wert)
    if "{{faq_jsonld}}" in seite:
        seite = seite.replace("{{faq_jsonld}}", faq_jsonld(seite))
    if "{{" in seite:
        sys.exit(f"{name}: Platzhalter offen: {seite[seite.index('{{'):seite.index('{{') + 30]}")
    return seite


def main():
    sperre_noindex()
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
