#!/usr/bin/env python3
"""Rotprobe für pruefen/zeuge_seiten.py: Jede Mutation bricht an einer Kopie genau eine Regel des Umbaus, und der
Zeuge muss dann rot werden, und zwar im genannten Fall (Anker). Bleibt er grün oder wird er nur woanders rot, prüft
er die Regel nicht.

Aufruf: python pruefen/rotprobe_seiten.py   Exit 0, wenn der Stand grün ist und jede Mutation im erwarteten Fall rot
macht, sonst Exit 1.

Gerechnet wird je Mutation in einer frischen Kopie des Repos in einem Temp-Ordner (ohne .git, _bericht, .claude);
der Arbeitsbaum bleibt unberührt. Drei Arten:
  seite   ändert eine gebaute Datei (Seite oder ausgeliefertes Skript) direkt
  quelle  ändert eine Quelle (bauen.py, konfig.js, inhalte/) und baut NICHT neu
  bau     ändert eine Quelle und baut die Kopie mit python bauen.py neu (so sieht ein späterer Bau aus, der
          bauen.py --pruefen grün hält)
Jede Mutation ersetzt ein Fragment, das in der Datei genau einmal stehen muss (bei „alle“ mindestens zweimal, die
Zahl wird gemeldet), sonst bricht die Probe ab: Eine Mutation, die nichts trifft, wäre eine grüne Lüge.
"""
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HIER = pathlib.Path(__file__).resolve().parent
WURZEL = HIER.parent
UMGEBUNG = dict(os.environ, PYTHONIOENCODING="utf-8")  # sonst schreibt der Zeuge unter Windows cp1252
WEG = "WEG"  # Art: Datei entfernen


def m(name, fall, art, datei, alt="", neu="", regex=False, alle=False):
    return {"name": name, "fall": fall, "art": art, "datei": datei, "alt": alt, "neu": neu, "regex": regex,
            "alle": alle}


