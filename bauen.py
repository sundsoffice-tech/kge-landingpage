#!/usr/bin/env python3
"""Baut die HTML-Seiten der Landingpage aus einer Schale und je einer Inhaltsdatei.

Warum: Kopf, Fuß, Callbar und Skripte stehen genau einmal in vorlagen/schale.html. Drei Kopien derselben Seite
sind schon einmal auseinandergedriftet (docs/60-LEKTIONEN.md, A2). Die fertigen HTML-Dateien liegen trotzdem
im Repo, weil sie ohne Bauschritt ausgeliefert werden (sunds-hub, ausrollen.sh; siehe DEPLOY.md).

Aufruf: python bauen.py            schreibt alle Seiten
        python bauen.py --pruefen  Exit 1, wenn eine Seite im Repo nicht dem Bauergebnis entspricht

NOINDEX: True bis zum Go-Live auf unfall-mg.de (DEPLOY.md), danach False setzen und neu bauen. Der Bau bricht ab,
solange NOINDEX aus ist und konfig.js noch Platzhalter trägt (sonst ginge die Seite ohne Messung in den Index).

Werte, die auf mehreren Seiten stehen, stehen genau einmal hier (WhatsApp, Rückrufzusage, Fotoschalter).
Die FAQPage-Daten (JSON-LD) erzeugt der Bau aus den sichtbaren <details>-Fragen, damit sie wortgleich bleiben.
"""
import datetime
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
# deshalb ohne Stundenzahl und ohne Uhrzeitversprechen. RUECKRUF_SONST hängt an den angezeigten Zeiten, nicht am
# Werktag (Samstag ist rechtlich Werktag, im Alltag nicht; Branchenkenner 09.11.2026). Der Satz „Rückruf in diesen
# Zeiten {werktags}, sonst {sonst}.“ steht nur noch im Hero (Start, Umland), im Fuß und auf der Nachtseite; sonst nennt
# die Seite die Uhrzeiten selbst, damit dieselbe Wendung je Seite höchstens zweimal steht (Künstler Runde 3, Ä1).
# Nach Bestätigung zum Beispiel RUECKRUF_WERKTAGS = "innerhalb einer Stunde".
RUECKRUF_WERKTAGS = "zeitnah"
RUECKRUF_SONST = "sobald das Telefon wieder besetzt ist"

# Bildplätze: jeder Platz ist einzeln schaltbar. Ein Platz erscheint genau dann, wenn hier Datei, alt-Text, Maße und
# Bildnachweis eingetragen sind und die Datei unter bilder/ liegt; sonst fehlt seine Zeile ganz (kein Kasten, kein
# „Foto folgt“). In inhalte/ steht je Platz nur der Platzhalter {{bild_<name>}}. FOTOS_ZEIGEN ist der Hauptschalter:
# False blendet alle Bilder und die Bildnachweise aus. Ist ein Platz eingetragen, aber unvollständig, bricht
# python bauen.py ab (sperre_bilder, Zeuge G12), damit kein Bild still fehlt. Die Bildnachweise der gezeigten Plätze erscheinen
# im Impressum. „Symbolbild“ steht bei gekauften oder freien Bildern, die nicht den Betrieb zeigen; bei einem echten
# Foto des Betriebs bleibt die Unterschrift leer. vorrang=True (nur das Bild oben auf der Startseite) lädt das Bild
# bevorzugt, alle anderen laden erst beim Heranscrollen.
FOTOS_ZEIGEN = True
# Richtung R1 „Nah dran“ (24.11.2026): die Schadenfotos sind KI-erzeugte Bilder (ChatGPT über Codex), alle im selben
# Bildlook (Werkzeug _bildroh/bildlook.py im Arbeitsbaum, nicht ausgeliefert). Jedes KI-Bild steht im Bildnachweis des
# Impressums. Ein Schild am Bild gibt es seit Fabrices Wort vom 24.11.2026 nicht mehr („ki erzeugtes bild nicht schreiben
# mein wort“, gegen die Auflage der Rechtsrolle, Nachtrag 01:55).
# Zusätzliche, freiwillige Felder je Platz:
#   breiten  Liste der Breiten in Pixeln; neben datei (…-<breite>.webp) liegen die schmaleren Dateien, daraus srcset
#   sizes    sizes-Angabe zum srcset (Vorgabe 100vw)
#   schmal   eigener Anschnitt für schmale Fenster: datei, breiten, breite, hoehe, medien (picture/source)
#   ki       True: mit KI erzeugt; der Nachweis muss „mit KI erzeugt“ nennen (sonst bricht der Bau ab)
#   klasse   zusätzliche Klasse der figure (buehne-bild, strecke-bild)
KI_KENNWORT = "mit KI erzeugt"
KI_NACHWEIS = ("mit KI erzeugt (ChatGPT, OpenAI) am 24.11.2026 für diese Seite, im Bildlook der Seite "
               "nachbearbeitet")
