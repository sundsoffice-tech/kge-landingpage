#!/usr/bin/env python3
"""Zeuge über die GEBAUTEN acht Seiten (index.html, ablauf.html, ... im Repo): die Regeln des Umbaus vom 23.11.2026,
die zeuge_bauen.py nicht sieht (Wissenschaftler S1, Codex-Gegenlauf Abschnitt 6 und 9). Rotprobe:
pruefen/rotprobe_seiten.py.

Aufruf: python pruefen/zeuge_seiten.py   Exit 0, wenn jeder Fall stimmt, sonst Exit 1.

Geprüft wird, was ausgeliefert wird, nicht das Bauergebnis im Speicher: Gleichheit von Datei und Bau prüft
python bauen.py --pruefen. Sollwerte kommen aus den Quellen, nicht aus einer zweiten Abschrift: Menü aus
bauen.MENUE, Seiten und Canonical aus bauen.SEITEN, Bilder aus bauen.BILDER, noindex aus bauen.NOINDEX, die
Rufnummer aus telefonAnzeige in konfig.js (bauen.RUF_ZEILE muss dazu passen, Fall R0). Nur die alte Nummer steht
hier als Muster; R3 sucht sie in den Seiten und in allen ausgelieferten Skripten und Stilen (*.js, *.css).

Fälle:
  P0  die acht Seiten aus SEITEN liegen gebaut im Repo, und keine andere HTML-Datei in der Wurzel
  M1  je Seite genau ein Handy-Menü (details.menue) und genau eine Kopfnavigation (nav.kopf-nav)
  M2  Ziele und Texte: Kopfnavigation = MENUE ohne Start, Handy-Menü = MENUE, in dieser Reihenfolge
  M3  aria-current="page" genau am Punkt der eigenen Seite, in beiden Menüs, sonst nirgends
  U0  Gegenprobe: der Textauszug trägt Titel und Beschreibung jeder Seite (sonst wäre U1 leer grün)
  U1  kein „Umland“ in Text (auch über Tags und &shy; hinweg), title, meta, alt, aria-*, Bildunterschrift, JSON-LD
      (auch nach Dekodieren der Unicode-Escapes) und ausgelieferten Skripten (href/src und umland.html zählen nicht)
  R0  Nummer aus konfig.js; bauen.RUF_ZEILE trägt dieselbe Anzeige und dasselbe tel-Ziel
  R1  je Seite die Anzeige der Nummer als sichtbarer Text
  R2  je Seite mindestens ein Link auf das tel-Ziel, kein anderes tel-Ziel
  R3  die alte Nummer in keiner Schreibweise, weder in den Seiten noch in den ausgelieferten Skripten
  B1  Zahl der figure = Zahl der img = Zahl der gezeigten Bildplätze = Zahl der Nachweiszeilen im Impressum
  B2  jedes img gehört zu einem gezeigten Platz, steht auf dessen Seite genau einmal, sein Nachweis steht im Impressum
  B3  Quellen: je Platz aus BILDER (auch leer) {{bild_<platz>}} genau einmal in inhalte/, {{bildnachweise}} im Impressum
  S1  kein „Symbolbild“-Etikett; jedes KI-Bild (BILDER[...]["ki"]) trägt „KI-erzeugtes Bild“ in seiner figure, jedes
      andere Schadenfoto „Beispielfoto“, außer bei Plätzen, die Betrieb oder Ort zeigen (BETRIEB_ODER_ORT);
      Richtungsvertrag Regel 5 und Nachtrag 01:55 (Rechtsauflagen), Richtung R1 24.11.2026
  S2  die Namenskarte („Ihr Sachverständiger“) steht nicht im selben Bildblock (Elternelement der figure) wie ein
      Schadenfoto (Nachtrag 01:55, erster Punkt)
  P1  noindex genau einmal je Seite, solange NOINDEX = True (sonst keins)
  P2  genau eine h1 je Seite
  P3  Canonical genau einmal, gleich SEITEN[...]["kanonisch"], und er zeigt auf die Seite selbst
  P4  alle internen Links, Quellen (href, src) und Anker lösen auf, in genauer Schreibweise und nur auf Ausgeliefertes
  P5  jede id je Seite höchstens einmal
  P6  Formular genau auf den Seiten, die formular.js laden, und formular.js genau dort, wo SEITEN es vorsieht
"""
import html
import json
import os
import pathlib
import posixpath
import re
import sys
import urllib.parse
from html.parser import HTMLParser

