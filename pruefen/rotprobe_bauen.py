#!/usr/bin/env python3
"""Rotprobe für pruefen/zeuge_bauen.py: Jede Mutation nimmt aus bauen.py genau eine Regel heraus, und der Zeuge muss
dann rot werden. Bleibt er grün, prüft er die Regel nicht (Programmierer r2, F2).

Aufruf: python pruefen/rotprobe_bauen.py   Exit 0, wenn der Stand grün ist und jede Mutation rot macht, sonst Exit 1.
Gerechnet wird in einer Kopie in einem Temp-Ordner (bauen.py, konfig.js, *.css, vorlagen/, inhalte/, bilder/,
pruefen/zeuge_bauen.py); seit Runde 6 zählt nur ein Rot im benannten Fall (ERWARTET), nicht irgendeine rote Zeile;
der Arbeitsbaum bleibt unberührt. Jede Mutation ersetzt eine Zeichenkette, die in bauen.py genau einmal stehen muss,
sonst bricht die Probe ab (eine Mutation, die nichts trifft, wäre eine grüne Lüge).
"""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HIER = pathlib.Path(__file__).resolve().parent
WURZEL = HIER.parent

MUTATIONEN = [
    ("R1 Zeilenregel läuft wieder über --> hinweg (alter Fehler F3)",
     r'text = re.sub(r"^[ \t]*<!--(?:(?!-->).)*-->[ \t]*\n"',
     r'text = re.sub(r"^[ \t]*<!--.*?-->[ \t]*\n"'),
    ("R2 Kommentare mitten in der Zeile bleiben stehen",
     r'return re.sub(r"[ \t]*<!--(?:(?!-->).)*-->", "", text, flags=re.S)',
     'return text'),
    ("R3 Kommentarsperre im Bau entfernt",
     '    if "<!--" in seite:\n',
     '    if False:\n'),
    ("R4 Leerprüfung der fünf Werte entfernt",
     '    if leer:\n        return f"BEWERTUNG_ZEIGEN ist an, aber leer',
     '    if False:\n        return f"BEWERTUNG_ZEIGEN ist an, aber leer'),
    ("R5 SEIT ohne Formprüfung (vierstellig)",
     r're.fullmatch(r"\d{4}", seit) and ',
     ''),
    ("R6 SEIT ohne Untergrenze 2005",
     'BEWERTUNG_SEIT_FRUEHESTENS <= int(seit) <= heute.year',
     'int(seit) <= heute.year'),
    ("R7 SEIT ohne Obergrenze laufendes Jahr",
     'BEWERTUNG_SEIT_FRUEHESTENS <= int(seit) <= heute.year',
     'BEWERTUNG_SEIT_FRUEHESTENS <= int(seit)'),
    ("R8 Stand in der Zukunft erlaubt",
     '    if (heute - stand).days < 0:\n',
     '    if False:\n'),
    ("R9 Stand bis 15 Tage gilt nicht als veraltet",
     '.days > BEWERTUNG_HOECHSTALTER_TAGE\n',
     '.days > BEWERTUNG_HOECHSTALTER_TAGE + 1\n'),
    ("R10 Datumsformat JJJJ-MM-TT statt TT.MM.JJJJ",
     '        stand = datetime.datetime.strptime(BEWERTUNG_STAND, "%d.%m.%Y")',
     '        stand = datetime.datetime.strptime(BEWERTUNG_STAND, "%Y-%m-%d")'),
    ("R11 Profilform erlaubt http",
     r'BEWERTUNG_PROFIL_FORM = r"https://',
     r'BEWERTUNG_PROFIL_FORM = r"https?://'),
    ("R12 Profilprüfung des Links entfernt",
     '    if not re.fullmatch(BEWERTUNG_PROFIL_FORM, BEWERTUNG_LINK):\n',
     '    if False:\n'),
    ("R13 Kartensuche-Sperre bei NOINDEX aus entfernt",
     'if BEWERTUNG_ZEIGEN and "/maps/search/" in BEWERTUNG_LINK:',
     'if False:'),
    ("R14 Zeile {{vertrauen}} bleibt bei leerem Inhalt stehen",
     '    if not vertrauen_html:',
     '    if False:'),
    ("R17 Bewertungskasten ohne Hinweis nach § 5b",
     "f'<p>{e(BEWERTUNG_HINWEIS)}</p></div>'",
     "'</div>'"),
    ("R18 veralteter Stand zeigt den Kasten trotzdem",
     '    if BEWERTUNG_ZEIGEN and not bewertung_veraltet():\n',
     '    if BEWERTUNG_ZEIGEN:\n'),
    ("R19 veralteter Stand bricht wieder ab statt wegzulassen",
     '        if fehler:\n            sys.exit(fehler)\n',
     '        if fehler or bewertung_veraltet():\n            sys.exit(fehler or "veraltet")\n'),
    ("R20 Bau und --pruefen melden den veralteten Stand nicht",
     '    if meldung:  # laut',
     '    if False:  # laut'),
    ("R21 Kundenbeleg ohne Formprüfung",
     'if not re.fullmatch(r"[A-Za-z0-9_-]{8}", BEWERTUNG_KUNDENBELEG) or re.search(r"X{4,}", BEWERTUNG_KUNDENBELEG, re.I):',
     'if False:'),
    ("R22 Kundenbeleg darf leer sein",
     ', "KUNDENBELEG": BEWERTUNG_KUNDENBELEG}',
     '}'),
    ("R23 Bildschirmfoto nicht verlangt",
     '    if not echt:\n',
     '    if False:\n'),
    ("R24 Bildschirmfoto ohne PNG-Prüfung (jede Datei reicht)",
     'echt = foto.read_bytes()[:8] == PNG_KOPF',
     'echt = foto.exists()'),
    ("R25 Bildschirmfoto zu einem beliebigen Tag",
     'return BELEGE / f"bewertung-{stand:%Y-%m-%d}.png"',
     'return next(BELEGE.glob("bewertung-*.png"), BELEGE / "fehlt.png")'),
    ("R15 Leerer Bildplatz: die Zeile bleibt als Leerzeile stehen",
     '        if not wert:  # leerer Platz',
     '        if False:  # leerer Platz'),
    ("R16 Hauptschalter FOTOS_ZEIGEN wirkt nicht",
     '    if not FOTOS_ZEIGEN or not b["datei"]',
     '    if not b["datei"]'),
    ("R26 Bildplatz: fehlende Bilddatei wird nicht bemerkt",
     '    if not (BILDWURZEL / datei).is_file():\n',
     '    if False:\n'),
    ("R27 Bildplatz: fehlender Bildnachweis wird nicht bemerkt",
     '    if not str(b["nachweis"]).strip():\n',
     '    if False:\n'),
    ("R28 Bildplatz: fehlender alt-Text wird nicht bemerkt",
     '    if not str(b["alt"]).strip():\n',
     '    if False:\n'),
    ("R29 Unvollständiger Bildplatz erscheint trotzdem",
     ' or bild_fehler(platz):',
     ':'),
    ("R36 KI-Bild ohne „mit KI erzeugt“ im Nachweis wird nicht bemerkt (Runde 4)",
     '    if b.get("ki") and KI_KENNWORT not in b["nachweis"]:\n',
     '    if False:\n'),
    ("R37 Nachweis im gebauten Impressum wird nicht mehr geprüft (Runde 5)",
     '    impressum_sperre(gebaut)\n',
     '    pass\n'),
    ("R38 Feld ki darf fehlen (Runde 5)",
     '    if not isinstance(b.get("ki"), bool):\n',
     '    if False:\n'),
    ("R30 Bildplatz: fehlende Maße werden nicht bemerkt",
     'b["breite"] > 0 and b["hoehe"] > 0',
     'True'),
    ("R31 vorrang wirkt nicht (kein fetchpriority)",
     'if b.get("vorrang") else',
     'if False else'),
    ("R32 sperre_bilder wird in main nicht mehr gerufen",
     '    sperre_bilder()\n',
     '    pass\n'),
    # R33 und R35: Mit --pruefen bricht main weiter mit „Bildplatz unfall“ ab, G12 bleibt also grün; schreibend
    # greift die Sperre gar nicht (R33) oder erst nach dem Schreiben (R35). Nur G13 sieht das (Programmierer KANN 3).
    ("R33 sperre_bilder nur noch bei --pruefen, nicht beim Schreiben",
     '    sperre_bilder()\n    pruefen = "--pruefen" in sys.argv\n',
     '    pruefen = "--pruefen" in sys.argv\n    if pruefen:\n        sperre_bilder()\n'),
    ("R35 sperre_bilder erst hinter der Seitenschleife, nach dem Schreiben",
     '    sperre_bilder()\n'
     '    pruefen = "--pruefen" in sys.argv\n'
     '    meldung = bewertung_meldung()\n'
     '    if meldung:  # laut, in Bau und Prüfung; der Exit bleibt davon unberührt\n'
     '        print(meldung)\n'
     '    gebaut = {name: bauen(name, meta) for name, meta in SEITEN.items()}\n'
     '    impressum_sperre(gebaut)\n'
     '    ausgabe_sperre(gebaut)\n'
     '    abweichungen = 0\n'
     '    for name in SEITEN:\n'
     '        neu = gebaut[name]\n'
     '        ziel = HIER / name\n'
     '        if pruefen:\n'
     '            alt = ziel.read_text(encoding="utf-8") if ziel.exists() else ""\n'
     '            if alt != neu:\n'
     '                print(f"ABWEICHUNG {name}")\n'
     '                abweichungen += 1\n'
     '        else:\n'
     '            ziel.write_text(neu, encoding="utf-8", newline="\\n")\n'
     '            print(f"{name}: {len(neu.encode(\'utf-8\'))} Bytes")\n',
     '    pruefen = "--pruefen" in sys.argv\n'
     '    meldung = bewertung_meldung()\n'
     '    if meldung:  # laut, in Bau und Prüfung; der Exit bleibt davon unberührt\n'
     '        print(meldung)\n'
     '    gebaut = {name: bauen(name, meta) for name, meta in SEITEN.items()}\n'
     '    impressum_sperre(gebaut)\n'
     '    ausgabe_sperre(gebaut)\n'
     '    abweichungen = 0\n'
     '    for name in SEITEN:\n'
     '        neu = gebaut[name]\n'
     '        ziel = HIER / name\n'
     '        if pruefen:\n'
     '            alt = ziel.read_text(encoding="utf-8") if ziel.exists() else ""\n'
     '            if alt != neu:\n'
     '                print(f"ABWEICHUNG {name}")\n'
     '                abweichungen += 1\n'
     '        else:\n'
     '            ziel.write_text(neu, encoding="utf-8", newline="\\n")\n'
     '            print(f"{name}: {len(neu.encode(\'utf-8\'))} Bytes")\n'
     '    sperre_bilder()\n'),
    ("R34 FOTOS_ZEIGEN = False schaltet die Bildsperre nicht mehr ab",
     '    if not FOTOS_ZEIGEN:\n        return\n    for platz in BILDER:',
     '    for platz in BILDER:'),
    # Runde 6, 4a: Einwilligungsmodus und Form des googleTag.
    ("R39 sperre_modus wird in main nicht mehr gerufen",
     '    sperre_modus()\n    sperre_noindex()\n',
     '    sperre_noindex()\n'),
    ("R40 modus_fehler nimmt jeden Modus",
     '    if modus != ["einfach"]:\n',
     '    if not modus:\n'),
    ("R41 googleTag nur noch „nicht leer“ statt AW- plus Ziffern",
     r'if len(tag) != 1 or not re.fullmatch(r"AW-\d{6,15}", tag[0]):',
     'if len(tag) != 1 or not tag[0]:'),
    # Runde 6, A1b: Nachweis sichtbar.
    ("R42 Sichtbarkeit des Nachweises in main nicht mehr geprüft",
     '    meldung = impressum_fehler(seiten) or nachweis_sichtbar_fehler(seiten.get("impressum.html", ""), stile())\n',
     '    meldung = impressum_fehler(seiten)\n'),
    ("R43 Attribut hidden zählt nicht als verborgen",
     ' or "hidden" in a or "inert" in a',
     ' or "inert" in a'),
    ("R44 aria-hidden zählt nicht als verborgen",
     'or a.get("aria-hidden", "").strip().lower() == "true"',
     'or False'),
    ("R45 template zählt nicht als verborgen",
     'VERBORGENE_TAGS = {"template", ',
     'VERBORGENE_TAGS = {'),
    ("R46 style-Attribut zählt nicht als verborgen",
     r'or bool(re.search(r"display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0(?![.\d])", stil))',
     'or False'),
    ("R47 verbergende Klasse aus den Stildateien zählt nicht",
     'or bool(set(a.get("class", "").split()) & self.klassen)',
     'or False'),
    ("R48 geschlossenes details zählt nicht als verborgen",
     'self.stapel.append((tag, verborgen, tag == "details" and "open" not in a))',
     'self.stapel.append((tag, verborgen, False))'),
    # Runde 6, A1a: url() nur auf schriften/.
    ("R49 url-Sperre prüft die Stildateien nicht mehr",
     '    quellen = dict(css_texte)\n',
     '    quellen = {}\n'),
    ("R50 @import erlaubt",
     r'        if re.search(r"@import|image-set\s*\(", text, flags=re.I):',
     '        if False:'),
    # Runde 6, Punkt 10: Bilder nur aus Bildplätzen.
    ("R51 ausgabe_sperre wird in main nicht mehr gerufen",
     '    impressum_sperre(gebaut)\n    ausgabe_sperre(gebaut)\n',
     '    impressum_sperre(gebaut)\n'),
    ("R52 Bildsperre der Seiten kennt nur noch img",
     r'BILD_MARKUP = re.compile(r"<(?:img|picture|source|image|video|object|embed|iframe)\b|\b(?:srcset|poster)\s*=|"',
     r'BILD_MARKUP = re.compile(r"<img\b|"'),
]