BILDER = {
    # Startseite, Bühne über die ganze erste Ansicht: Messung an einer Delle im Abendlicht.
    "start": {"datei": "bilder/r2-messung-1536.webp", "breiten": [768, 1280, 1536],
              "schmal": {"datei": "bilder/r2-messung-hoch-864.webp", "breiten": [432, 864], "breite": 864,
                         "hoehe": 1536, "medien": "(max-width: 699px)"},
              "alt": "Eine Hand setzt ein Lackschichtdickenmessgerät an der hinteren Seitenwand auf, die Spiegelung "
                     "knickt an der Delle ab",
              "breite": 1536, "hoehe": 864, "unterschrift": "", "ki": True,
              "klasse": "buehne-bild", "nachweis": "Startseite, Messung an einer Delle: " + KI_NACHWEIS,
              "vorrang": True},
    # Nach dem Unfall, vor „An der Unfallstelle“: leer, 16:9.
    "unfall": {"datei": "", "alt": "", "breite": 0, "hoehe": 0, "unterschrift": "", "nachweis": ""},
    # Wer zahlt?, Zeile „Kleiner Schaden“: verdeckter Schaden hinter der abgenommenen Stoßstange.
    "streifschaden": {"datei": "bilder/r1-verdeckt-1536.webp", "breiten": [768, 1280, 1536],
                      "sizes": "(min-width: 900px) 60vw, 100vw",
                      "alt": "Abgenommene Stoßstange, dahinter ein zerdrückter Pralldämpfer und ein gebrochener Halter",
                      "breite": 1536, "hoehe": 1024,
                      "unterschrift": "Von außen kaum ein Kratzer, dahinter ein zerdrückter Pralldämpfer.",
                      "ki": True, "klasse": "strecke-bild",
                      "nachweis": "Seite „Wer zahlt?“, verdeckter Schaden hinter der Stoßstange: " + KI_NACHWEIS},
    # R1 schlank (24.11.2026): Lackriss, die vier Ablaufbilder (Anruf, Werkstatt, Gutachten, Versand), das
    # Unterboden-Vollbild der Kostenseite und das Münster-Foto (Einsatzgebiet) sind aus der Erzeugung genommen. Die
    # Dateien liegen weiter unter bilder/ (r3-lackriss, r2-anruf, r2-werkstatt, r3-gutachten, r2-versand, r1-unterboden,
    # r1-muenster), werden aber nicht mehr geladen und stehen nicht mehr im Bildnachweis.
    # Einsatzgebiet, Abschnitt Hebebühne: leer, 16:9.
    "hebebuehne": {"datei": "", "alt": "", "breite": 0, "hoehe": 0, "unterschrift": "", "nachweis": ""},
    # Wer zahlt?: Kopf ohne Bild seit R1 schlank; r1-umschlag wird nicht mehr geladen.
}
# Satz vor den Nachweiszeilen im Impressum (Rechtsnachtrag 01:55; seit 24.11.2026 ohne Bezug auf ein Schild am Bild).
NACHWEIS_SATZ = ("Die Fotos auf dieser Seite sind mit KI erzeugte Beispielbilder. "
                 "Sie zeigen keine Fälle, Personen oder Räume des Büros.")
# Ordner, in dem bilder/ liegt; der Zeuge setzt ihn auf einen eigenen Ordner.
BILDWURZEL = HIER