MUTATIONEN = [
    # Regel 1, Menü
    m("M-a Handy-Menü auf ablauf.html entfernt", "M1", "seite", "ablauf.html",
      r'\s*<details class="menue">.*?</details>', "", regex=True),
    m("M-b Kopfnavigation der Startseite ohne Einsatzgebiet", "M2", "seite", "index.html",
      r'(<nav class="kopf-nav" aria-label="Hauptmenü">.*?)<a href="umland.html">Einsatzgebiet</a>\s*', r"\1", regex=True),
    m("M-c aria-current im Bau immer an Start statt an der eigenen Seite", "M3", "bau", "bauen.py",
      """aktuell = ' aria-current="page"' if ziel == eigen else \"\"""",
      """aktuell = ' aria-current="page"' if ziel == "./" else \"\""""),
    m("M-d aria-current an fremdem Punkt der Kopfnavigation (nachts-wochenende)", "M3", "seite",
      "nachts-wochenende.html",
      r'(<nav class="kopf-nav" aria-label="Hauptmenü">.*?)<a href="kosten.html">', r'\1<a href="kosten.html" aria-current="page">',
      regex=True),
    # Regel 2, kein „Umland“
    m("U-a Titel mit „Umland“ (umland.html)", "U1", "seite", "umland.html",
      "<title>Kfz-Gutachter für Viersen, Neuss und Kaarst |", "<title>Kfz-Gutachter für Viersen, Neuss, Kaarst und Umland |"),
    m("U-b meta description mit „Umland“ über SEITEN in bauen.py", "U1", "bau", "bauen.py",
      "Kaarst, ebenso in Willich", "Kaarst und im Umland, ebenso in Willich"),
    m("U-c alt-Text mit „Umland“ (index.html)", "U1", "seite", "index.html",
      'alt="Hintere Seitenwand einer Limousine mit gerissenem Lack und eingedrücktem Blech"',
      'alt="Hintere Seitenwand einer Limousine mit gerissenem Lack und eingedrücktem Blech, Umland"'),
    m("U-d Bildunterschrift mit „Umland“ (index.html)", "U1", "seite", "index.html",
      "<figcaption>Mönchengladbach, Münster St. Vitus</figcaption>",
      "<figcaption>Mönchengladbach und Umland, Münster St. Vitus</figcaption>"),
    m("U-e aria-label mit „Umland“ (kosten.html)", "U1", "seite", "kosten.html",
      'aria-label="Hauptmenü"', 'aria-label="Hauptmenü Umland"'),
    m("U-f JSON-LD mit „Umland“ (index.html)", "U1", "seite", "index.html",
      'in Mönchengladbach und den Nachbarstädten.",', 'in Mönchengladbach und im Umland.",'),
    m("U-g sichtbare h1 mit „umland“ über inhalte/umland.html", "U1", "bau", "inhalte/umland.html",
      "<h1>Kfz-Gutachter für Viersen, Neuss und Kaarst</h1>", "<h1>Kfz-Gutachter für Viersen, Neuss und das umland</h1>"),
    # Regel 3, Rufnummer
    m("R-a falsches tel-Ziel im Fuß (nachts-wochenende.html)", "R2", "seite", "nachts-wochenende.html",
      '<li>Telefon <a href="tel:+4921616888691"', '<li>Telefon <a href="tel:+4921616888690"'),
    m("R-b kein tel-Link mehr auf datenschutz.html", "R2", "seite", "datenschutz.html",
      'href="tel:+4921616888691"', 'href="kontakt.html"', alle=True),
    m("R-c Nummer nur noch als 02161 6888691 geschrieben (impressum.html)", "R1", "seite", "impressum.html",
      "02161 688 86 91", "02161 6888691", alle=True),
    m("R-d alte Nummer mit Leerzeichen (datenschutz.html)", "R3", "seite", "datenschutz.html",
      "<span data-echte-nummer>(+49 2161 6888691)</span>", "<span data-echte-nummer>(+49 2161 622 57 68)</span>"),
    m("R-e alte Nummer mit Zeichenreferenz &#54; für die erste Ziffer (kontakt.html, roh kein Treffer)", "R3", "seite",
      "kontakt.html", "<span data-echte-nummer>(+49 2161 6888691)</span>",
      "<span data-echte-nummer>(02161 &#54;22 57 68)</span>"),
    m("R-h alte Nummer über Tags verteilt (ablauf.html, 622<span>57</span>68)", "R3", "seite", "ablauf.html",
      "<span data-echte-nummer>(+49 2161 6888691)</span>",
      "<span data-echte-nummer>(02161 622<span>57</span>68)</span>"),
    m("R-i tel-Ziel nur noch in einem src, kein anklickbarer Link (datenschutz.html)", "R2", "seite",
      "datenschutz.html", 'href="tel:+4921616888691"', 'href="kontakt.html" src="tel:+4921616888691"', alle=True),
    m("R-j doppeltes href, das erste (das der Browser nimmt) falsch (nachts-wochenende.html)", "R2", "seite",
      "nachts-wochenende.html", '<li>Telefon <a href="tel:+4921616888691"',
      '<li>Telefon <a href="tel:+4921616888690" href="tel:+4921616888691"'),
    m("R-f alte Nummer in einem ausgelieferten Skript (leiste.js)", "R3", "seite", "leiste.js",
      r"\A", "// alt: 02161/622 57 68\n", regex=True),
    m("R-g konfig.js nennt eine andere Nummer als bauen.py und die Seiten", "R0", "quelle", "konfig.js",
      'telefonAnzeige: "02161 688 86 91"', 'telefonAnzeige: "02161 688 86 92"'),
    # Regel 4, Bilder und Nachweise (die zwei unbemerkten Fälle aus dem Codex-Gegenlauf, Abschnitt 6)
    m("B-a Platzhalter {{bild_streifschaden}} aus inhalte/kosten.html entfernt, nicht neu gebaut", "B3", "quelle",
      "inhalte/kosten.html", "        {{bild_streifschaden}}\n", ""),
    m("B-b Platzhalter {{bild_streifschaden}} entfernt und neu gebaut: Bild weg, Nachweis bleibt", "B1", "bau",
      "inhalte/kosten.html", "        {{bild_streifschaden}}\n", ""),
    m("B-c {{bildnachweise}} aus inhalte/impressum.html entfernt, nicht neu gebaut", "B3", "quelle",
      "inhalte/impressum.html", "    {{bildnachweise}}\n", ""),
    m("B-d {{bildnachweise}} entfernt und neu gebaut: Bilder ohne veröffentlichten Nachweis", "B1", "bau",
      "inhalte/impressum.html", "    {{bildnachweise}}\n", ""),
    m("B-e Nachweiszeile des Streifschadens im gebauten Impressum entfernt", "B2", "seite", "impressum.html",
      r"Streifschaden an einem weißen Auto:[^<]*<br>", "", regex=True),
    m("B-f Bild ohne Platz und ohne Nachweis auf ablauf.html eingefügt", "B2", "seite", "ablauf.html",
      "<h1>Nach dem Unfall: was Sie jetzt tun sollten</h1>",
      '<h1>Nach dem Unfall: was Sie jetzt tun sollten</h1><figure class="bild"><img src="bilder/favicon.svg" '
      'alt="Zeichen" width="10" height="10" loading="lazy"><figcaption>Symbolbild: Zeichen</figcaption></figure>'),
    # Regel 5, Beispielfoto und Namenskarte (Rechtsbericht 24.11.2026)
    m("S-a Marke am Streifschaden entfernt (kosten.html)", "S1", "seite", "kosten.html",
      '<span class="bild-marke">Beispielfoto</span>', ""),
    m("S-b Marke am Lackschaden aus, über BILDER in bauen.py, neu gebaut", "S1", "bau", "bauen.py",
      '"art": "schaden", "marke": True, "vorrang": True',
      '"art": "schaden", "marke": False, "vorrang": True'),
    m("S-c Marke am Lackschaden entfernt (index.html)", "S1", "seite", "index.html",
      '<span class="bild-marke">Beispielfoto</span>', ""),
    m("S-d Namenskarte neben das Schadenfoto gesetzt (index.html)", "S2", "seite", "index.html",
      '<figure class="bild"><img src="bilder/schadendetail-lack.jpg"',
      '<p class="name-zeile">Ihr Sachverständiger: Cihan Es</p><figure class="bild"><img src="bilder/schadendetail-lack.jpg"'),
    # Regel 6, Seitenregeln
    m("P-a noindex auf ablauf.html entfernt", "P1", "seite", "ablauf.html",
      '<meta name="robots" content="noindex">\n', ""),
    m("P-b keine h1 auf kontakt.html", "P2", "seite", "kontakt.html",
      "<h1>Kontakt und Anfahrt</h1>", "<h2>Kontakt und Anfahrt</h2>"),
    m("P-c zweite h1 auf ablauf.html", "P2", "seite", "ablauf.html",
      '<h2 id="weg">Vom Anruf zum fertigen Gutachten</h2>', '<h1 id="weg">Vom Anruf zum fertigen Gutachten</h1>'),
    m("P-d Canonical von kosten.html zeigt auf ablauf.html", "P3", "seite", "kosten.html",
      '<link rel="canonical" href="kosten.html">', '<link rel="canonical" href="ablauf.html">'),
    m("P-e Canonical in SEITEN auf fremde Seite, neu gebaut (Datei und SEITEN stimmen überein)", "P3", "bau",
      "bauen.py", '"kanonisch": "kosten.html"', '"kanonisch": "ablauf.html"'),
    m("P-f toter Anker auf andere Seite (nachts-wochenende.html → kontakt.html#rueckruf-weg)", "P4", "seite",
      "nachts-wochenende.html", 'href="kontakt.html#rueckruf"', 'href="kontakt.html#rueckruf-weg"'),
    m("P-g toter Anker auf derselben Seite (ablauf.html #mitbringe)", "P4", "seite", "ablauf.html",
      'href="#mitbringen"', 'href="#mitbringe"'),
    m("P-h Ankerziel entfernt (kosten.html ohne id honorar, umland.html verlinkt es)", "P4", "seite", "kosten.html",
      'id="honorar"', 'id="honorar-alt"'),
    m("P-i Link auf fehlende Seite (impressum.html → datenschtz.html)", "P4", "seite", "impressum.html",
      'href="datenschutz.html"', 'href="datenschtz.html"'),
    m("P-j Symbolverweis ins Leere (index.html #i-menu)", "P4", "seite", "index.html",
      '<use href="#i-menue"/>', '<use href="#i-menu"/>'),
    m("P-k doppelte id auf ablauf.html", "P5", "seite", "ablauf.html",
      '<h2 id="weg">', '<h2 id="mitbringen">'),
    m("P-l formular.js auf kontakt.html entfernt, Formular bleibt", "P6", "seite", "kontakt.html",
      '<script src="formular.js" defer></script>\n', ""),
    m("P-m formular.js auf ablauf.html geladen, ohne Formular", "P6", "seite", "ablauf.html",
      '<script src="einwilligung.js" defer></script>',
      '<script src="formular.js" defer></script>\n<script src="einwilligung.js" defer></script>'),
    m("P-n formular.js für kontakt.html aus SEITEN entfernt, neu gebaut", "P6", "bau", "bauen.py",
      """"kanonisch": "kontakt.html",\n        "skripte": '<script src="formular.js" defer></script>',""",
      """"kanonisch": "kontakt.html",\n        "skripte": "","""),
    m("P-o gebaute Seite nachts-wochenende.html fehlt", "P0", "weg", "nachts-wochenende.html"),
    # Runde 2 nach dem Codex-Gegenlauf 23.11., 19:15: Fälle, die der erste Stand grün durchließ.
    m("U-h „Um<span>land</span>“ in der h1 (umland.html)", "U1", "seite", "umland.html",
      "<h1>Kfz-Gutachter für Viersen, Neuss und Kaarst</h1>",
      "<h1>Kfz-Gutachter für Viersen, Neuss und das Um<span>land</span></h1>"),
    m("U-i JSON-LD mit \\u-Escape „Um\\u006cand“ (index.html)", "U1", "seite", "index.html",
      '"name": "Kfz Gutachter Es",', '"name": "Kfz Gutachter Es, Um\\u006cand",'),
    m("U-j „Umland“ im Text eines ausgelieferten Skripts (leiste.js)", "U1", "seite", "leiste.js",
      r"\A", "// Hinweis an Besucher: auch im Umland\n", regex=True),
    m("U-k „Um&shy;land“ in der h1 (umland.html)", "U1", "seite", "umland.html",
      "<h1>Kfz-Gutachter für Viersen, Neuss und Kaarst</h1>",
      "<h1>Kfz-Gutachter für Viersen, Neuss und das Um&shy;land</h1>"),
    m("R-k alte Nummer in stil.css (nicht in einer festen Liste, sondern über *.css gefunden)", "R3", "seite",
      "stil.css", r"\A", "/* 02161 622 57 68 */\n", regex=True),
    m("B-g Platzhalter des leeren Platzes {{bild_unfall}} aus inhalte/ablauf.html entfernt", "B3", "quelle",
      "inhalte/ablauf.html", "    {{bild_unfall}}\n", ""),
    m("B-h Nachweisblock im gebauten Impressum auskommentiert", "B1", "seite", "impressum.html",
      r"(<h2>Bildnachweise</h2>\s*<p>.*?</p>)", r"<!--\1-->", regex=True),
    m("P-p Link mit falscher Groß-/Kleinschreibung (umland.html → KOSTEN.html#honorar)", "P4", "seite",
      "umland.html", 'href="kosten.html#honorar"', 'href="KOSTEN.html#honorar"'),
    m("P-q Link auf eine Bauquelle, die nicht ausgeliefert wird (impressum.html → inhalte/datenschutz.html)", "P4",
      "seite", "impressum.html", 'href="datenschutz.html"', 'href="inhalte/datenschutz.html"'),
    m("P-r robots „no index“ statt noindex (ablauf.html)", "P1", "seite", "ablauf.html",
      '<meta name="robots" content="noindex">', '<meta name="robots" content="no index">'),
    m("P-s formular.js auf kontakt.html als type=text/plain (lädt nicht)", "P6", "seite", "kontakt.html",
      '<script src="formular.js" defer></script>', '<script type="text/plain" src="formular.js" defer></script>'),
    m("P-t neunte HTML-Seite im Repo, nicht in SEITEN", "P0", "neu", "alt-startseite.html",
      neu="<!DOCTYPE html><title>alt</title><h1>alt</h1>\n"),
    m("P-u Canonical der Startseite ../ in SEITEN, neu gebaut", "P3", "bau", "bauen.py",
      '"kanonisch": "./"', '"kanonisch": "../"'),
]


