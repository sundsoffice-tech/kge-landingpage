#!/usr/bin/env python3
"""Zeuge für die Konfigurationssperre in bauen.py (konfig_fehler), vor allem labels.website_call.

Aufruf: python pruefen/zeuge_bauen.py   Exit 0, wenn jeder Fall stimmt, sonst Exit 1.
Geprüft wird die Funktion, die sperre_noindex bei NOINDEX = False aufruft: leer ist erlaubt (kein Nummerntausch),
ein Platzhalter mit X oder ein Label mit unzulässigen Zeichen ist ein Abbruch (Programmierer r1, Fund 7).
Dazu die Form der konfig.js des Repos, immer mit eigenen Testwerten: Der Zeuge hängt nicht daran, ob die Datei
gerade Platzhalter oder Kontowerte trägt, und bleibt am Tag der Kontoanlage grün.
"""
import pathlib
import re
import sys

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


def main():
    rot = 0
    for name, text, soll_abbruch in FAELLE:
        fehler = bauen.konfig_fehler(text)
        ok = bool(fehler) == soll_abbruch
        rot += 0 if ok else 1
        print(("ok   " if ok else "ROT  ") + name + ("" if ok else f" · gemeldet: {fehler!r}"))
    print(f"ROT: {rot} von {len(FAELLE)} weichen ab" if rot else f"GRÜN: {len(FAELLE)} Fälle stimmen")
    sys.exit(1 if rot else 0)


if __name__ == "__main__":
    main()