# Runde 6, Punkt 6 (Codex 3, Programmierer K4): Jede Mutation muss im benannten Fall rot werden, nicht irgendwo.
# Die Fälle sind die erste Kennung der Zeile im Zeugen (K1, G13, W5 …). Zuordnung gemessen am Stand ced80c1.
ERWARTET = {
    "R1": "K1", "R2": "K1", "R3": "S1", "R4": "B2", "R5": "J1", "R6": "J2", "R7": "J5", "R8": "B8", "R9": "A2",
    "R10": "B1", "R11": "L3", "R12": "L1", "R13": "N1", "R14": "V1", "R15": "F3", "R16": "F1", "R17": "V2",
    "R18": "A5", "R19": "A5", "R20": "A7", "R21": "B12", "R22": "B11", "R23": "P1", "R24": "P3", "R25": "P2",
    "R26": "G1", "R27": "G3", "R28": "G4", "R29": "G7", "R30": "G5", "R31": "G8", "R32": "G12", "R33": "G13",
    "R34": "G14", "R35": "G13", "R36": "G6a", "R37": "G17", "R38": "G6c",
    "R39": "W5", "R40": "W2", "R41": "T1", "R42": "H8", "R43": "H2", "R44": "H3", "R45": "H4", "R46": "H5",
    "R47": "H6", "R48": "H7", "R49": "U2", "R50": "U4", "R51": "I4", "R52": "I3",
}