def kopie(ziel):
    shutil.copytree(WURZEL, ziel, ignore=shutil.ignore_patterns(".git", "_bericht", ".claude", "__pycache__",
                                                                  "_klon-*"))


def zeuge(ziel):
    lauf = subprocess.run([sys.executable, "-B", str(ziel / "pruefen" / "zeuge_seiten.py")], env=UMGEBUNG,
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    rote = [z for z in lauf.stdout.splitlines() if z.startswith("ROT  ")]
    return lauf.returncode, rote, lauf.stdout + lauf.stderr


def baue(ziel):
    lauf = subprocess.run([sys.executable, "-B", str(ziel / "bauen.py")], cwd=ziel, env=UMGEBUNG,
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    return lauf.returncode, lauf.stdout + lauf.stderr


def anwenden(mut, text):
    """Gibt (neuer Text, Trefferzahl) zurück."""
    if mut["regex"]:
        n = len(re.findall(mut["alt"], text, flags=re.S))
        return re.sub(mut["alt"], mut["neu"], text, count=0 if mut["alle"] else 1, flags=re.S), n
    return text.replace(mut["alt"], mut["neu"]), text.count(mut["alt"])


def pruefe_fragmente():
    for mut in MUTATIONEN:
        if mut["art"] == "weg":
            if not (WURZEL / mut["datei"]).is_file():
                sys.exit(f"ABBRUCH: {mut['name']}: {mut['datei']} fehlt schon")
            continue
        if mut["art"] == "neu":
            if (WURZEL / mut["datei"]).exists():
                sys.exit(f"ABBRUCH: {mut['name']}: {mut['datei']} gibt es schon")
            continue
        _, n = anwenden(mut, (WURZEL / mut["datei"]).read_text(encoding="utf-8"))
        if (mut["alle"] and n < 2) or (not mut["alle"] and n != 1):
            sys.exit(f"ABBRUCH: {mut['name']}: Fragment steht {n}-mal in {mut['datei']} "
                     f"(verlangt {'mindestens zweimal' if mut['alle'] else 'genau einmal'})")


def main():
    sys.stdout.reconfigure(errors="replace")
    pruefe_fragmente()
    fehl = 0
    with tempfile.TemporaryDirectory(prefix="kge-rotprobe-seiten-") as tmp:
        # Stand: Kopie grün, und nach einem Neubau der Kopie ebenfalls grün (Bau und Zeuge passen zusammen).
        stand = pathlib.Path(tmp) / "stand"
        kopie(stand)
        rc, _, ausgabe = zeuge(stand)
        if rc != 0:
            print(ausgabe)
            sys.exit("ABBRUCH: Der Zeuge ist schon ohne Mutation rot (Stand rot).")
        rc, ausgabe = baue(stand)
        rc2, _, ausgabe2 = zeuge(stand)
        if rc != 0 or rc2 != 0:
            print(ausgabe, ausgabe2)
            sys.exit("ABBRUCH: Nach dem Neubau der unveränderten Kopie ist der Zeuge rot oder der Bau bricht ab.")
        print("GRÜN  Stand: Kopie und neu gebaute Kopie bestehen den Zeugen")
        for i, mut in enumerate(MUTATIONEN):
            ziel = pathlib.Path(tmp) / f"m{i:02d}"
            kopie(ziel)
            pfad = ziel / mut["datei"]
            zusatz = ""
            if mut["art"] == "weg":
                pfad.unlink()
            elif mut["art"] == "neu":
                pfad.write_text(mut["neu"], encoding="utf-8", newline="")
            else:
                neu, n = anwenden(mut, pfad.read_text(encoding="utf-8"))
                pfad.write_text(neu, encoding="utf-8", newline="")
                zusatz = f" ({n} Stellen)" if mut["alle"] else ""
            if mut["art"] == "bau":
                rc, ausgabe = baue(ziel)
                if rc != 0:
                    fehl += 1
                    print(f"FEHL  {mut['name']} · der Neubau bricht ab, die Mutation prüft nichts: "
                          f"{ausgabe.strip().splitlines()[-1:]}")
                    shutil.rmtree(ziel, ignore_errors=True)
                    continue
            rc, rote, _ = zeuge(ziel)
            # Ein Absturz im erwarteten Fall ist kein Treffer: Er belegt nicht, dass der Fall die Regel prüft.
            treffer = [z for z in rote if z.startswith(f"ROT  {mut['fall']} ") and "AUSNAHME" not in z]
            if rc == 1 and treffer:
                andere = sorted({z.split()[1] for z in rote} - {mut["fall"]})
                print(f"ROT   {mut['name']}{zusatz} · {treffer[0][5:220]}"
                      + (f" · auch {', '.join(andere)}" if andere else ""))
            elif rc == 1:
                fehl += 1
                print(f"FEHL  {mut['name']} · rot, aber nicht im Fall {mut['fall']}: "
                      f"{', '.join(z.split()[1] for z in rote)}")
            else:
                fehl += 1
                print(f"GRÜN  {mut['name']} · der Zeuge merkt die Mutation nicht (rc {rc})")
            shutil.rmtree(ziel, ignore_errors=True)
    if fehl:
        print(f"ROTPROBE DURCHGEFALLEN: {fehl} von {len(MUTATIONEN)} Mutationen nicht im erwarteten Fall rot")
        sys.exit(1)
    print(f"ROTPROBE BESTANDEN: Stand grün, {len(MUTATIONEN)} von {len(MUTATIONEN)} Mutationen im erwarteten Fall rot")


if __name__ == "__main__":
    main()