HIER = pathlib.Path(__file__).resolve().parent
WURZEL = HIER.parent
sys.path.insert(0, str(WURZEL))
import bauen  # noqa: E402

# Die alte Nummer in jeder Schreibweise mit bis zu sechs Trennzeichen zwischen den Gruppen (auch &nbsp;).
ALTE_NUMMER = re.compile(r"622[^0-9]{0,6}57[^0-9]{0,6}68|6225768")
# Plätze, deren Bild den Betrieb oder den Ort zeigt: Dort ist keine „Symbolbild“-Unterschrift verlangt. Ein neuer
# Platz steht nicht hier und braucht damit „Symbolbild“, bis jemand ihn bewusst einträgt (Wissenschaftler S1, 5).
BETRIEB_ODER_ORT = {
    "ort": "zeigt den Ort: Münster St. Vitus, Mönchengladbach",
}
# Ausgelieferte Skripte und Stile (DEPLOY.md, git archive): alle *.js und *.css der Wurzel, nicht eine feste
# Liste, damit eine neue Datei mitgeprüft wird (Programmierer KANN 8). Dort darf weder die alte Nummer noch
# „Umland“ stehen: Skripte blenden Text ein (Programmierer SOLL 4).
SKRIPTE = tuple(sorted(d.name for d in WURZEL.iterdir() if d.suffix in (".js", ".css")))
# Attribute, deren Wert als Text gilt (Vorleser, Suchmaschine, Tooltip). href/src/class/id sind Adressen oder Namen.
TEXT_ATTRIBUTE = {"alt", "title", "content", "placeholder", "value", "label"}
AUSSEN = ("http:", "https:", "mailto:", "tel:", "data:", "//")


def norm(text):
    """Leerraum vereinheitlichen. Zeichenreferenzen löst der Parser schon auf; Rohtext entschlüsselt der Aufrufer."""
    return " ".join(text.replace("\xa0", " ").replace("\xad", "").split())  # &shy; trennt nur optisch