# Bewertung im Hero (Conversion-Prüfung 19.11.2026, O1; Wortlaut nach Wettbewerbsrecht vorab 20.11.2026, Nr. 1):
# ein Kasten im Hero der Startseite. Im HTML steht er vor der Namenszeile zwischen h1 und Anrufknopf (Platzhalter
# vertrauen), stil.css ordnet ihn per order hinter den Knopf. Die Sternchenerklärung, auf die sich die Vorgabe vom
# 20.11.2026 bezog, gibt es seit dem 23.11.2026 nicht mehr: Lage vor dem Einschalten ansehen und neu abstimmen.
# Die Zeile ist ganz ein Link aufs Google-Profil, der Hinweis nach § 5b Abs. 3 UWG steht direkt darunter, ohne Klick
# und in 16 px. Keine Sternegrafik.
# Vorgabe AUS. Vor dem Einschalten alle fünf Werte am Profil neu ablesen (SEIT = Jahr der ältesten Bewertung,
# STAND = Tag des Ablesens) und BEWERTUNG_LINK auf die echte Profiladresse setzen (heute nur eine Kartensuche).
# Der Bau bricht ab, wenn der Schalter AN ist und ein Wert leer ist, SEIT keine Jahreszahl von 2005 bis heute ist,
# der Stand in der Zukunft liegt, der Link keine Profiladresse ist (nur https://g.page/…, https://maps.app.goo.gl/…
# oder https://www.google.com/maps/place/…; die Kartensuche von heute bricht also ab) oder ein Beleg fehlt
# (BEWERTUNG_KUNDENBELEG, Bildschirmfoto belege/bewertung-JJJJ-MM-TT.png zum Stand). Ist der Stand älter als 14 Tage,
# baut er OHNE Kasten und meldet „BEWERTUNG VERALTET“ (Spieltheoretiker r2, M3). Die 14 Tage gelten nur beim Bauen:
# Die ausgelieferte Seite altert weiter (DEPLOY.md, „Bewertung und Name“).
BEWERTUNG_ZEIGEN = False
BEWERTUNG_NOTE = "4,9"            # Stand 09.11.2026 laut Hausbefund, nicht neu abgelesen
BEWERTUNG_ANZAHL = "48"           # Stand 09.11.2026 laut Hausbefund, nicht neu abgelesen
BEWERTUNG_SEIT = ""               # Jahr der ältesten Bewertung, noch nicht abgelesen
BEWERTUNG_STAND = "09.11.2026"    # TT.MM.JJJJ, Tag des Ablesens
BEWERTUNG_LINK = "https://www.google.com/maps/search/?api=1&query=Kfz+Gutachter+Es+M%C3%B6nchengladbach"
BEWERTUNG_HINWEIS = "Aus unserem Google-Profil. Wir prüfen nicht, ob die Verfasser unsere Leistung genutzt haben."
# Vorgangsnummer der schriftlichen Freigabe des Kunden für den Kasten (acht Zeichen), leer bis sie vorliegt.
BEWERTUNG_KUNDENBELEG = ""
BEWERTUNG_HOECHSTALTER_TAGE = 14
BEWERTUNG_SEIT_FRUEHESTENS = 2005
# Belege zum Stand, vom Ausliefern ausgenommen (.gitattributes): belege/bewertung-JJJJ-MM-TT.png
BELEGE = HIER / "belege"
PNG_KOPF = b"\x89PNG\r\n\x1a\n"
BEWERTUNG_PROFIL_FORM = r"https://(?:g\.page/|maps\.app\.goo\.gl/|www\.google\.com/maps/place/)[^\s\"'<>]+"

# Name im Hero, eigener Schalter, an derselben Stelle, außerhalb des Bewertungskastens. Vorgabe AN seit 20.11.2026:
# „Ihr Sachverständiger: Cihan Es“ ist ohne Bestätigung zulässig (Wettbewerbsrecht vorab Nr. 2), die Marketingrolle
# verlangt den Namen im ersten Bildschirm. „Sie sprechen direkt mit Cihan Es“ erst nach Bestätigung des Kunden.
NAME_ZEIGEN = True
NAME_TEXT = "Ihr Sachverständiger: Cihan Es"


def whatsapp_nummer():
    ziffern = re.sub(r"\D", "", WHATSAPP_ANZEIGE)
    if not ziffern.startswith("0"):
        sys.exit(f"WHATSAPP_ANZEIGE muss mit 0 beginnen: {WHATSAPP_ANZEIGE}")
    return "49" + ziffern[1:]


# Anrufzeile im Kopf der Unterseiten: Nummer als Text und als Link, steht nur hier. Auf der Startseite trägt der
# Knopf im Hero die Nummer. Große Anrufknöpfe am Ende der Abschnitte gibt es seit dem Umbau vom 23.11.2026 nicht mehr:
# Anrufstellen sind Kopf, ein Knopf oder diese Zeile oben, die Anrufleiste am Handy und der Kontaktabschnitt.
RUF_ZEILE = ('<p class="ruf"><a href="tel:+4921616888691" data-messung="phone_click"><svg><use href="#i-tel"/></svg>'
             '02161 688 86 91</a><span>Mo bis Fr 8 bis 18 Uhr, Sa 9 bis 14 Uhr</span></p>')

