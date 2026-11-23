#!/usr/bin/env python3
"""Zeuge für die Sperren in bauen.py: Konfiguration (konfig_fehler, vor allem labels.website_call), Bewertungskasten
(bewertung_fehler mit fester Uhr, noindex_fehler), Kommentare (ohne_kommentare und Kommentarsperre), Fotoschalter
und der Wegfall von {{vertrauen}}. Rotprobe: pruefen/rotprobe_bauen.py.

Aufruf: python pruefen/zeuge_bauen.py   Exit 0, wenn jeder Fall stimmt, sonst Exit 1.
Geprüft wird die Funktion, die sperre_noindex bei NOINDEX = False aufruft: leer ist erlaubt (kein Nummerntausch),
ein Platzhalter mit X oder ein Label mit unzulässigen Zeichen ist ein Abbruch (Programmierer r1, Fund 7).
Dazu die Form der konfig.js des Repos, immer mit eigenen Testwerten: Der Zeuge hängt nicht daran, ob die Datei
gerade Platzhalter oder Kontowerte trägt, und bleibt am Tag der Kontoanlage grün.
"""
import atexit
import contextlib
import datetime
import difflib
import io
import pathlib
import re
import shutil
import sys
import tempfile

HIER = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent))
import bauen  # noqa: E402


def konfig(tag="AW-1234567890", klick="LabKlick", wa="LabWa", form="LabForm", anruf='    website_call: ""\n'):
    return ('/* Beispiel im Kommentar: "AW-XXXXXXXXXX" */\nwindow.KGE_KONFIG = {\n'
            f'  googleTag: "{tag}",\n  labels: {{\n    phone_click: "{klick}",\n    whatsapp_click: "{wa}",\n'
            f'    form_submit: "{form}",\n{anruf}  }},\n  einwilligungsModus: "einfach"\n}};\n')


TEST = {"googleTag": "AW-1234567890", "phone_click": "TestKlick01", "whatsapp_click": "TestWa01",
        "form_submit": "TestForm01", "website_call": ""}


def echte_mit(werte):
    """Text der konfig.js des Repos, jeder der fünf Werte durch einen Testwert ersetzt (jeder muss genau einmal stehen)."""
    text = (HIER.parent / "konfig.js").read_text(encoding="utf-8")
    for schluessel, wert in werte.items():
        text, n = re.subn(rf'(?m)^(\s*{schluessel}:\s*)"[^"]*"', lambda m, w=wert: f'{m.group(1)}"{w}"', text)
        if n != 1:
            sys.exit(f"ROT  konfig.js des Repos: {schluessel} steht {n}-mal statt einmal als Wert")
    return text


FAELLE = [
    ("echte Werte, website_call leer: erlaubt", konfig(), False),
    ("echte Werte, website_call gesetzt: erlaubt", konfig(anruf='    website_call: "AbC-d_1234567890"\n'), False),
    ("website_call Platzhalter mit X: Abbruch", konfig(anruf='    website_call: "XXXXXXXXXXXXXXXXXXX"\n'), True),
    ("website_call mit Leerzeichen: Abbruch", konfig(anruf='    website_call: "Lab Anruf"\n'), True),
    ("website_call mit Schrägstrich (ganze send_to eingetragen): Abbruch", konfig(anruf='    website_call: "AW-1/Lab"\n'), True),
    ("website_call fehlt ganz: Abbruch", konfig(anruf=""), True),
    ("googleTag Platzhalter: Abbruch wie bisher", konfig(tag="AW-XXXXXXXXXX"), True),
    ("phone_click Platzhalter: Abbruch wie bisher", konfig(klick="XXXXXXXXXXXXXXXXXXX"), True),
    ("form_submit leer: Abbruch wie bisher", konfig(form=""), True),
    # Die Form der echten konfig.js, aber immer mit eigenen Testwerten: Der Zeuge hängt damit nicht am Zustand der
    # Datei (Platzhalter vor der Kontoanlage, Kontowerte danach) und bleibt an beiden Tagen grün.
    ("Form der konfig.js des Repos mit Testwerten, website_call leer: erlaubt", echte_mit(TEST), False),
    ("Form der konfig.js des Repos mit Testwerten und Testlabel für website_call: erlaubt",
     echte_mit(dict(TEST, website_call="TestAnruf01")), False),
    ("Form der konfig.js des Repos mit Platzhalter in googleTag: Abbruch",
     echte_mit(dict(TEST, googleTag="AW-XXXXXXXXXX")), True),
    ("Form der konfig.js des Repos mit Platzhalter in website_call: Abbruch",
     echte_mit(dict(TEST, website_call="XXXXXXXXXXXXXXXXXXX")), True),
]