class Seite(HTMLParser):
    """Liest eine gebaute Seite einmal und hält, was die Fälle brauchen."""

    def __init__(self, name, roh):
        super().__init__(convert_charrefs=True)
        self.name, self.roh = name, roh
        self.text, self.attr_text, self.jsonld = [], [], []
        self.ids, self.verweise, self.links, self.figuren, self.imgs = [], [], [], [], []
        self.kopf_navs = self.menues = self.h1 = self.formulare = 0
        self.robots, self.kanonisch, self.skripte = [], [], []
        self._skript = self._stil = False
        self._ld = False
        self._ort = None  # "kopf" oder "menue", solange ein Menü offen ist
        self._link = None
        self._figur = None
        self._unterschrift = False
        self.feed(roh)
        self.close()

    def handle_starttag(self, tag, attrs):
        a = {}
        for k, v in attrs:  # doppeltes Attribut: wie im Browser gilt das erste
            a.setdefault(k, v or "")
        klassen = re.split(r"[ \t\n\f\r]+", a.get("class", "").strip())  # nur ASCII-Leerraum trennt Klassen
        if "id" in a:
            self.ids.append(a["id"])
        for k, v in a.items():
            if k in TEXT_ATTRIBUTE or k.startswith("aria-"):
                if not (tag == "meta" and a.get("name") in ("viewport", "theme-color", "robots")) \
                        and k != "aria-hidden" and k != "aria-current":
                    self.attr_text.append(f"{tag}[{k}]={v}")
            if k in ("href", "src"):
                self.verweise.append((tag, k, v, self.getpos()[0]))
        if tag == "script":
            self._skript = True
            art = a.get("type", "").strip().lower()
            self._ld = art == "application/ld+json"
            if a.get("src") and art in ("", "text/javascript", "application/javascript", "module"):
                src = a["src"].strip()
                self.skripte.append(src[2:] if src.startswith("./") else src)
        elif tag == "style":
            self._stil = True
        elif tag == "nav" and "kopf-nav" in klassen:
            self.kopf_navs += 1
            self._ort = "kopf"
        elif tag == "details" and "menue" in klassen:
            self.menues += 1
            self._ort = "menue"
        elif tag == "a":
            self._link = {"ort": self._ort, "href": a.get("href"), "aktuell": a.get("aria-current"), "text": []}
            self.links.append(self._link)
        elif tag == "h1":
            self.h1 += 1
        elif tag == "form":
            self.formulare += 1
        elif tag == "meta" and a.get("name", "").lower() == "robots":
            self.robots.append(a.get("content", ""))
        elif tag == "link" and "canonical" in a.get("rel", "").lower().split():
            self.kanonisch.append(a.get("href", ""))
        elif tag == "figure":
            self._figur = {"imgs": [], "unterschrift": []}
            self.figuren.append(self._figur)
        elif tag == "figcaption":
            self._unterschrift = True
        if tag == "img":
            bild = {"src": a.get("src", ""), "alt": a.get("alt", ""), "breite": a.get("width", ""),
                    "hoehe": a.get("height", ""), "in_figur": self._figur is not None}
            self.imgs.append(bild)
            if self._figur is not None:
                self._figur["imgs"].append(bild)

    def handle_endtag(self, tag):
        if tag == "script":
            self._skript = self._ld = False
        elif tag == "style":
            self._stil = False
        elif tag in ("nav", "details") and self._ort:
            if (tag == "nav" and self._ort == "kopf") or (tag == "details" and self._ort == "menue"):
                self._ort = None
        elif tag == "a":
            self._link = None
        elif tag == "figure":
            self._figur = None
        elif tag == "figcaption":
            self._unterschrift = False

    def handle_data(self, data):
        if self._skript:
            if self._ld:
                self.jsonld.append(data)
            return
        if self._stil:
            return
        self.text.append(data)
        if self._link is not None:
            self._link["text"].append(data)
        if self._unterschrift and self._figur is not None:
            self._figur["unterschrift"].append(data)
        if self._figur is not None:
            self._figur.setdefault("text", []).append(data)

    @property
    def sichtbar(self):
        return norm(" ".join(self.text))

    @property
    def zusammen(self):
        """Text ohne Trenner zwischen den Knoten: so liest das Auge Um<span>land</span> oder 622<span>57</span>68."""
        return norm("".join(self.text))


def lade():
    seiten = {}
    for name in bauen.SEITEN:
        pfad = WURZEL / name
        if pfad.is_file():
            seiten[name] = Seite(name, pfad.read_text(encoding="utf-8"))
    return seiten


SEITEN = lade()
_FREMD = {}


def seite_von(datei):
    """Geparste Seite zu einem Dateinamen; auch für Ziele außerhalb von SEITEN (nur gelesen, wenn verlinkt)."""
    if datei in SEITEN:
        return SEITEN[datei]
    if datei not in _FREMD:
        _FREMD[datei] = Seite(datei, (WURZEL / datei).read_text(encoding="utf-8"))
    return _FREMD[datei]


def nummer():
    """(Anzeige, tel-Ziel) aus konfig.js, telefonAnzeige."""
    treffer = re.findall(r'^\s*telefonAnzeige:\s*"([^"]*)"', (WURZEL / "konfig.js").read_text(encoding="utf-8"), re.M)
    if len(treffer) != 1 or not treffer[0].strip():
        raise ValueError(f"konfig.js: telefonAnzeige {len(treffer)}-mal statt einmal oder leer")
    ziffern = re.sub(r"\D", "", treffer[0])
    if not ziffern.startswith("0") or len(ziffern) < 8:
        raise ValueError(f"konfig.js: telefonAnzeige ist keine Ortsnummer: {treffer[0]!r}")
    return treffer[0], "tel:+49" + ziffern[1:]


def eigen(name):
    return "./" if name == "index.html" else name


# --- Fälle: jeder gibt eine Liste von Verstößen zurück, leer heißt grün -----------------------------------------