# Menü: eine Liste für die Kopfzeile (ab 1024 px) und das Handy-Menü (details, ohne JavaScript). Die Punkte führen
# auf Seiten, nicht auf Sprungmarken der Startseite. Die Adresse umland.html bleibt, weil Anzeigen darauf zeigen;
# sichtbar heißt die Seite Einsatzgebiet.
MENUE = [("./", "Start"), ("ablauf.html", "Nach dem Unfall"), ("kosten.html", "Wer zahlt?"),
         ("umland.html", "Einsatzgebiet"), ("kontakt.html", "Kontakt und Anfahrt")]


def menue(name, mit_start, einzug):
    """Die Links des Menüs für die Seite name; die eigene Seite trägt aria-current."""
    eigen = "./" if name == "index.html" else name
    zeilen = []
    for ziel, text in MENUE:
        if ziel == "./" and not mit_start:
            continue
        aktuell = ' aria-current="page"' if ziel == eigen else ""
        zeilen.append(f'<a href="{ziel}"{aktuell}>{html.escape(text)}</a>')
    return ("\n" + " " * einzug).join(zeilen)


GLOBAL = {
    "ruf": RUF_ZEILE,
    "wa_link": f"https://wa.me/{whatsapp_nummer()}?text={WHATSAPP_TEXT}",
    "wa_anzeige": WHATSAPP_ANZEIGE,
    "rueckruf_werktags": RUECKRUF_WERKTAGS,
    "rueckruf_sonst": RUECKRUF_SONST,
}


def konfig_fehler(konfig):
    """Prüft den Text von konfig.js; gibt die Fehlermeldung zurück oder None. Zeuge: pruefen/zeuge_bauen.py."""
    # Nur die Werte prüfen, nicht die Kommentare (die nennen das Muster "AW-XXXXXXXXXX" als Beispiel).
    werte = re.findall(r'^\s*(?:googleTag|phone_click|whatsapp_click|form_submit):\s*"([^"]*)"', konfig, re.M)
    if len(werte) != 4 or any(not w or re.search(r"AW-X|X{4,}", w) for w in werte):
        return "NOINDEX ist aus, aber konfig.js trägt noch Platzhalter (AW-X…). Erst Messung eintragen, dann bauen."
    # website_call: leer ist erlaubt und heißt „kein Nummerntausch“. Gesetzt muss es ein echtes Label sein, sonst
    # schaltete ein stehengebliebener Platzhalter oder Tippfehler die Anrufmessung stumm ab (Programmierer r1, Fund 7).
    anruf = re.findall(r'^\s*website_call:\s*"([^"]*)"', konfig, re.M)
    if len(anruf) != 1:
        return "konfig.js: labels.website_call fehlt oder steht mehrfach (leer lassen heißt: kein Nummerntausch)."
    if anruf[0] and (re.search(r"X{4,}", anruf[0]) or not re.fullmatch(r"[A-Za-z0-9_-]+", anruf[0])):
        return ("NOINDEX ist aus, aber labels.website_call in konfig.js ist kein Label (Platzhalter oder unzulässige "
                "Zeichen). Echtes Label eintragen oder leer lassen (leer heißt: kein Nummerntausch).")
    return None


def noindex_fehler(konfig):
    """P2: Ohne noindex darf nur gebaut werden, wenn konfig.js echte Werte trägt und eine eingeschaltete Bewertung
    nicht auf die Kartensuche zeigt. Gibt die Fehlermeldung zurück oder None. Zeuge: pruefen/zeuge_bauen.py."""
    fehler = konfig_fehler(konfig)
    if fehler:
        return fehler
    # Doppelt zur Profilform in bewertung_fehler: Diese Sperre bleibt, falls jemand die Profilform lockert.
    if BEWERTUNG_ZEIGEN and "/maps/search/" in BEWERTUNG_LINK:
        return ("NOINDEX ist aus und BEWERTUNG_ZEIGEN an, aber BEWERTUNG_LINK ist noch die Kartensuche. "
                "Echte Profiladresse eintragen oder BEWERTUNG_ZEIGEN = False.")
    return None


def sperre_noindex():
    if NOINDEX:
        return
    fehler = noindex_fehler((HIER / "konfig.js").read_text(encoding="utf-8"))
    if fehler:
        sys.exit(fehler)