def kopie(ziel):
    for name in ["bauen.py", "konfig.js"] + [d.name for d in WURZEL.glob("*.css")]:
        shutil.copy2(WURZEL / name, ziel / name)
    for ordner in ("vorlagen", "inhalte", "bilder"):
        shutil.copytree(WURZEL / ordner, ziel / ordner)
    (ziel / "pruefen").mkdir()
    shutil.copy2(HIER / "zeuge_bauen.py", ziel / "pruefen" / "zeuge_bauen.py")


def zeuge(ziel):
    umgebung = dict(os.environ, PYTHONIOENCODING="utf-8")  # sonst schreibt der Zeuge unter Windows cp1252
    lauf = subprocess.run([sys.executable, "-B", str(ziel / "pruefen" / "zeuge_bauen.py")], env=umgebung,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    rote = [z for z in lauf.stdout.splitlines() if z.startswith("ROT  ")]
    return lauf.returncode, rote, lauf.stdout + lauf.stderr


def main():
    sys.stdout.reconfigure(errors="replace")
    quelle =(WURZEL / "bauen.py").read_text(encoding="utf-8")
    for name, alt, neu in MUTATIONEN:
        n = quelle.count(alt)
        if n != 1:
            sys.exit(f"ABBRUCH: {name}: Ausgangstext steht {n}-mal statt einmal in bauen.py")
        if name.split()[0] not in ERWARTET:
            sys.exit(f"ABBRUCH: {name}: kein erwarteter Fall in ERWARTET")
    gruene = 0
    with tempfile.TemporaryDirectory(prefix="kge-rotprobe-") as tmp:
        ziel = pathlib.Path(tmp) / "baum"
        ziel.mkdir()
        kopie(ziel)
        rc, _, ausgabe = zeuge(ziel)
        if rc != 0:
            print(ausgabe)
            sys.exit("ABBRUCH: Der Zeuge ist schon ohne Mutation rot (Stand rot).")
        for name, alt, neu in MUTATIONEN:
            (ziel / "bauen.py").write_text(quelle.replace(alt, neu, 1), encoding="utf-8", newline="")
            rc, rote, ausgabe = zeuge(ziel)
            soll = ERWARTET[name.split()[0]]
            treffer = [z for z in rote if z[5:].split()[0] == soll]
            if rc == 1 and treffer:
                andere = sorted({z[5:].split()[0] for z in rote} - {soll})
                print(f"ROT   {name} · {treffer[0][5:200]}" + (f" · auch {', '.join(andere)}" if andere else ""))
            elif rc == 1:
                gruene += 1
                print(f"FEHL  {name} · rot, aber nicht im Fall {soll}: {', '.join(z[5:].split()[0] for z in rote)}")
            else:
                gruene += 1
                print(f"GRÜN  {name} · der Zeuge merkt die Mutation nicht (rc {rc})")
        (ziel / "bauen.py").write_text(quelle, encoding="utf-8", newline="")
    if gruene:
        print(f"ROTPROBE DURCHGEFALLEN: {gruene} von {len(MUTATIONEN)} Mutationen nicht im benannten Fall rot")
        sys.exit(1)
    print(f"ROTPROBE BESTANDEN: Stand grün, {len(MUTATIONEN)} von {len(MUTATIONEN)} Mutationen im benannten Fall rot")


if __name__ == "__main__":
    main()