def p0():
    fremd = sorted(d.name for d in WURZEL.glob("*.html") if d.name not in bauen.SEITEN)
    return [f"{n} fehlt im Repo" for n in bauen.SEITEN if n not in SEITEN] + \
        ([] if len(bauen.SEITEN) == 8 else [f"SEITEN hat {len(bauen.SEITEN)} statt 8 Seiten"]) + \
        [f"{d} liegt im Repo, steht aber nicht in SEITEN (würde ungeprüft ausgeliefert)" for d in fremd]


def m1():
    v = []
    for n, s in SEITEN.items():
        if s.menues != 1:
            v.append(f"{n}: {s.menues} Handy-Menüs statt 1")
        if s.kopf_navs != 1:
            v.append(f"{n}: {s.kopf_navs} Kopfnavigationen statt 1")
    return v


def m2():
    v = []
    soll_menue = [(z, t) for z, t in bauen.MENUE]
    soll_kopf = [(z, t) for z, t in bauen.MENUE if z != "./"]
    for n, s in SEITEN.items():
        for ort, soll in (("kopf", soll_kopf), ("menue", soll_menue)):
            ist = [(l["href"], norm("".join(l["text"]))) for l in s.links if l["ort"] == ort]
            if ist != soll:
                v.append(f"{n} {ort}: {ist} statt {soll}")
    return v


def m3():
    v = []
    for n, s in SEITEN.items():
        for l in s.links:
            if l["aktuell"] is None:
                if l["ort"] and l["href"] == eigen(n):
                    v.append(f"{n} {l['ort']}: eigener Punkt {l['href']} ohne aria-current")
                continue
            if l["ort"] is None:
                v.append(f"{n}: aria-current außerhalb der Menüs an {l['href']}")
            elif l["href"] != eigen(n) or l["aktuell"] != "page":
                v.append(f"{n} {l['ort']}: aria-current={l['aktuell']!r} an {l['href']}, eigene Seite ist {eigen(n)}")
    return v


def u0():
    v = []
    for n, s in SEITEN.items():
        meta = bauen.SEITEN[n]
        if norm(meta["titel"]) not in s.sichtbar:
            v.append(f"{n}: Titel nicht im Textauszug")
        if not any(norm(meta["beschreibung"]) in norm(t) for t in s.attr_text):
            v.append(f"{n}: Beschreibung nicht im Attributauszug")
    return v


def u1():
    v = []
    muster = re.compile(r"umland", re.I)
    for n, s in SEITEN.items():
        orte = [("Text", s.sichtbar), ("Text ohne Trenner", s.zusammen)] + \
               [("Attribut", norm(t)) for t in s.attr_text] + [("JSON-LD", norm(j)) for j in s.jsonld]
        for j in s.jsonld:  # \u-Escapes: erst nach dem Dekodieren lesbar
            try:
                orte.append(("JSON-LD dekodiert", json.dumps(json.loads(j), ensure_ascii=False)))
            except ValueError as e:
                v.append(f"{n}: JSON-LD nicht lesbar: {e}")
        for art, t in orte:
            for m in muster.finditer(t):
                v.append(f"{n} {art}: …{t[max(0, m.start() - 40):m.end() + 20]}…")
    for d in SKRIPTE:  # Text aus Skripten; der Dateiname umland.html als Ziel zählt wie in href nicht
        t = (WURZEL / d).read_text(encoding="utf-8").replace("umland.html", "")
        for m in muster.finditer(t):
            v.append(f"{d}: …{t[max(0, m.start() - 40):m.end() + 20]}…")
    return v


def r0():
    anzeige, ziel = nummer()
    v = []
    if anzeige not in bauen.RUF_ZEILE:
        v.append(f"bauen.RUF_ZEILE ohne Anzeige {anzeige!r}")
    if f'href="{ziel}"' not in bauen.RUF_ZEILE:
        v.append(f"bauen.RUF_ZEILE ohne href={ziel}")
    return v


def r1():
    anzeige, _ = nummer()
    return [f"{n}: Anzeige {anzeige!r} fehlt im sichtbaren Text" for n, s in SEITEN.items()
            if norm(anzeige) not in s.sichtbar]