def bewertung_fehler(heute=None):
    """Gibt die Fehlermeldung zurück oder None. Nur bei BEWERTUNG_ZEIGEN = True geprüft. Zeuge: pruefen/zeuge_bauen.py
    mit festem heute."""
    heute = heute or datetime.date.today()
    werte = {"NOTE": BEWERTUNG_NOTE, "ANZAHL": BEWERTUNG_ANZAHL, "SEIT": BEWERTUNG_SEIT,
             "STAND": BEWERTUNG_STAND, "LINK": BEWERTUNG_LINK, "KUNDENBELEG": BEWERTUNG_KUNDENBELEG}
    leer = [k for k, v in werte.items() if not str(v).strip()]
    if leer:
        return f"BEWERTUNG_ZEIGEN ist an, aber leer: {', '.join('BEWERTUNG_' + k for k in leer)}"
    if not re.fullmatch(r"[A-Za-z0-9_-]{8}", BEWERTUNG_KUNDENBELEG) or re.search(r"X{4,}", BEWERTUNG_KUNDENBELEG, re.I):
        return (f"BEWERTUNG_KUNDENBELEG ist keine Vorgangsnummer (acht Zeichen aus Buchstaben, Ziffern, - und _, kein "
                f"Platzhalter): {BEWERTUNG_KUNDENBELEG!r}")
    seit = BEWERTUNG_SEIT.strip()
    if not (re.fullmatch(r"\d{4}", seit) and BEWERTUNG_SEIT_FRUEHESTENS <= int(seit) <= heute.year):
        return (f"BEWERTUNG_SEIT ist keine Jahreszahl von {BEWERTUNG_SEIT_FRUEHESTENS} bis {heute.year}: "
                f"{BEWERTUNG_SEIT!r} (Jahr der ältesten Bewertung am Profil ablesen)")
    try:
        stand = datetime.datetime.strptime(BEWERTUNG_STAND, "%d.%m.%Y").date()
    except ValueError:
        return f"BEWERTUNG_STAND ist kein Datum TT.MM.JJJJ: {BEWERTUNG_STAND}"
    if (heute - stand).days < 0:
        return f"BEWERTUNG_STAND {BEWERTUNG_STAND} liegt in der Zukunft: Stand ist der Tag des Ablesens."
    if not re.fullmatch(BEWERTUNG_PROFIL_FORM, BEWERTUNG_LINK):
        return (f"BEWERTUNG_LINK ist keine Profiladresse (nur https://g.page/…, https://maps.app.goo.gl/… oder "
                f"https://www.google.com/maps/place/…): {BEWERTUNG_LINK}")
    foto = bewertung_foto(stand)
    try:
        echt = foto.read_bytes()[:8] == PNG_KOPF
    except OSError:
        echt = False
    if not echt:
        return (f"Beleg fehlt: {foto} (Bildschirmfoto des Google-Profils vom Tag des Stands, PNG). "
                "Erst ablesen und ablegen, dann einschalten.")
    return None


def bewertung_foto(stand):
    """Pfad des Belegs zum Stand: belege/bewertung-JJJJ-MM-TT.png (Spieltheoretiker r2, M3)."""
    return BELEGE / f"bewertung-{stand:%Y-%m-%d}.png"


def bewertung_veraltet(heute=None):
    """Stand älter als BEWERTUNG_HOECHSTALTER_TAGE: Der Bau lässt den Kasten weg, statt abzubrechen (M3 e). Ein Abbruch
    träfe den nächsten fremden Bau und legte „Stand = heute“ ohne Ablesen nahe. Nur nach bewertung_fehler() rufen."""
    stand = datetime.datetime.strptime(BEWERTUNG_STAND, "%d.%m.%Y").date()
    return ((heute or datetime.date.today()) - stand).days > BEWERTUNG_HOECHSTALTER_TAGE


def bewertung_meldung(heute=None):
    """Die laute Zeile für Bau und --pruefen, oder None."""
    if BEWERTUNG_ZEIGEN and not bewertung_fehler(heute) and bewertung_veraltet(heute):
        return f"BEWERTUNG VERALTET, Kasten weggelassen: Stand {BEWERTUNG_STAND}"
    return None


def bewertung_zeile():
    """Die Zeile im Kasten, wortgleich mit der Seite. DEPLOY.md, Schritt 2, gibt sie der Wörtersperre als Ausnahme
    (python bauen.py --bewertungszeile), damit nur genau dieser belegte Satz durchgeht und keine andere „4,9“."""
    return (f"{BEWERTUNG_NOTE} von 5 bei Google, {BEWERTUNG_ANZAHL} Bewertungen seit {BEWERTUNG_SEIT}, "
            f"Stand {BEWERTUNG_STAND}")