# --- Bewertung, Name, Kommentare (Programmierer r2, F2, F3, F6) -------------------------------------------------
# Feste Uhr: bewertung_fehler bekommt heute=HEUTE, das Ergebnis hängt nicht am Tag des Laufs.
HEUTE = datetime.date(2026, 11, 20)
PROFIL = "https://g.page/r/CkgeBeispiel"
GUELTIG = dict(BEWERTUNG_ZEIGEN=True, BEWERTUNG_NOTE="4,9", BEWERTUNG_ANZAHL="48", BEWERTUNG_SEIT="2019",
               BEWERTUNG_STAND="06.11.2026", BEWERTUNG_LINK=PROFIL, BEWERTUNG_KUNDENBELEG="FG7a2c91")
PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 24
WURZEL_TMP = pathlib.Path(tempfile.mkdtemp(prefix="kge-zeuge-belege-"))
atexit.register(shutil.rmtree, WURZEL_TMP, True)


def tag(tage_zurueck, von=None):
    return ((von or HEUTE) - datetime.timedelta(days=tage_zurueck)).strftime("%d.%m.%Y")


def belegordner(stand, foto=True, inhalt=PNG, foto_tag=None):
    """Eigener Belegordner je Fall: mit Bildschirmfoto zum Stand (oder zu foto_tag), ohne, oder mit falschem Inhalt."""
    ordner = pathlib.Path(tempfile.mkdtemp(dir=WURZEL_TMP))
    if foto:
        try:
            datum = datetime.datetime.strptime(foto_tag or stand, "%d.%m.%Y").date()
        except ValueError:
            return ordner
        (ordner / f"bewertung-{datum:%Y-%m-%d}.png").write_bytes(inhalt)
    return ordner


def mit_belegen(werte, **beleg):
    return dict(werte, BELEGE=belegordner(werte.get("BEWERTUNG_STAND", ""), **beleg))


@contextlib.contextmanager
def schalter(**werte):
    """Setzt Modulwerte von bauen für einen Fall und stellt sie danach wieder her."""
    alt = {k: getattr(bauen, k) for k in werte}
    for k, v in werte.items():
        setattr(bauen, k, v)
    try:
        yield
    finally:
        for k, v in alt.items():
            setattr(bauen, k, v)


def bewertung(beleg=None, **abweichung):
    with schalter(**mit_belegen(dict(GUELTIG, **abweichung), **(beleg or {}))):
        return bauen.bewertung_fehler(heute=HEUTE)


def veraltet(stand):
    with schalter(**mit_belegen(dict(GUELTIG, BEWERTUNG_STAND=stand))):
        return bauen.bewertung_veraltet(heute=HEUTE)


def meldung(stand):
    with schalter(**mit_belegen(dict(GUELTIG, BEWERTUNG_STAND=stand))):
        return bauen.bewertung_meldung(heute=HEUTE)


HEUTE_ECHT = datetime.date.today()


def bau_veraltet():
    """Stand 15 Tage alt (Uhr des Laufs, weil bauen() kein heute nimmt): Seite ohne Kasten, Name steht, kein Abbruch."""
    seite = baue(**mit_belegen(dict(GUELTIG, BEWERTUNG_STAND=tag(15, HEUTE_ECHT), NAME_ZEIGEN=True)))
    return isinstance(seite, str) and 'class="bewertung"' not in seite and NAME_ZEILE in seite