def r2():
    _, ziel = nummer()
    v = []
    for n, s in SEITEN.items():
        tel = [urllib.parse.unquote(w).replace(" ", "") for _, k, w, _ in s.verweise
               if w.strip().lower().startswith("tel:")]
        # Anklickbar ist nur <a href>: ein tel: in src oder an einem anderen Element zählt nicht als Link.
        anklickbar = [urllib.parse.unquote(l["href"] or "").replace(" ", "") for l in s.links]
        if ziel not in anklickbar:
            v.append(f"{n}: kein <a href> auf {ziel}")
        v += [f"{n}: fremdes tel-Ziel {t}" for t in tel if t != ziel]
    return v


def r3():
    v = []
    # Seiten roh und als Text ohne Trenner (622<span>57</span>68 liest sich wie 6225768), dazu die Skripte.
    texte = [(n, s.roh) for n, s in SEITEN.items()] + [(n + " (Text)", s.zusammen) for n, s in SEITEN.items()] + \
            [(d, (WURZEL / d).read_text(encoding="utf-8")) for d in SKRIPTE]
    for name, roh in texte:
        for fassung in (roh, html.unescape(roh), urllib.parse.unquote(html.unescape(roh))):
            m = ALTE_NUMMER.search(fassung)
            if m:
                v.append(f"{name}: alte Nummer {m.group(0)!r}")
                break
    return v


def gezeigt():
    """Die Plätze, deren Bild der Bau zeigt (bauen.bild_html nicht leer), in der Reihenfolge von BILDER."""
    return [p for p in bauen.BILDER if bauen.bild_html(p)]


def nachweiszeilen():
    imp = SEITEN.get("impressum.html")
    if imp is None:
        return None
    roh = re.sub(r"<!--.*?-->", "", imp.roh, flags=re.S)  # ein auskommentierter Block ist nicht veröffentlicht
    m = re.findall(r"<h2>\s*Bildnachweise\s*</h2>\s*<p>(.*?)</p>", roh, re.S | re.I)
    if len(m) > 1:
        return ["DOPPELT"] * 99
    zeilen = re.split(r"<br\s*/?>", m[0], flags=re.I) if m else []
    return [norm(html.unescape(re.sub(r"<[^>]+>", "", z))) for z in zeilen]


def b1():
    figuren = sum(len(s.figuren) for s in SEITEN.values())
    imgs = sum(len(s.imgs) for s in SEITEN.values())
    plaetze = len(gezeigt())
    zeilen = nachweiszeilen()
    zeilen = -1 if zeilen is None else len(zeilen)
    if len({figuren, imgs, plaetze, zeilen}) != 1:
        return [f"figure {figuren}, img {imgs}, gezeigte Plätze {plaetze}, Nachweiszeilen {zeilen}"]
    return []


def quelle(datei):
    """Text einer Inhaltsquelle ohne HTML-Kommentare (bauen.py entfernt sie, ein Platzhalter darin wirkt nicht)."""
    return re.sub(r"<!--.*?-->", "", datei.read_text(encoding="utf-8"), flags=re.S)


def platz_seite(platz):
    """Die Inhaltsseiten, in denen der Platzhalter des Platzes steht."""
    return [d.name for d in sorted((WURZEL / "inhalte").glob("*.html")) if "{{bild_" + platz + "}}" in quelle(d)]


def b2():
    v = []
    nach_datei = {bauen.BILDER[p]["datei"]: p for p in gezeigt()}
    zeilen = nachweiszeilen() or []
    gesehen = {}
    for n, s in SEITEN.items():
        for b in s.imgs:
            platz = nach_datei.get(b["src"])
            if platz is None:
                v.append(f"{n}: Bild {b['src']} gehört zu keinem gezeigten Platz, also ohne Nachweis")
                continue
            gesehen.setdefault(platz, []).append(n)
            if not b["in_figur"]:
                v.append(f"{n}: Bild {b['src']} steht außerhalb einer figure")
            if not (b["alt"].strip() and b["breite"].isdigit() and b["hoehe"].isdigit()):
                v.append(f"{n}: Bild {b['src']} ohne alt, width oder height")
            if norm(bauen.BILDER[platz]["nachweis"]) not in zeilen:
                v.append(f"{n}: Bild {b['src']} (Platz {platz}) ohne Nachweiszeile im Impressum")
    for p in gezeigt():
        ist = gesehen.get(p, [])
        soll = platz_seite(p)
        if len(ist) != 1 or ist != soll:
            v.append(f"Platz {p}: gezeigt auf {ist}, Platzhalter in inhalte/{soll}")
    return v