def vertrauen():
    """O1: Bewertungskasten und Namenszeile im Hero der Startseite (zwischen h1 und Knopf), je mit eigenem Schalter. Leer, wenn beide
    aus sind; bauen() nimmt dann die ganze Zeile mit dem Platzhalter heraus."""
    e = html.escape
    teile = []
    if BEWERTUNG_ZEIGEN:
        fehler = bewertung_fehler()
        if fehler:
            sys.exit(fehler)
    if BEWERTUNG_ZEIGEN and not bewertung_veraltet():
        teile.append(f'<div class="bewertung"><a href="{e(BEWERTUNG_LINK)}" rel="noopener">{e(bewertung_zeile())}</a>'
                     f'<p>{e(BEWERTUNG_HINWEIS)}</p></div>')
    if NAME_ZEIGEN:
        teile.append(f'<p class="name-zeile">{e(NAME_TEXT)}</p>')
    return "\n      ".join(teile)


def bild_fehler(platz):
    """Prüft einen Bildplatz aus BILDER; gibt die Fehlermeldung zurück oder None. Ein leerer Platz (keine Datei
    eingetragen) ist kein Fehler, er erscheint einfach nicht. Zeuge: pruefen/zeuge_bauen.py, G1 bis G6."""
    b = BILDER[platz]
    datei = b["datei"]
    if not datei:
        return None
    if not str(b["alt"]).strip():
        return f"Bildplatz {platz}: alt-Text fehlt"
    if not (isinstance(b["breite"], int) and isinstance(b["hoehe"], int) and b["breite"] > 0 and b["hoehe"] > 0):
        return f"Bildplatz {platz}: Breite und Höhe fehlen"
    if not str(b["nachweis"]).strip():
        return f"Bildplatz {platz}: Bildnachweis fehlt"
    if not (BILDWURZEL / datei).is_file():
        return f"Bildplatz {platz}: Datei {datei} fehlt"
    for weitere in varianten(b):
        if not (BILDWURZEL / weitere).is_file():
            return f"Bildplatz {platz}: Datei {weitere} fehlt"
    if b.get("ki") and KI_KENNWORT not in b["nachweis"]:
        return f"Bildplatz {platz}: KI-Bild, der Nachweis nennt „{KI_KENNWORT}“ nicht"
    return None


def stufen(datei, breiten):
    """Die Dateien eines Bildes je Breite: aus bilder/x-1536.webp und [768, 1536] wird [(bilder/x-768.webp, 768), …].
    Ohne Breitenangabe im Namen bleibt die Datei allein."""
    m = re.match(r"^(.*)-\d+(\.\w+)$", datei)
    if not m:
        return [(datei, 0)]
    return [(f"{m.group(1)}-{w}{m.group(2)}", w) for w in breiten]


def varianten(b):
    """Alle Dateien eines Platzes außer datei selbst (Breitenstufen und schmaler Anschnitt)."""
    dateien = [d for d, _ in stufen(b["datei"], b.get("breiten") or [])]
    s = b.get("schmal")
    if s:
        dateien += [s["datei"]] + [d for d, _ in stufen(s["datei"], s.get("breiten") or [])]
    return [d for d in dict.fromkeys(dateien) if d != b["datei"]]


def bild_html(platz):
    """Die <figure>-Zeile eines Bildplatzes, oder leer: Hauptschalter aus, Platz nicht belegt oder unvollständig."""
    b = BILDER[platz]
    if not FOTOS_ZEIGEN or not b["datei"] or bild_fehler(platz):
        return ""
    e = html.escape
    laden = 'fetchpriority="high"' if b.get("vorrang") else 'loading="lazy"'
    unter = f'<figcaption>{e(b["unterschrift"])}</figcaption>' if b["unterschrift"] else ""
    klasse = f'bild {e(b["klasse"])}' if b.get("klasse") else "bild"
    satz = ""
    if b.get("breiten"):
        satz = (f' srcset="{e(", ".join(f"{d} {w}w" for d, w in stufen(b["datei"], b["breiten"])))}"'
                f' sizes="{e(b.get("sizes", "100vw"))}"')
    bild = (f'<img src="{e(b["datei"])}" alt="{e(b["alt"])}" width="{b["breite"]}" '
            f'height="{b["hoehe"]}"{satz} {laden}>')
    s = b.get("schmal")
    if s:
        quellen = ", ".join(f"{d} {w}w" for d, w in stufen(s["datei"], s.get("breiten") or [s["breite"]]))
        bild = (f'<picture><source media="{e(s["medien"])}" srcset="{e(quellen)}" sizes="100vw" '
                f'width="{s["breite"]}" height="{s["hoehe"]}">{bild}</picture>')
    return f'<figure class="{klasse}">{bild}{unter}</figure>'