def bau_veraltet_ohne_name():
    """Stand veraltet und Name aus: Die Zeile fällt ganz weg, genau wie bei beiden Schaltern aus."""
    alt = baue(**mit_belegen(dict(GUELTIG, BEWERTUNG_STAND=tag(15, HEUTE_ECHT), NAME_ZEIGEN=False)))
    aus = baue(BEWERTUNG_ZEIGEN=False, NAME_ZEIGEN=False)
    return isinstance(alt, str) and alt == aus


def pruefen_meldet_veraltet():
    """main mit --pruefen druckt die Zeile BEWERTUNG VERALTET (der Exit hängt nur an Abweichungen der Seiten)."""
    stand = tag(15, HEUTE_ECHT)
    puffer = io.StringIO()
    with schalter(**mit_belegen(dict(GUELTIG, BEWERTUNG_STAND=stand, NAME_ZEIGEN=True))), \
            contextlib.redirect_stdout(puffer):
        argv, sys.argv = sys.argv, ["bauen.py", "--pruefen"]
        try:
            bauen.main()
        except SystemExit:
            pass
        finally:
            sys.argv = argv
    return f"BEWERTUNG VERALTET, Kasten weggelassen: Stand {stand}" in puffer.getvalue()


def noindex_mit(**werte):
    with schalter(**werte):
        return bauen.noindex_fehler(konfig())


def baue(seite="index.html", **werte):
    """Baut eine Seite mit gesetzten Schaltern; ein Abbruch (sys.exit) kommt als ("ABBRUCH", Meldung) zurück."""
    with schalter(**werte):
        try:
            return bauen.bauen(seite, bauen.SEITEN[seite])
        except SystemExit as e:
            return ("ABBRUCH", str(e))


NAME_ZEILE = '      <p class="name-zeile">Ihr Sachverständiger: Cihan Es</p>\n'


def vertrauen_aus_ohne_leerzeile():
    """Beide Schalter aus: Die Seite gleicht der mit Namenszeile ohne genau diese Zeile, also bleibt keine Leerzeile
    und kein Platzhalter stehen."""
    an = baue(BEWERTUNG_ZEIGEN=False, NAME_ZEIGEN=True)
    aus = baue(BEWERTUNG_ZEIGEN=False, NAME_ZEIGEN=False)
    return isinstance(an, str) and an.count(NAME_ZEILE) == 1 and aus == an.replace(NAME_ZEILE, "")


def bewertung_im_bau():
    """Schalter AN mit gültigen Werten (Stand heute): Kasten mit Link und Hinweis, Name dahinter."""
    seite = baue(**mit_belegen(dict(GUELTIG, BEWERTUNG_STAND=tag(0, HEUTE_ECHT), NAME_ZEIGEN=True)))
    if not isinstance(seite, str):
        return False
    k, n = seite.find('<div class="bewertung"><a href="' + PROFIL + '"'), seite.find('class="name-zeile"')
    return 0 < k < n and bauen.BEWERTUNG_HINWEIS in seite and "seit 2019, Stand" in seite


def sperre_ohne_entfernen():
    """Kommentarsperre: Entfernt ohne_kommentare nichts, bricht der Bau ab (die Schale trägt Kommentare)."""
    with schalter(ohne_kommentare=lambda t: t):
        try:
            bauen.bauen("index.html", bauen.SEITEN["index.html"])
        except SystemExit as e:
            return "Kommentar in der gebauten Seite" in str(e)
    return False


NACHWEIS = "Startseite: Foto Beispiel, Quelle Beispiel"
EIN = {"datei": "bilder/x.jpg", "alt": "Text", "breite": 1600, "hoehe": 900, "unterschrift": "Symbolbild",
       "nachweis": NACHWEIS}
LEER = {"datei": "", "alt": "", "breite": 0, "hoehe": 0, "unterschrift": "", "nachweis": ""}
FIGUR = ('<figure class="bild"><img src="bilder/x.jpg" alt="Text" width="1600" height="900" loading="lazy">'
         '<figcaption>Symbolbild</figcaption></figure>')


def bildordner(vorhanden=True):
    """Eigener Ordner je Fall, mit oder ohne die Bilddatei bilder/x.jpg."""
    ordner = pathlib.Path(tempfile.mkdtemp(dir=WURZEL_TMP))
    (ordner / "bilder").mkdir()
    if vorhanden:
        (ordner / "bilder" / "x.jpg").write_bytes(b"\xff\xd8\xff\xe0")
    return ordner