def b3():
    v = []
    # Alle Plätze, auch die heute leeren: Fehlt der Platzhalter eines leeren Platzes, verschwindet sein Bild
    # später still, sobald er belegt wird (Codex-Gegenlauf 23.11., 19:15).
    for p in bauen.BILDER:
        anzahl = sum(quelle(d).count("{{bild_" + p + "}}") for d in (WURZEL / "inhalte").glob("*.html"))
        if anzahl != 1:
            v.append(f"{{{{bild_{p}}}}} steht {anzahl}-mal statt einmal in inhalte/")
    if True:  # unabhängig davon, ob heute ein Bild gezeigt wird
        anzahl = quelle(WURZEL / "inhalte" / "impressum.html").count("{{bildnachweise}}")
        if anzahl != 1:
            v.append(f"{{{{bildnachweise}}}} steht {anzahl}-mal statt einmal in inhalte/impressum.html")
    return v


def s1():
    v = []
    nach_datei = {bauen.BILDER[p]["datei"]: p for p in bauen.BILDER if bauen.BILDER[p]["datei"]}
    for n, s in SEITEN.items():
        for f in s.figuren:
            unter = norm("".join(f["unterschrift"]))
            if unter.startswith("Symbolbild"):
                v.append(f"{n}: Unterschrift mit Etikett „Symbolbild“ vorn: {unter!r}")
            for b in f["imgs"]:
                platz = nach_datei.get(b["src"], "?")
                if platz in BETRIEB_ODER_ORT:
                    continue
                text = norm("".join(f.get("text", [])))
                ki = platz in bauen.BILDER and bauen.BILDER[platz].get("ki")
                soll = "KI-erzeugtes Bild" if ki else "Beispielfoto"
                if soll not in text:
                    v.append(f"{n}: Bild {b['src']} (Platz {platz}) ohne „{soll}“ in Marke oder Unterschrift: {text!r}")
    return v