def sperre_bilder():
    """Ein eingetragener, aber unvollständiger Bildplatz bricht den Bau ab (bauen() selbst lässt ihn nur weg, damit
    der Zeuge Seiten bauen kann). Steht in main."""
    if not FOTOS_ZEIGEN:
        return
    for platz in BILDER:
        meldung = bild_fehler(platz)
        if meldung:
            sys.exit(meldung)


def bildnachweise():
    """Abschnitt fürs Impressum: je gezeigtem Bild eine Zeile. Leer, wenn kein Bild gezeigt wird; bauen() nimmt dann
    die Zeile mit dem Platzhalter heraus."""
    zeilen = [html.escape(BILDER[platz]["nachweis"].strip()) for platz in BILDER if bild_html(platz)]
    if not zeilen:
        return ""
    ki = any(BILDER[p].get("ki") for p in BILDER if bild_html(p))
    satz = f"\n    <p>{html.escape(NACHWEIS_SATZ)}</p>" if ki else ""
    return "<h2>Bildnachweise</h2>" + satz + "\n    <p>" + "<br>".join(zeilen) + "</p>"


def ohne_kommentare(text):
    """Interne Notizen (<!-- ... -->) gehören in die Quelle, nicht in die ausgelieferte Seite (Conversion-Prüfung
    19.11.2026, Nebenfund). Erst Zeilen, die nur aus einem Kommentar bestehen (auch über mehrere Zeilen), samt
    Zeilenende, dann jeder übrige Kommentar für sich. Ein Kommentar endet am ersten -->: Der Ausdruck (?:(?!-->).)*
    läuft nie über ein --> hinweg, so bleibt Inhalt zwischen zwei Kommentaren stehen (Programmierer r2, F3). Ein nicht
    geschlossenes <!-- bleibt stehen und bricht den Bau an der Kommentarsperre in bauen() ab."""
    text = re.sub(r"^[ \t]*<!--(?:(?!-->).)*-->[ \t]*\n", "", text, flags=re.S | re.M)
    return re.sub(r"[ \t]*<!--(?:(?!-->).)*-->", "", text, flags=re.S)


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
        "titel": "Kfz-Gutachter in Mönchengladbach: Cihan Es, Unfallgutachten vor Ort | Kfz Gutachter Es",
        "beschreibung": "Cihan Es, Kfz-Sachverständiger für Unfallschäden in Mönchengladbach. Besichtigung dort, wo Ihr Fahrzeug steht, oder auf der Hebebühne an der Karstraße 25. Büro in Rheydt. Telefon 02161 688 86 91.",
        "kanonisch": "./",
        "skripte": '<script src="formular.js" defer></script>',
    },
    "ablauf.html": {
        "titel": "Nach dem Unfall: erste Schritte und Weg zum Gutachten | Kfz Gutachter Es",
        "beschreibung": "Was Sie an der Unfallstelle tun sollten, was Sie zur Besichtigung brauchen, wie ein Unfallgutachten entsteht und was darin steht. Kfz-Sachverständiger Cihan Es, Mönchengladbach.",
        "kanonisch": "ablauf.html",
        "skripte": "",
    },
    "kosten.html": {
        "titel": "Wer zahlt das Unfallgutachten? Kosten und Honorar | Kfz Gutachter Es",
        "beschreibung": "Wer das Gutachten nach einem Unfall zahlt, was bei Teilschuld, kleinem Schaden und Kasko gilt, was Ihnen außerdem zusteht und wie Sachverständige nach der BVSK-Honorarbefragung 2024 abrechnen.",
        "kanonisch": "kosten.html",
        "skripte": "",
    },
    "umland.html": {
        "titel": "Kfz-Gutachter für Viersen, Neuss und Kaarst | Kfz Gutachter Es",
        "beschreibung": "Kfz-Sachverständiger Cihan Es aus Mönchengladbach besichtigt Unfallfahrzeuge in Viersen, Neuss und Kaarst, ebenso in Willich, Korschenbroich und Grevenbroich: zu Hause, beim Arbeitgeber oder in der Werkstatt Ihrer Wahl.",
        "kanonisch": "umland.html",
        "skripte": "",
    },
    "kontakt.html": {
        "titel": "Kontakt und Anfahrt | Kfz Gutachter Es, Mönchengladbach",
        "beschreibung": "Telefon 02161 688 86 91, WhatsApp und Rückruf. Besichtigung mit Hebebühne an der Karstraße 25 in Mönchengladbach, Büro an der Dahlener Straße 286 in Rheydt. Telefonzeiten Mo bis Fr 8 bis 18 Uhr, Sa 9 bis 14 Uhr.",
        "kanonisch": "kontakt.html",
        "skripte": '<script src="formular.js" defer></script>',
    },
    "nachts-wochenende.html": {
        "titel": "Unfall abends oder am Wochenende | Kfz Gutachter Es, Mönchengladbach",
        "beschreibung": "Unfall außerhalb der Telefonzeiten: was Sie jetzt schon tun können, wie Sie das Büro erreichen und wann der Rückruf kommt. Kfz-Sachverständiger Cihan Es, Mönchengladbach.",
        "kanonisch": "nachts-wochenende.html",
        "skripte": "",
    },
    "impressum.html": {
        "titel": "Impressum | Kfz Gutachter Es, Mönchengladbach",
        "beschreibung": "Anbieterkennzeichnung der Seite von Kfz Gutachter Es, Cihan Es, Mönchengladbach.",
        "kanonisch": "impressum.html",
        "skripte": "",
    },
    "datenschutz.html": {
        "titel": "Datenschutzerklärung | Kfz Gutachter Es, Mönchengladbach",
        "beschreibung": "Welche Daten diese Seite verarbeitet: Aufruf, Rückruf-Formular, Anruf, WhatsApp, Google Ads Conversion-Messung mit Einwilligung.",
        "kanonisch": "datenschutz.html",
        "skripte": "",
    },
}