def tabelle(platz="unfall", **abweichung):
    """Bildtabelle für einen Fall: alle Plätze leer, nur platz belegt (None: keiner)."""
    t = {p: dict(LEER) for p in bauen.BILDER}
    if platz:
        t[platz] = dict(EIN, **abweichung)
    return t


def platz_fehler(vorhanden=True, **abweichung):
    with schalter(BILDER=tabelle(**abweichung), BILDWURZEL=bildordner(vorhanden)):
        return bauen.bild_fehler("unfall")


def seite_mit_bild(seite="ablauf.html", an=True, vorhanden=True, platz="unfall", **abweichung):
    """Baut eine Seite mit eigener Bildtabelle und eigenem Bildordner; der Platz unfall steht auf ablauf.html."""
    return baue(seite, FOTOS_ZEIGEN=an, BILDER=tabelle(platz, **abweichung), BILDWURZEL=bildordner(vorhanden))


def schalter_aus_wie_leer():
    """Hauptschalter aus: kein Bild, die Seite gleicht der mit leerer Tabelle."""
    aus, leer = seite_mit_bild(an=False), seite_mit_bild(platz=None)
    return isinstance(aus, str) and aus == leer and "<figure" not in aus


def bild_genau():
    """Platz belegt gegen leer: genau die eine Zeile mit der Figur mehr, keine Leerzeile, nichts fällt weg."""
    an, aus = seite_mit_bild(), seite_mit_bild(platz=None)
    if not (isinstance(an, str) and isinstance(aus, str)):
        return False
    d = [z for z in difflib.ndiff(aus.splitlines(), an.splitlines()) if z[:2] in ("+ ", "- ")]
    return all(z.startswith("+ ") for z in d) and [z[2:].strip() for z in d] == [FIGUR]


def enthaelt(teil, fehlt=(), **fall):
    seite = seite_mit_bild(**fall)
    return isinstance(seite, str) and teil in seite and not any(f in seite for f in fehlt)


def nachweise_im_impressum(an):
    """Impressum mit einem gezeigten Bild: Abschnitt Bildnachweise mit dem Nachweis. Hauptschalter aus: kein
    Abschnitt, die Seite gleicht der mit leerer Tabelle (keine Leerzeile, kein Platzhalter)."""
    seite = seite_mit_bild("impressum.html", an=an)
    if not isinstance(seite, str):
        return False
    if an:
        return "<h2>Bildnachweise</h2>" in seite and NACHWEIS in seite
    return seite == seite_mit_bild("impressum.html", platz=None) and "Bildnachweise" not in seite


OK = None  # erwartet: keine Meldung
FEHLER = "Meldung"  # erwartet: eine Meldung