class Bildblock(HTMLParser):
    """Merkt sich je offenem Element, ob darin die Namenskarte steht und ob ein Kind eine figure mit Schadenfoto ist
    (img oder source in einem picture; Treffer über jeden Dateinamen in src oder srcset)."""
    LEER = {"img", "br", "input", "meta", "link", "source", "hr", "wbr", "area", "base", "col", "embed", "track"}

    def __init__(self, schaden):
        super().__init__(convert_charrefs=True)
        self.schaden, self.stapel, self.funde = schaden, [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("img", "source"):
            namen = {a.get("src") or ""} | {t.split()[0] for t in (a.get("srcset") or "").split(",") if t.strip()}
            treffer = sorted(namen & self.schaden)
            if treffer:
                i = len(self.stapel) - 1
                if i >= 0 and self.stapel[i]["tag"] == "picture":
                    i -= 1
                if i >= 1 and self.stapel[i]["tag"] == "figure":
                    self.stapel[i - 1]["foto"] = treffer[0]
        if tag not in self.LEER:
            self.stapel.append({"tag": tag, "name": False, "foto": None})

    def handle_endtag(self, tag):
        while self.stapel:
            e = self.stapel.pop()
            if e["name"] and e["foto"]:
                self.funde.append(f"<{e['tag']}> mit Namenskarte und Schadenfoto {e['foto']}")
            if e["tag"] == tag:
                break

    def handle_data(self, data):
        if "Ihr Sachverständiger" in data:
            for e in self.stapel:
                e["name"] = True


def schadendateien():
    """Alle Dateien der gezeigten Schadenfotos (alle Breiten und der schmale Anschnitt)."""
    dateien = set()
    for p in gezeigt():
        if p in BETRIEB_ODER_ORT:
            continue
        b = bauen.BILDER[p]
        dateien |= {b["datei"], *bauen.varianten(b)} if hasattr(bauen, "varianten") else {b["datei"]}
    return dateien


def s2():
    v = []
    schaden = schadendateien()
    for n, s in SEITEN.items():
        b = Bildblock(schaden)
        b.feed(s.roh)
        b.close()
        v += [f"{n}: {f}" for f in b.funde]
    return v


def p1():
    v = []
    for n, s in SEITEN.items():
        noindex = [r for r in s.robots if "noindex" in [w.strip().lower() for w in r.split(",")]]
        if bauen.NOINDEX and (len(noindex) != 1 or len(s.robots) != 1):
            v.append(f"{n}: robots {s.robots}, verlangt genau ein noindex (NOINDEX = True)")
        if not bauen.NOINDEX and noindex:
            v.append(f"{n}: noindex steht, obwohl NOINDEX = False")
    return v


def p2():
    return [f"{n}: {s.h1} h1 statt 1" for n, s in SEITEN.items() if s.h1 != 1]


def ziel_datei(pfad, von):
    """Relativer Verweis -> Datei relativ zur Wurzel ('./' -> index.html, '../' bleibt '../index.html')."""
    if pfad == "":
        return von
    if pfad == ".":
        pfad = "./"
    if pfad.endswith("/"):
        pfad += "index.html"
    return posixpath.normpath(pfad)


def nicht_ausgeliefert():
    """Pfade mit export-ignore in .gitattributes: liegen im Repo, fehlen aber auf dem Webserver (DEPLOY.md)."""
    datei = WURZEL / ".gitattributes"
    if not datei.is_file():
        return set()
    return set(re.findall(r"^(\S+)\s+export-ignore", datei.read_text(encoding="utf-8"), re.M))


def genau_vorhanden(rel):
    """Datei vorhanden, mit genau dieser Groß- und Kleinschreibung (Windows fände KOSTEN.html auch als kosten.html)."""
    if rel.startswith("../") or rel == ".." or posixpath.isabs(rel):
        return False
    ort = WURZEL
    for teil in rel.split("/"):
        if not ort.is_dir() or teil not in os.listdir(ort):
            return False
        ort = ort / teil
    return ort.is_file()


def p3():
    v = []
    for n, s in SEITEN.items():
        soll = bauen.SEITEN[n]["kanonisch"]
        if s.kanonisch != [soll]:
            v.append(f"{n}: canonical {s.kanonisch} statt [{soll!r}]")
        elif ziel_datei(soll, n) != n:
            v.append(f"{n}: canonical {soll} zeigt auf {ziel_datei(soll, n)}")
    return v


def p4():
    v = []
    ausgenommen = nicht_ausgeliefert()
    for n, s in SEITEN.items():
        for tag, k, wert, zeile in s.verweise:
            w = wert.strip()
            if not w or w.lower().startswith(AUSSEN):
                if not w:
                    v.append(f"{n}:{zeile} leeres {k} an <{tag}>")
                continue
            if w.lower().startswith("javascript:"):
                v.append(f"{n}:{zeile} javascript:-Verweis")
                continue
            teile = urllib.parse.urlsplit(w)
            datei = ziel_datei(urllib.parse.unquote(teile.path), n)
            if not genau_vorhanden(datei):
                v.append(f"{n}:{zeile} <{tag} {k}={w!r}>: Datei {datei} fehlt (genaue Schreibweise)")
                continue
            if datei.split("/")[0] in ausgenommen or datei in ausgenommen:
                v.append(f"{n}:{zeile} <{tag} {k}={w!r}>: {datei} wird nicht ausgeliefert (export-ignore)")
                continue
            if teile.fragment:
                if not datei.endswith(".html"):
                    v.append(f"{n}:{zeile} Anker auf Nicht-HTML {w!r}")
                elif urllib.parse.unquote(teile.fragment) not in seite_von(datei).ids:
                    v.append(f"{n}:{zeile} <{tag} {k}={w!r}>: Anker #{teile.fragment} fehlt in {datei}")
    return v


def p5():
    v = []
    for n, s in SEITEN.items():
        doppelt = sorted({i for i in s.ids if s.ids.count(i) > 1})
        if doppelt:
            v.append(f"{n}: ids doppelt {doppelt}")
    return v


def p6():
    v = []
    soll = {n for n, m in bauen.SEITEN.items() if "formular.js" in m["skripte"]}
    if not soll:
        v.append("SEITEN: keine Seite lädt formular.js (Sollmenge leer)")
    for n, s in SEITEN.items():
        laedt = s.skripte.count("formular.js")
        formular = s.formulare
        if (n in soll) != (laedt == 1) or laedt > 1:
            v.append(f"{n}: formular.js {laedt}-mal geladen, laut SEITEN {'ja' if n in soll else 'nein'}")
        if (formular > 0) != (laedt > 0):
            v.append(f"{n}: {formular} Formular(e), formular.js {laedt}-mal")
    return v


FAELLE = [
    ("P0", "die acht Seiten aus SEITEN liegen gebaut im Repo", p0),
    ("M1", "je Seite genau ein Handy-Menü und genau eine Kopfnavigation", m1),
    ("M2", "Menüziele und -texte gleich MENUE (Kopf ohne Start, Handy-Menü vollständig)", m2),
    ("M3", "aria-current genau am Punkt der eigenen Seite, sonst nirgends", m3),
    ("U0", "Gegenprobe: Textauszug trägt Titel und Beschreibung jeder Seite", u0),
    ("U1", "kein „Umland“ in Text, title, meta, alt, aria, Bildunterschrift, JSON-LD", u1),
    ("R0", "Nummer aus konfig.js, RUF_ZEILE in bauen.py passt dazu", r0),
    ("R1", "je Seite die Nummer als sichtbarer Text", r1),
    ("R2", "je Seite mindestens ein tel-Link auf die Nummer, kein anderes tel-Ziel", r2),
    ("R3", "alte Nummer in keiner Schreibweise (Seiten und ausgelieferte Skripte)", r3),
    ("B1", "figure = img = gezeigte Bildplätze = Nachweiszeilen im Impressum", b1),
    ("B2", "jedes Bild gehört zu einem Platz, steht auf dessen Seite und hat seinen Nachweis", b2),
    ("B3", "Platzhalter der gezeigten Plätze und {{bildnachweise}} stehen je genau einmal in den Quellen", b3),
    ("S1", "kein „Symbolbild“-Etikett; KI-Bilder mit „KI-erzeugtes Bild“, andere Schadenfotos mit „Beispielfoto“", s1),
    ("S2", "Namenskarte nicht im selben Bildblock wie ein Schadenfoto", s2),
    ("P1", "noindex genau einmal je Seite, solange NOINDEX = True", p1),
    ("P2", "genau eine h1 je Seite", p2),
    ("P3", "Canonical genau einmal, aus SEITEN, zeigt auf die Seite selbst", p3),
    ("P4", "interne Links, Quellen und Anker lösen auf", p4),
    ("P5", "ids je Seite eindeutig", p5),
    ("P6", "Formular genau auf den Seiten, die formular.js laden (laut SEITEN)", p6),
]


def main():
    sys.stdout.reconfigure(errors="replace")
    rot = 0
    for kennung, name, fall in FAELLE:
        try:
            verstoesse = fall()
        except Exception as e:  # ein Absturz ist rot, nie grün
            verstoesse = [f"AUSNAHME {type(e).__name__}: {e}"]
        rot += 1 if verstoesse else 0
        if verstoesse:
            rest = f" (+{len(verstoesse) - 3} weitere)" if len(verstoesse) > 3 else ""
            print(f"ROT  {kennung} {name} · " + " | ".join(verstoesse[:3]) + rest)
        else:
            print(f"ok   {kennung} {name}")
    print(f"ROT: {rot} von {len(FAELLE)} weichen ab" if rot else f"GRÜN: {len(FAELLE)} Fälle stimmen")
    sys.exit(1 if rot else 0)


if __name__ == "__main__":
    main()
