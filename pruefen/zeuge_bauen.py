#!/usr/bin/env python3
"""Zeuge für die Konfigurationssperre in bauen.py (konfig_fehler), vor allem labels.website_call.

Aufruf: python pruefen/zeuge_bauen.py   Exit 0, wenn jeder Fall stimmt, sonst Exit 1.
Geprüft wird die Funktion, die sperre_noindex bei NOINDEX = False aufruft: leer ist erlaubt (kein Nummerntausch),
ein Platzhalter mit X oder ein Label mit unzulässigen Zeichen ist ein Abbruch (Programmierer r1, Fund 7).
Dazu die konfig.js des Repos selbst: Solange sie Platzhalter trägt, muss die Sperre greifen.
"""
import pathlib
import sys

HIER = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent))
import bauen  # noqa: E402


def konfig(tag="AW-1234567890", klick="LabKlick", wa="LabWa", form="LabForm", anruf='    website_call: ""\n'):
    return ('/* Beispiel im Kommentar: "AW-XXXXXXXXXX" */\nwindow.KGE_KONFIG = {\n'
            f'  googleTag: "{tag}",\n  labels: {{\n    phone_click: "{klick}",\n    whatsapp_click: "{wa}",\n'
            f'    form_submit: "{form}",\n{anruf}  }},\n  einwilligungsModus: "einfach"\n}};\n')


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
    ("konfig.js des Repos (Platzhalter bis zur Kontoanlage): Abbruch",
     (HIER.parent / "konfig.js").read_text(encoding="utf-8"), True),
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
