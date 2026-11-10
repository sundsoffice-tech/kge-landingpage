# Landingpage Kfz Gutachter Es: Aufbau, Bauen, Ausrollen

Stand 09.11.2026 (Neuaufbau auf Zweig `neu-2026-11-09`). Zielseite der Google-Ads-Kampagne ab 16.11.2026.

## Dateien

| Datei | Zweck |
|---|---|
| `vorlagen/schale.html` | Kopf, Fuß, Sticky-Callbar, Icon-Sprite, Skripte: steht genau einmal |
| `inhalte/<seite>.html` | Inhalt je Seite (`<main>` plus JSON-LD) |
| `bauen.py` | schreibt aus Schale und Inhalt die fertigen Seiten; `--pruefen` meldet Abweichungen (Exit 1) |
| `index.html` | Hauptseite Mönchengladbach (Hero, Kosten, Ablauf, Betrieb, FAQ, Orte, Rückruf-Formular) |
| `umland.html` | Variante für Viersen, Willich, Korschenbroich, Neuss, Kaarst, Grevenbroich |
| `ablauf.html`, `kosten.html`, `nachts-wochenende.html` | Sitelink-Zielseiten (Google lehnt Sitelinks auf Anker derselben Seite ab) |
| `impressum.html`, `datenschutz.html` | Pflichtseiten |
| `stil.css` | gemeinsames Stylesheet, Signaletik-Look (Skill `dossier`) |
| `konfig.js` | AW-ID, Conversion-Labels, Telefonanzeige, Lead-Endpunkt; Platzhalter bis zur Kontoanlage |
| `einwilligung.js` | Consent-Banner, Consent Mode v2 (default denied, update beim Klick), Google-Tag, Conversion-Aktionen |
| `formular.js` | Rückruf-Formular an `https://leads.sundsconnect.de/lead`, Erfolg erst nach `ok:true` |
| `schriften/` | Archivo (variable, woff2, latin und latin-ext), selbst gehostet |
| `bilder/` | Favicon; Betriebsfotos kommen hierher (Platzhalter `<!-- FOTO: ... -->` in den Inhalten) |

Die fertigen HTML-Dateien liegen im Repo, weil sie ohne Bauschritt ausgeliefert werden (sunds-hub, `ausrollen.sh`). Geändert wird in `inhalte/`,
`vorlagen/` oder `stil.css`, danach `python bauen.py`. Ein direkter Edit an `index.html` geht beim nächsten Bau verloren.

## Vor jedem Push prüfen

1. `python bauen.py --pruefen` (Exit 0).
2. Wörtersperre: `python <lm>/kunden/kfz-gutachter-es/kampagnen-vorbereitung/pruefen/woertersperre.py --ausnahme "Ismet Es Kfz Meisterbetrieb e.K." *.html` muss 0 Funde liefern. Die Ausnahme ist der Firmenname im Transparenzsatz des Impressums (Wettbewerbsrechtler 09.11.2026).
3. `impeccable detect index.html umland.html ablauf.html kosten.html nachts-wochenende.html impressum.html datenschutz.html` (Ziel 0 Funde).
4. Screenshots 390 und 1280 ansehen (Skill `hinsehen`, `schirmfoto.mjs` mit Geräteemulation; ein reines `--window-size=390` schneidet rechts ab).

## Staging und Live

- Auslieferung seit 10.11.2026: sunds-hub (Caddy, Snippet `kge_landingpage`), Zwischenadresse https://leads.sundsconnect.de/kge-vorschau/ mit `X-Robots-Tag: noindex`. Ausrollen nur mit `leadmaschine/kunden/kfz-gutachter-es/server/ausrollen.sh <archiv.tar> <commit>` (Archiv aus `git -c core.autocrlf=false archive --format=tar <commit>`); jeder Commit bekommt einen Ordner unter `/opt/kge-landingpage/`, `www` ist ein Symlink, Rückweg `ausrollen.sh zurueck <alter-commit>`.
- GitHub Pages (https://sundsoffice-tech.github.io/kge-landingpage/, Zweig `main`) ist nur noch der alte Staging-Stand. **Push nach `main` ist dort weiter ein Deploy**, deshalb nur über PR und nach Freigabe. Die Datenschutzerklärung nennt sunds-hub als Hosting; über GitHub Pages darf die Kampagne nicht laufen.
- Live-Domain: `unfall-mg.de` (Inhaber laut Vertrag Ziffer 6 Cihan Es, Kfz Gutachter Es). Canonical und alle Links sind relativ, die Seite läuft unter beiden Adressen ohne Änderung.

## Go-Live-Liste (Tag der Kontoanlage)

1. `konfig.js`: `googleTag` (AW-ID) und die drei Labels aus Google Ads > Tools > Conversions eintragen; `telefonAnzeige` muss der sichtbaren Nummer entsprechen.
2. Lead-Endpunkt: Origin `https://unfall-mg.de` in der CORS-Liste eintragen (gemessen 09.11.2026 00:47: OPTIONS mit diesem Origin antwortet 204 ohne `Access-Control-Allow-Origin`). Testlead mit Marker TEST, danach die Testdatei auf dem Server löschen (60-LEKTIONEN E4).
3. `bauen.py`: `NOINDEX = False`, neu bauen.
4. Betriebsfotos in `bilder/` legen, `<!-- FOTO: ... -->`-Platzhalter in `inhalte/index.html`, `inhalte/umland.html` ersetzen (`<img>` mit `width`, `height`, `alt`; Hero-Bild mit `fetchpriority="high"`).
5. DNS: A-Record `@` und `www` auf sunds-hub (169.58.211.51, gemessen 10.11.2026 über leads.sundsconnect.de), kein AAAA auf fremde Ziele; danach auf sunds-hub `domain_scharf.sh` (Trockenlauf), dann `--echt` (Caddy-Block, Zertifikat). GitHub Pages bekommt keine Custom Domain. Die früheren GitHub-Pages-A-Records gelten nicht mehr; HTTPS und Zertifikat stellt Caddy.
6. Prüfung vor dem ersten Klick: Tag Assistant zeigt `consent default denied`, nach „Erlauben“ `update granted`; Ablehnen-Pfad lädt nichts von googletagmanager.com; Testanruf über 60 Sekunden erscheint im Anrufbericht; Testlead kommt beim Kunden an.

## Messung ohne Konfiguration

Solange `konfig.js` Platzhalter trägt, lädt `einwilligung.js` kein Google-Skript und feuert keine Conversion, auch nach „Erlauben“ nicht; die Konsole meldet „Messung nicht konfiguriert“. Das Banner und die Speicherung der Entscheidung funktionieren trotzdem.