def bauen(name, meta):
    schale = (HIER / "vorlagen" / "schale.html").read_text(encoding="utf-8")
    inhalt = (HIER / "inhalte" / name).read_text(encoding="utf-8")
    bilder_html = {"bild_" + platz: bild_html(platz) for platz in BILDER}
    for schluessel, wert in bilder_html.items():
        if not wert:  # leerer Platz: die ganze Zeile fällt weg, kein Kasten
            inhalt = re.sub(r"^[ \t]*\{\{" + schluessel + r"\}\}[ \t]*\n", "", inhalt, flags=re.M)
    vertrauen_html = vertrauen()
    if not vertrauen_html:  # beide aus, oder nur die Bewertung an und veraltet: die Zeile fällt ganz weg
        inhalt = re.sub(r"^[ \t]*\{\{vertrauen\}\}[ \t]*\n", "", inhalt, flags=re.M)
    nachweise_html = bildnachweise()
    if not nachweise_html:
        inhalt = re.sub(r"^[ \t]*\{\{bildnachweise\}\}[ \t]*\n\n?", "", inhalt, flags=re.M)
    schale, inhalt = ohne_kommentare(schale), ohne_kommentare(inhalt)
    # Inhalt zuerst einsetzen, damit seine Platzhalter (WhatsApp, Rückruf) in der Schleife mit ersetzt werden.
    werte = {"inhalt": inhalt.strip()}
    werte.update(meta)
    werte["noindex"] = '<meta name="robots" content="noindex">' if NOINDEX else ""
    werte["vertrauen"] = vertrauen_html
    werte["bildnachweise"] = nachweise_html
    werte.update(bilder_html)
    werte["nav_kopf"] = menue(name, False, 6)
    werte["nav_menue"] = menue(name, True, 10)
    werte.update(GLOBAL)
    seite = schale
    for schluessel, wert in werte.items():
        seite = seite.replace("{{" + schluessel + "}}", wert)
    if "{{faq_jsonld}}" in seite:
        seite = seite.replace("{{faq_jsonld}}", faq_jsonld(seite))
    if "{{" in seite:
        sys.exit(f"{name}: Platzhalter offen: {seite[seite.index('{{'):seite.index('{{') + 30]}")
    if "<!--" in seite:
        sys.exit(f"{name}: Kommentar in der gebauten Seite: {seite[seite.index('<!--'):seite.index('<!--') + 60]}")
    return seite


def main():
    if "--bewertungszeile" in sys.argv:
        print(bewertung_zeile())
        return
    sperre_noindex()
    sperre_bilder()
    pruefen = "--pruefen" in sys.argv
    meldung = bewertung_meldung()
    if meldung:  # laut, in Bau und Prüfung; der Exit bleibt davon unberührt
        print(meldung)
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