# (Name, Funktion, Soll): Soll None heißt „keine Meldung“, "Meldung" heißt „Meldung erwartet“, True/False ist das
# erwartete Ergebnis einer Ja/Nein-Prüfung, ein String sonst das erwartete Ergebnis wörtlich.
WEITERE = [
    ("B1 alle fünf Werte gültig, Stand 14 Tage alt: baut", lambda: bewertung(), OK),
    ("B2 NOTE leer: Abbruch", lambda: bewertung(BEWERTUNG_NOTE=""), FEHLER),
    ("B3 SEIT nur Leerzeichen: Abbruch", lambda: bewertung(BEWERTUNG_SEIT="  "), FEHLER),
    ("B4 ANZAHL leer: Abbruch", lambda: bewertung(BEWERTUNG_ANZAHL=""), FEHLER),
    ("B5 LINK leer: Abbruch", lambda: bewertung(BEWERTUNG_LINK=""), FEHLER),
    ("B6 Stand 15 Tage alt: kein Abbruch (Kasten fällt weg, A2 bis A7)", lambda: bewertung(BEWERTUNG_STAND="05.11.2026"), OK),
    ("B11 KUNDENBELEG leer: Abbruch mit Nennung des leeren Werts", lambda: bewertung(BEWERTUNG_KUNDENBELEG=""),
     "BEWERTUNG_ZEIGEN ist an, aber leer: BEWERTUNG_KUNDENBELEG"),
    ("B12 KUNDENBELEG Platzhalter XXXXXXXX: Abbruch", lambda: bewertung(BEWERTUNG_KUNDENBELEG="XXXXXXXX"), FEHLER),
    ("B13 KUNDENBELEG vier Zeichen: Abbruch", lambda: bewertung(BEWERTUNG_KUNDENBELEG="FG7a"), FEHLER),
    ("B14 KUNDENBELEG neun Zeichen: Abbruch", lambda: bewertung(BEWERTUNG_KUNDENBELEG="FG7a2c91x"), FEHLER),
    ("B15 KUNDENBELEG mit Leerzeichen: Abbruch", lambda: bewertung(BEWERTUNG_KUNDENBELEG="FG7a 2c9"), FEHLER),
    ("P1 Bildschirmfoto fehlt: Abbruch", lambda: bewertung(beleg={"foto": False}), FEHLER),
    ("P2 Bildschirmfoto von einem anderen Tag: Abbruch", lambda: bewertung(beleg={"foto_tag": "07.11.2026"}), FEHLER),
    ("P3 Bildschirmfoto leer (kein PNG): Abbruch", lambda: bewertung(beleg={"inhalt": b""}), FEHLER),
    ("P4 Bildschirmfoto ist Text mit Endung .png: Abbruch", lambda: bewertung(beleg={"inhalt": b"kein Bild"}), FEHLER),
    ("P5 veralteter Stand ohne Bildschirmfoto: Abbruch, nicht nur weglassen", lambda: bewertung(
        BEWERTUNG_STAND="05.11.2026", beleg={"foto": False}), FEHLER),
    ("B7 Stand heute: baut", lambda: bewertung(BEWERTUNG_STAND="20.11.2026"), OK),
    ("B8 Stand in der Zukunft (morgen): Abbruch", lambda: bewertung(BEWERTUNG_STAND="21.11.2026"), FEHLER),
    ("B9 Stand im Format JJJJ-MM-TT: Abbruch", lambda: bewertung(BEWERTUNG_STAND="2026-11-20"), FEHLER),
    ("B10 Stand 31.02.2026 (kein Tag): Abbruch", lambda: bewertung(BEWERTUNG_STAND="31.02.2026"), FEHLER),
    ("J1 SEIT Platzhalter JJJJ: Abbruch", lambda: bewertung(BEWERTUNG_SEIT="JJJJ"), FEHLER),
    ("J2 SEIT 2004 (vor 2005): Abbruch", lambda: bewertung(BEWERTUNG_SEIT="2004"), FEHLER),
    ("J3 SEIT 2005: baut", lambda: bewertung(BEWERTUNG_SEIT="2005"), OK),
    ("J4 SEIT laufendes Jahr 2026: baut", lambda: bewertung(BEWERTUNG_SEIT="2026"), OK),
    ("J5 SEIT 2027 (nach heute): Abbruch", lambda: bewertung(BEWERTUNG_SEIT="2027"), FEHLER),
    ("J6 SEIT 19 (zweistellig): Abbruch", lambda: bewertung(BEWERTUNG_SEIT="19"), FEHLER),
    ("L1 Link Kartensuche: Abbruch auch mit noindex", lambda: bewertung(
        BEWERTUNG_LINK="https://www.google.com/maps/search/?api=1&query=Kfz+Gutachter+Es"), FEHLER),
    ("L2 Link maps?q=: Abbruch", lambda: bewertung(BEWERTUNG_LINK="https://www.google.com/maps?q=Kfz+Gutachter+Es"), FEHLER),
    ("L3 Link http://g.page/…: Abbruch", lambda: bewertung(BEWERTUNG_LINK="http://g.page/r/CkgeBeispiel"), FEHLER),
    ("L4 Link fremder Host g.page.example.com: Abbruch", lambda: bewertung(BEWERTUNG_LINK="https://g.page.example.com/x"), FEHLER),
    ("L5 Link https://g.page/ ohne Pfad: Abbruch", lambda: bewertung(BEWERTUNG_LINK="https://g.page/"), FEHLER),
    ("L6 Link maps.app.goo.gl: baut", lambda: bewertung(BEWERTUNG_LINK="https://maps.app.goo.gl/AbCdEf123"), OK),
    ("L7 Link www.google.com/maps/place: baut", lambda: bewertung(
        BEWERTUNG_LINK="https://www.google.com/maps/place/Kfz+Gutachter+Es/@51.19,6.43,17z"), OK),
    ("L8 Link mit Anführungszeichen: Abbruch", lambda: bewertung(BEWERTUNG_LINK='https://g.page/r/x"onclick=1'), FEHLER),
    ("N1 NOINDEX aus, Bewertung an, Kartensuche: Abbruch", lambda: noindex_mit(
        BEWERTUNG_ZEIGEN=True, BEWERTUNG_LINK="https://www.google.com/maps/search/?api=1&query=x"), FEHLER),
    ("N2 NOINDEX aus, Bewertung aus, Kartensuche: baut", lambda: noindex_mit(
        BEWERTUNG_ZEIGEN=False, BEWERTUNG_LINK="https://www.google.com/maps/search/?api=1&query=x"), OK),
    ("N3 NOINDEX aus, Bewertung an, Profiladresse: baut", lambda: noindex_mit(BEWERTUNG_ZEIGEN=True, BEWERTUNG_LINK=PROFIL), OK),
    ("K1 zwei Kommentare in einer Zeile, Text dazwischen bleibt", lambda: bauen.ohne_kommentare(
        "<!-- a --> <p>WICHTIG</p> <!-- b -->\n<p>bleibt</p>\n"), " <p>WICHTIG</p>\n<p>bleibt</p>\n"),
    ("K2 zwei Kommentare über Zeilen, Inhalt dazwischen bleibt", lambda: bauen.ohne_kommentare(
        "  <!-- a --> <p>WICHTIG</p>\n<p>X</p> <!-- b -->\n<p>Y</p>\n"), " <p>WICHTIG</p>\n<p>X</p>\n<p>Y</p>\n"),
    ("K3 mehrzeiliger Kommentar als eigene Zeilen: samt Zeilenende weg", lambda: bauen.ohne_kommentare(
        "<p>A</p>\n  <!-- eins\n  zwei -->\n<p>B</p>\n"), "<p>A</p>\n<p>B</p>\n"),
    ("K4 Kommentar am Zeilenende hinter Inhalt: nur der Kommentar weg", lambda: bauen.ohne_kommentare(
        "<p>A</p> <!-- Notiz -->\n<p>B</p>\n"), "<p>A</p>\n<p>B</p>\n"),
    ("K5 ganze Kommentarzeile: samt Zeilenende weg", lambda: bauen.ohne_kommentare(
        "<p>A</p>\n    <!-- Notiz -->\n<p>B</p>\n"), "<p>A</p>\n<p>B</p>\n"),
    ("K6 nicht geschlossener Kommentar bleibt stehen (Sperre fängt ihn)", lambda: bauen.ohne_kommentare(
        "<p>A</p> <!-- offen\n<p>B</p>\n"), "<p>A</p> <!-- offen\n<p>B</p>\n"),
    ("S1 Kommentarsperre: ohne Entfernen bricht der Bau ab", sperre_ohne_entfernen, True),
    ("F1 Hauptschalter FOTOS_ZEIGEN aus: kein Bild, Seite wie mit leerer Tabelle", schalter_aus_wie_leer, True),
    ("F2 Platz belegt: Figur mit Maßen, alt, lazy und Unterschrift", lambda: enthaelt(FIGUR), True),
    ("F3 Platz belegt gegen leer: genau die Zeile der Figur mehr, keine Leerzeile", bild_genau, True),
    ("G1 Platz eingetragen, Bilddatei fehlt: Meldung", lambda: platz_fehler(vorhanden=False), FEHLER),
    ("G2 Datei, Maße, alt und Nachweis da: keine Meldung", lambda: platz_fehler(), OK),
    ("G3 Bildnachweis leer: Meldung", lambda: platz_fehler(nachweis="  "), FEHLER),
    ("G4 alt-Text leer: Meldung", lambda: platz_fehler(alt=""), FEHLER),
    ("G5 Höhe 0: Meldung", lambda: platz_fehler(hoehe=0), FEHLER),
    ("G6 leerer Platz (keine Datei eingetragen): keine Meldung", lambda: platz_fehler(datei=""), OK),
    ("G7 Datei fehlt: der Platz erscheint nicht, der Bau läuft", lambda: enthaelt("<main>", fehlt=("<figure",), vorhanden=False), True),
    ("G8 vorrang: fetchpriority statt lazy", lambda: enthaelt('fetchpriority="high"', fehlt=('loading="lazy"',), vorrang=True), True),
    ("G9 Unterschrift leer: keine figcaption", lambda: enthaelt("<figure", fehlt=("<figcaption",), unterschrift=""), True),
    ("G10 gezeigtes Bild: Abschnitt Bildnachweise im Impressum", lambda: nachweise_im_impressum(True), True),
    ("G11 Hauptschalter aus: kein Abschnitt Bildnachweise, keine Leerzeile", lambda: nachweise_im_impressum(False), True),
    ("V1 beide Schalter aus: {{vertrauen}} samt Zeile weg, keine Leerzeile", vertrauen_aus_ohne_leerzeile, True),
    ("V2 Bewertung an, gültig: Kasten mit Profil-Link und Hinweis, Name dahinter", bewertung_im_bau, True),
    ("V3 Bewertung an mit SEIT JJJJ: der Bau bricht ab", lambda: isinstance(baue(**mit_belegen(dict(
        GUELTIG, BEWERTUNG_SEIT="JJJJ", BEWERTUNG_STAND=tag(0, HEUTE_ECHT)))), tuple), True),
    ("V4 Bewertung an ohne Bildschirmfoto: der Bau bricht ab", lambda: isinstance(baue(**mit_belegen(dict(
        GUELTIG, BEWERTUNG_STAND=tag(0, HEUTE_ECHT)), foto=False)), tuple), True),
    ("A1 Stand 14 Tage: nicht veraltet", lambda: veraltet("06.11.2026"), False),
    ("A2 Stand 15 Tage: veraltet", lambda: veraltet("05.11.2026"), True),
    ("A3 Meldung bei 15 Tagen, wörtlich", lambda: meldung("05.11.2026"),
     "BEWERTUNG VERALTET, Kasten weggelassen: Stand 05.11.2026"),
    ("A4 keine Meldung bei 14 Tagen", lambda: meldung("06.11.2026"), OK),
    ("A5 Bau mit Stand 15 Tage: Seite ohne Kasten, mit Name, kein Abbruch", bau_veraltet, True),
    ("A6 Bau mit Stand 15 Tage, Name aus: Zeile ganz weg wie bei beiden Schaltern aus", bau_veraltet_ohne_name, True),
    ("A7 --pruefen druckt BEWERTUNG VERALTET", pruefen_meldet_veraltet, True),
]


def stimmt(ist, soll):
    if soll is OK:
        return ist is None
    if soll == FEHLER:
        return isinstance(ist, str) and bool(ist.strip())
    return ist == soll


def main():
    rot = 0
    for name, text, soll_abbruch in FAELLE:
        fehler = bauen.konfig_fehler(text)
        ok = bool(fehler) == soll_abbruch
        rot += 0 if ok else 1
        print(("ok   " if ok else "ROT  ") + name + ("" if ok else f" · gemeldet: {fehler!r}"))
    for name, fall, soll in WEITERE:
        try:
            ist = fall()
        except Exception as e:  # ein Absturz ist rot, nie grün
            ist = f"AUSNAHME {type(e).__name__}: {e}"
            ok = False
        else:
            ok = stimmt(ist, soll)
        rot += 0 if ok else 1
        print(("ok   " if ok else "ROT  ") + name + ("" if ok else f" · ist: {ist!r}"))
    zahl = len(FAELLE) + len(WEITERE)
    print(f"ROT: {rot} von {zahl} weichen ab" if rot else f"GRÜN: {zahl} Fälle stimmen")
    sys.exit(1 if rot else 0)


if __name__ == "__main__":
    main()
