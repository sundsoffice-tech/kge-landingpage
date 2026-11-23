# Landingpage Kfz Gutachter Es: Aufbau, Bauen, Ausrollen

Stand 09.11.2026 (Neuaufbau auf Zweig `neu-2026-11-09`). Zielseite der Google-Ads-Kampagne ab 16.11.2026. Umbau zur Website mit Seitenmenü am 23.11.2026 (Zweig `kge/website-umbau-2026-11-23`), siehe Abschnitt „Seiten, Menü und Bildplätze“.

## Dateien

| Datei | Zweck |
|---|---|
| `vorlagen/schale.html` | Kopf, Fuß, Sticky-Callbar, Icon-Sprite, Skripte: steht genau einmal |
| `inhalte/<seite>.html` | Inhalt je Seite (`<main>` plus JSON-LD) |
| `bauen.py` | schreibt aus Schale und Inhalt die fertigen Seiten; `--pruefen` meldet Abweichungen (Exit 1) |
| `index.html` | Startseite (Kopf mit Name, Adressen und Anrufknopf, Versicherung des Gegners, Verweis auf die ersten Schritte, wer zahlt, Ablauf mit Gutachteninhalt, Über Cihan Es, Einsatzgebiet in zwei Sätzen, Fragen, Kontakt und Rückruf-Formular) |
| `umland.html` | Seite „Einsatzgebiet“ für Viersen, Willich, Korschenbroich, Neuss, Kaarst, Grevenbroich. Die Adresse bleibt, weil Anzeigen darauf zeigen; das Wort aus dem Dateinamen steht nirgends sichtbar |
| `kontakt.html` | „Kontakt und Anfahrt“: beide Adressen, Telefonzeiten, Rückruf-Formular |
| `ablauf.html` („Nach dem Unfall“), `kosten.html` („Wer zahlt?“), `nachts-wochenende.html` („Abends und am Wochenende“, nur im Fuß) | Fachseiten und Sitelink-Ziele (Google lehnt Sitelinks auf Anker derselben Seite ab) |
| `impressum.html`, `datenschutz.html` | Pflichtseiten |
| `stil.css` | gemeinsames Stylesheet, Signaletik-Look (Skill `dossier`) |
| `konfig.js` | AW-ID, Conversion-Labels, Telefonanzeige, Lead-Endpunkt; Platzhalter bis zur Kontoanlage |
| `einwilligung.js` | Consent-Banner, Consent Mode v2 (default denied, update beim Klick), Google-Tag, Conversion-Aktionen |
| `formular.js` | Rückruf-Formular an `https://leads.sundsconnect.de/lead`, Erfolg erst nach `ok:true` |
| `leiste.js` | blendet die Anrufleiste aus, solange der Anrufknopf im Hero zu sehen ist |
| `pruefen/` | Zeugen ohne Browser: `zeuge-einwilligung.js`, `rotprobe-einwilligung.js`, `zeuge_bauen.py`, `rotprobe_bauen.py`; werden nicht ausgeliefert |
| `.gitattributes` | nimmt Bauquellen und Zeugen aus `git archive` aus (`export-ignore`) |
| `schriften/` | Archivo (variable, woff2, latin und latin-ext), selbst gehostet |
| `bilder/` | Favicon und die Bilder der Bildplätze (in den Inhalten steht je Platz `{{bild_<name>}}`, die Tabelle `BILDER` in `bauen.py` schaltet jeden Platz einzeln) |

Die fertigen HTML-Dateien liegen im Repo, weil sie ohne Bauschritt ausgeliefert werden (sunds-hub, `ausrollen.sh`). Geändert wird in `inhalte/`,
`vorlagen/` oder `stil.css`, danach `python bauen.py`. Ein direkter Edit an `index.html` geht beim nächsten Bau verloren.

Ausgeliefert wird der Inhalt von `git archive`. `.gitattributes` nimmt `pruefen/`, `inhalte/`, `vorlagen/`, `bauen.py`,
`DEPLOY.md`, `belege/`, `.gitignore`, `.github` und sich selbst davon aus; ein Archiv ist deshalb die Auslieferung, kein
Arbeitsbaum. Zum Bauen und Prüfen einen Klon oder `git worktree add` nehmen. Probe nach jeder Änderung an
`.gitattributes` (git liest die Attribute aus dem archivierten Commit, also nach dem Commit messen):
`git archive HEAD | tar -t` zeigt die acht Seiten, `konfig.js`, `einwilligung.js`, `leiste.js`, `formular.js`,
`stil.css`, `bilder/`, `schriften/` und nichts aus der Liste oben.

## Vor jedem Push prüfen

1. `python bauen.py --pruefen` (Exit 0).
2. Wörtersperre: `python <lm>/kunden/kfz-gutachter-es/kampagnen-vorbereitung/pruefen/woertersperre.py --ausnahme "Ismet Es Kfz Meisterbetrieb e.K." *.html` muss 0 Funde liefern. Die Ausnahme ist der Firmenname im Transparenzsatz des Impressums (Wettbewerbsrechtler 09.11.2026). Mit `BEWERTUNG_ZEIGEN = True` kommt genau eine zweite Ausnahme dazu, nach Abschnitt „Bewertung und Name“, Schritt 6.
3. `impeccable detect index.html umland.html ablauf.html kosten.html kontakt.html nachts-wochenende.html impressum.html datenschutz.html` (Ziel 0 Funde).
4. Screenshots 390 und 1280 ansehen (Skill `hinsehen`, `schirmfoto.mjs` mit Geräteemulation; ein reines `--window-size=390` schneidet rechts ab).
5. Zeugen, jeder mit Exit 0: `node pruefen/zeuge-einwilligung.js` (Einwilligung, Nummerntausch, Widerruf), `node pruefen/rotprobe-einwilligung.js` (jede Mutation an `einwilligung.js` muss den Zeugen rot machen), `python pruefen/zeuge_bauen.py` (Sperren in `bauen.py`: Konfiguration, Bewertungskasten mit fester Uhr, Kommentare, Fotoschalter), `python pruefen/rotprobe_bauen.py` (jede herausgenommene Regel in `bauen.py` muss diesen Zeugen rot machen). Die Zeugen rechnen ohne Browser; Bild, Umbruch, Anrufleiste und das Ausweichen des Einwilligungsbalkens sehen sie nicht.

## Staging und Live

- Auslieferung seit 10.11.2026: sunds-hub (Caddy, Snippet `kge_landingpage`), Zwischenadresse https://leads.sundsconnect.de/kge-vorschau/ mit `X-Robots-Tag: noindex`. Ausrollen nur mit `leadmaschine/kunden/kfz-gutachter-es/server/ausrollen.sh <archiv.tar> <commit>` (Archiv aus `git -c core.autocrlf=false archive --format=tar <commit>`); jeder Commit bekommt einen Ordner unter `/opt/kge-landingpage/`, `www` ist ein Symlink, Rückweg `ausrollen.sh zurueck <alter-commit>`.
- GitHub Pages (https://sundsoffice-tech.github.io/kge-landingpage/, Zweig `main`) ist nur noch der alte Staging-Stand. **Push nach `main` ist dort weiter ein Deploy**, deshalb nur über PR und nach Freigabe. Die Datenschutzerklärung nennt sunds-hub als Hosting; über GitHub Pages darf die Kampagne nicht laufen.
- Live-Domain: `unfall-mg.de` (Inhaber laut Vertrag Ziffer 6 Cihan Es, Kfz Gutachter Es). Canonical und alle Links sind relativ, die Seite läuft unter beiden Adressen ohne Änderung.

## Go-Live-Liste

Am Tag der Kontoanlage sind die Schritte 1, 2, 6 und 7 dran. Schritt 5 (DNS) ist seit 16.11.2026 erledigt. Schritt 4 (Betriebsfotos) hängt an den Fotos des Kunden und an keinem der beiden Tage. Schritt 3 (`NOINDEX = False`) hängt nicht am Datum, sondern an zwei Bedingungen: Die Freigabe des Kunden liegt mit Beleg vor, und der Inhaber von S&S legt das erste Scharfschalten um. Bis dahin bleibt `NOINDEX = True`, auch wenn schon echte IDs in `konfig.js` stehen.

1. `konfig.js`: `googleTag` (AW-ID) und drei Labels aus Google Ads > Tools > Conversions eintragen: `phone_click`, `whatsapp_click`, `form_submit`; `telefonAnzeige` muss der sichtbaren Nummer entsprechen.
   - **`website_call` bleibt leer (`""`).** Die Seite geht mit leerem Schalter live. In Woche 1 und 2 des Kampagnenstarts wird er nicht gesetzt, und die Aktion „Anrufe über eine Telefonnummer auf Ihrer Website“ wird im Konto nicht angelegt. Gesetzt wird er später nur über das Verfahren „Schalter setzen“ weiter unten.
   - Leer heißt: kein Nummerntausch, auf der Seite steht für jeden Besucher 02161 688 86 91. Anrufe über die Seite zählen als `phone_click`; Anrufe aus der Anzeige zählt Google ohne diese Seite.
   - Im Konto sind `phone_click` und `whatsapp_click` sekundär, primär sind der Anruf aus der Anzeige ab 60 s und `form_submit`.
   - Dieselben Werte am selben Tag in die Leadmaschine (`kunden/kfz-gutachter-es/go-live.json` und `ads/wache.json`; Feldnamen im Kommentar von `konfig.js`). Zum leeren `website_call` gehört dort ebenfalls ein leerer Wert.
2. Lead-Endpunkt: Origin `https://unfall-mg.de` in der CORS-Liste eintragen (gemessen 09.11.2026 00:47: OPTIONS mit diesem Origin antwortet 204 ohne `Access-Control-Allow-Origin`). Der Testlead landet im Postfach des Kunden, deshalb vorher ein Wort an ihn über den Inhaber von S&S (Nachzug v8 der Leadmaschine, Abschnitt 10). Testlead mit Marker TEST, danach die Testdatei auf dem Server löschen (60-LEKTIONEN E4).
3. Erst wenn die Freigabe des Kunden mit Beleg vorliegt und der Inhaber von S&S das Scharfschalten umlegt: `bauen.py`: `NOINDEX = False`, neu bauen. GitHub Pages für dieses Repo ist dann schon abgeschaltet (Settings, Pages, Source „None“; am besten lange vorher, spätestens vor diesem Schritt, nichts braucht die Kopie mehr, alle Ziel-URLs der Kampagne zeigen auf `unfall-mg.de`): Die alte Staging-Kopie baut aus `main`, verweist mit ihrem Canonical auf sich selbst und wäre ohne `noindex` eine zweite, auffindbare Fassung der Seite.
4. Bilder: Dateien nach `bilder/` legen (Namen und Maße im Abschnitt „Seiten, Menü und Bildplätze“), in `bauen.py` den Platz in der Tabelle `BILDER` ausfüllen (Datei, alt-Text, Maße, Unterschrift, Bildnachweis) und neu bauen. Ein ausgefüllter, aber unvollständiger Platz bricht den Bau ab.
5. DNS: A-Record `@` und `www` auf sunds-hub (169.58.211.51, gemessen 10.11.2026 über leads.sundsconnect.de), kein AAAA auf fremde Ziele; danach auf sunds-hub `domain_scharf.sh` (Trockenlauf), dann `--echt` (Caddy-Block, Zertifikat). GitHub Pages bekommt keine Custom Domain. Die früheren GitHub-Pages-A-Records gelten nicht mehr; HTTPS und Zertifikat stellt Caddy.
6. Prüfung vor dem ersten Klick: Tag Assistant zeigt `consent default denied`, nach „Erlauben“ `update granted`; Ablehnen-Pfad lädt nichts von googletagmanager.com; nach „Erlauben“ steht genau ein `config` im dataLayer, und alle Telefon-Links zeigen und wählen 02161 688 86 91; über den Fußlink „Einwilligung zur Messung ändern“ ablehnen lädt die Seite neu, danach lädt nichts mehr von Google; Testlead kommt beim Kunden an. Ein Testanruf über eine getauschte Nummer gehört nicht hierher: Er braucht einen echten Anzeigenklick und einen gesetzten Schalter und steht im Verfahren „Schalter setzen“.
7. Messung mit echtem Tag, sobald echte IDs in `konfig.js` stehen und bevor der erste Klick kommt. Sie ist bis dahin offen: Die Zeugen sehen nur, was die Seite in den dataLayer legt, und die Browserläufe liefen mit einem leeren Stub statt gtag.js. Ablauf: Netzwerk-Protokoll des Browsers öffnen, „Erlauben“ wählen, dann über den Fußlink „Ablehnen“. Danach geht keine Anfrage mehr an Google (googletagmanager.com, googleadservices.com, google.com, doubleclick.net), und es bleibt weder ein Cookie `_gcl_*`, `_gac_*` oder `gwcc` noch der localStorage-Schlüssel `_gcl_ls`. Bleibt etwas stehen, die Löschung in `einwilligung.js` (`loescheGoogleCookies`) nachziehen, bevor Klicks kommen.

## Verfahren „Schalter setzen“ (`website_call`)

`labels.website_call` in `konfig.js` schaltet den Nummerntausch ein: Wer über eine Anzeige kommt und „Erlauben“ wählt, sieht und wählt dann statt 02161 688 86 91 eine Weiterleitungsnummer von Google, und Anrufe ab 60 s zählen unter der Aktion „Anrufe über eine Telefonnummer auf Ihrer Website“. Alle anderen Besucher und das Impressum behalten die echte Nummer. Vor dem Setzen stehen die Bedingungen 1, 2, 4 und 6, und die Dateien aus Bedingung 5 sind vorbereitet. Bedingung 3 und die Conversion-Probe aus Bedingung 5 lassen sich vorher nicht erfüllen, weil sie den gesetzten Schalter auf der ausgelieferten Seite brauchen: Sie sind die Abnahme direkt nach dem Setzen.

1. Der Kunde hat zugestimmt, dass Besucher aus Anzeigen auf der Seite eine Nummer von Google sehen; der Beleg ist abgelegt.
2. Die Form der Google-Nummer und das Bild bei 390 px sind gesehen: Kopf, Hero-Knopf und Fuß mit der Ersatznummer (sie kann länger sein als die echte), Anrufleiste und Einwilligungsbalken dazu; zuerst auf der Zwischenadresse. Die Anrufleiste zeigt „Anrufen“ und keine Nummer, dort zählt das Ziel des Links. Foto abgelegt.
3. Abnahme nach dem Setzen, in zwei Teilen. **3a, sofort:** die Seite über einen echten Anzeigenklick öffnen (nicht die Adresse eintippen), „Erlauben“ wählen, prüfen, dass Kopf, Hero-Knopf und Fuß eine andere Nummer zeigen und die Anrufleiste sie wählt, darüber anrufen und länger als 60 Sekunden sprechen; der Anruf kommt beim Kunden an. Danach über den Fußlink ablehnen: die Seite lädt neu und zeigt wieder die echte Nummer. Fällt 3a durch, geht es sofort zurück (Absatz „Zurück“). **3b, binnen eines Tages:** Der Anruf steht im Anrufbericht unter der Aktion. Steht er am Folgetag nicht dort, geht es ebenfalls zurück.
4. Die 60-Sekunden-Schwelle trägt: Bedingung 4 nach Nachzug v8 der Leadmaschine, Abschnitt 5 (Zähltabelle mit Mindestmenge und Abgleich mit der Anrufliste des Kunden). Eine Quote ohne Mindestmenge zählt nicht.
5. Wache und Go-Live-Datei der Leadmaschine tragen das Label und gehen im selben Zug mit der Seite raus (vorbereitet heißt: auf einem Zweig der Leadmaschine, nicht auf `main`; das Label entsteht erst beim Anlegen der Aktion, dem ersten Schritt von „Setzen“, und gemergt wird im selben Zug wie das Ausrollen der Seite); sonst meldet die Messkette rot, sobald es auf der Seite steht. Die Conversion-Probe gehört zur Abnahme nach dem Setzen: Sie läuft gegen die ausgelieferte `konfig.js` und ist an deren Prüfsumme gebunden.
6. In derselben Woche gibt es keinen zweiten Eingriff an Kampagne oder Seite, sonst lässt sich keine Wirkung zuordnen.

Setzen, erst wenn 1, 2, 4 und 6 belegt und die Dateien aus 5 vorbereitet sind: Aktion im Konto anlegen (Mindestdauer 60 s, Zählung „Eine“, primär), ihr Label nach `labels.website_call` eintragen, Zeugen und `python bauen.py --pruefen` fahren, ausrollen, dann Bedingung 3a, die Conversion-Probe und binnen eines Tages 3b. Vor dem Ausrollen den Commit des laufenden Stands notieren (`ausrollen.sh stand`, letzter Teil der Zeile); er trägt den leeren Schalter und ist der Rückweg. Erlaubt sind im Label Buchstaben, Ziffern, `-` und `_`; ein Platzhalter mit X oder andere Zeichen brechen den Bau ab, sobald `NOINDEX` aus ist, und im Browser steht dann die Konsolenzeile „website_call verworfen“.

Zurück, als ein Zug in derselben Stunde. Erstens, in Sekunden: auf sunds-hub `bash ausrollen.sh zurueck <Commit des vorigen Stands>` (der Stand mit leerem Schalter; `zurueck` nimmt den Commit-Namen, also den letzten Teil der Zeile aus `ausrollen.sh stand`, nicht den ganzen Pfad; das Skript liegt im Ordner des letzten Ausrollens unter `/home/ubuntu/kge-ausrollen-<Datum>/`). Zweitens das Label in `konfig.js` auf `main` wieder auf `""` setzen. Drittens `ads/wache.json` und `go-live.json` der Leadmaschine zurücknehmen. Bis alle drei stehen, rollt niemand aus `main` aus, auch nicht für etwas anderes: Ein Ausrollen aus `main` mit gesetztem Label schaltete den Tausch wieder ein, und weil dann alle Stellen gleich sind, meldeten Tor und Wache grün. Anlass ist ein Ereignis, keine Statistik: ein verwirrter Anrufer, eine Beschwerde des Kunden oder ein gebrochenes Bild.

## Bewertung und Name (`BEWERTUNG_ZEIGEN`, `NAME_ZEIGEN` in `bauen.py`)

Beide stehen im Hero der Startseite. Im HTML steht `{{vertrauen}}` zwischen h1 und Anrufknopf, der Bewertungskasten vor der Namenszeile, also über dem Knopf; `stil.css` ordnet den Kasten per `order` hinter den Knopf. Mit eingeschaltetem Kasten ist das nicht angesehen. Die Sternchenerklärung gibt es seit dem Umbau vom 23.11.2026 nicht mehr; die Lage des Kastens vor dem Einschalten neu mit dem Wettbewerbsrecht abstimmen (Vorgabe vom 20.11.2026 bezog sich auf das Sternchen). Jeder Schalter wirkt allein; sind beide aus, fällt die Zeile `{{vertrauen}}` ganz weg.

`NAME_ZEIGEN = True` seit 20.11.2026: „Ihr Sachverständiger: Cihan Es“. Der Satz „Sie sprechen direkt mit Cihan Es“ kommt erst nach Bestätigung des Kunden.

`BEWERTUNG_ZEIGEN = False`. Eingeschaltet wird nur in dieser Reihenfolge, jeder Schritt mit Beleg:

1. Die Freigabe des Kunden liegt schriftlich vor (die Bewertungen stammen von echten Kunden, keine gekauften oder getauschten; der Hinweis unter der Zeile bleibt; Rechtsbericht kge-cta-r1). Ihre Vorgangsnummer (acht Zeichen) kommt nach `BEWERTUNG_KUNDENBELEG`; leer, kürzer, länger oder ein Platzhalter wie `XXXXXXXX` bricht den Bau ab. Der Bau prüft nur die Form der Nummer, nicht die Freigabe selbst. Deshalb vor dem Einschalten den Beleg der Go-live-Freigabe lesen. Er entsteht mit `python zentrale/freigabe/freigabe-beleg.py <nummer>` in einem Klon der Leadmaschine mit ssh-Zugang zum Server. Achtung, das Skript liest nicht nur: Es legt den Beleg unter `kunden/kfz-gutachter-es/gespraeche/` ab und überschreibt bei „freigegeben“ den Block `freigabe` in `go-live.json` mit dem Umfang dieses Vorgangs. Es wird deshalb nur einmal und nur für den Vorgang der Go-live-Freigabe gefahren; liegt der Beleg schon vor, wird die abgelegte Datei gelesen, nicht das Skript erneut gestartet. Eingeschaltet wird nur, wenn der Umfang den Punkt `landingpage` enthält, die Entscheidung „freigegeben“ lautet und die Zeile „Anmerkung:“ (das Feld für Änderungswünsche; sie erscheint nur, wenn der Kunde etwas eingetragen hat) nichts zu Bewertungen sagt. Der Beleg selbst (`kunden/kfz-gutachter-es/gespraeche/freigabe-…json`) bleibt in der Leadmaschine und kommt nie in dieses Repo: Es ist öffentlich, und der Beleg trägt Namen, IP-Adresse und Browserkennung des Kunden.
2. Die Sonntagsangabe im Google-Profil („24 Stunden geöffnet“) hat der Kunde berichtigt. Der Link im Kasten macht die Profilangaben zu unserem Auftritt; vorher nicht einschalten.
3. Die Antwort liegt bereit, falls der Kunde den Satz „Aus unserem Google-Profil. Wir prüfen nicht, ob die Verfasser unsere Leistung genutzt haben.“ gestrichen haben will (er kann ihn als Zweifel an seinen Bewertungen lesen): „Der Satz ist seit 2022 Pflicht, wenn eine Seite Bewertungen zeigt (§ 5b Abs. 3 UWG). Ohne ihn ist die Zeile abmahnbar, und gerade die Wettbewerbszentrale geht dem nach. Ohne den Satz zeigen wir keine Bewertung auf der Seite.“ Der Hinweis ist Bedingung für die Zeile; es gibt keine Fassung ohne ihn.
4. Die fünf Werte am selben Tag am Profil ablesen: `BEWERTUNG_NOTE`, `BEWERTUNG_ANZAHL`, `BEWERTUNG_SEIT` (Jahr der ältesten Bewertung), `BEWERTUNG_STAND` (Tag des Ablesens, TT.MM.JJJJ) und `BEWERTUNG_LINK` (die echte Profiladresse, `https://g.page/…`, `https://maps.app.goo.gl/…` oder `https://www.google.com/maps/place/…`). Am selben Tag ein Bildschirmfoto des Profils als PNG nach `belege/bewertung-<JJJJ-MM-TT>.png` legen, das Datum gleich dem Stand (Stand 20.11.2026 heißt `belege/bewertung-2026-11-20.png`). Der Ausschnitt zeigt Name des Betriebs, Note, Anzahl und das Datum, aber keine einzelnen Rezensionen und keine Namen von Verfassern: Das Repo ist öffentlich. `belege/` ist vom Ausliefern ausgenommen (`.gitattributes`). Fehlt das Foto, passt sein Datum nicht oder ist es kein PNG, bricht der Bau ab. Ein altes Foto unter neuem Namen erkennt der Bau nicht; das Datum im Bild prüft der Mensch.
5. `BEWERTUNG_ZEIGEN = True`, `python bauen.py`. Der Bau bricht ab, wenn ein Wert leer ist, ein Beleg aus Schritt 1 oder 4 fehlt, `SEIT` keine Jahreszahl von 2005 bis heute ist, der Stand in der Zukunft liegt oder der Link keine Profiladresse ist (die heutige Kartensuche bricht also ab, mit und ohne `noindex`).
6. Wörtersperre (Schritt 2 oben): Mit eingeschaltetem Kasten meldet sie auf `index.html` einen Fund „4,9 … (Bewertungszahl ohne Beleg)“. Die Sperre kennt keine Belegliste, nur `--ausnahme` mit einem wörtlichen Satz. Deshalb geht genau die gebaute Zeile als zweite Ausnahme hinein, aus `bauen.py` gelesen, nie abgetippt: `--ausnahme "Ismet Es Kfz Meisterbetrieb e.K." --ausnahme "$(python bauen.py --bewertungszeile)"`. Damit geht nur dieser eine Satz mit Anzahl, Jahr und Stand durch; jede andere „4,9“ bleibt ein Fund. Die zweite Ausnahme nur setzen, wenn das Profilfoto aus Schritt 4 mit demselben Stand abgelegt ist (der Bau aus Schritt 5 hat das schon geprüft). Die Sperre selbst wird hier nicht geändert, sie gehört der Leadmaschine (`kunden/kfz-gutachter-es/kampagnen-vorbereitung/pruefen/`).
7. Bilder bei 390 und 1280 ansehen. Mit eingeschaltetem Kasten weicht der Einwilligungsbalken am Handy aus (`FREI_HALTEN` in `einwilligung.js`): Bei 390 × 844 erscheint er erst nach rund 150 px Scrollen statt nach 4 s (gemessen 20.11.2026 am alten Hero mit Sternchen; am Aufbau vom 23.11.2026 nicht neu gemessen). Wer nicht scrollt, sieht ihn nicht, und dessen Klicks auf der Seite (`phone_click`, `whatsapp_click`, `form_submit`) werden nicht gemessen; den Anruf aus der Anzeige zählt Google ohne die Seite. Gewollt, weil der Hinweis nach § 5b Abs. 3 UWG nicht verdeckt werden darf.

Veralteter Stand: Ist `BEWERTUNG_STAND` älter als 14 Tage, bricht der Bau nicht ab, sondern baut die Seiten OHNE Kasten (die Namenszeile bleibt) und druckt „BEWERTUNG VERALTET, Kasten weggelassen: Stand <Datum>“; `--pruefen` druckt dieselbe Zeile, der Exit hängt weiter nur an Abweichungen der Seiten. So trifft ein alter Stand nicht den nächsten fremden Bau, und niemand ist versucht, den Stand ohne Ablesen auf heute zu setzen. Wer die Zeile sieht: entweder neu ablesen (Schritt 4, mit neuem Foto) oder den Bau so ausrollen, ohne Kasten. Leere oder falsche Werte, fehlende Belege und ein Stand in der Zukunft brechen weiter ab.

Die 14-Tage-Regel greift nur beim Bauen. `ausrollen.sh` baut nicht, und die ausgelieferte Seite zeigt Note, Anzahl und Stand weiter, auch nach Wochen. Ein eingeschalteter Kasten braucht deshalb einen wöchentlichen Nachleser: Profil ablesen, bei einer Abweichung oder einem Stand über 14 Tage neu bauen und ausrollen oder abschalten. **Offen, Wächter noch nicht gebaut** (gehört als Ziel in die Überwachung der Leadmaschine, `zentrale/waechter/ueberwachung.tsv`). **Ohne laufenden Nachleser nicht einschalten.** Ein Termin im Kalender ersetzt ihn nicht.

**Offen, entscheidet die Rechtsprüfung vor dem Einschalten:** Die Frist trifft die beiden Werte ungleich. Bei rund 48 Bewertungen ist die Anzahl nach 14 Tagen mit 31 bis 60 % Wahrscheinlichkeit überholt, die Note 4,9 nur mit 2 bis 5 % (Rechnung im Bericht des Wissenschaftlers, Prüfziel kge-cta-r3). Ob die Zeile stattdessen „über 45 Bewertungen“ mit 30 Tagen Gültigkeit sagen darf, entscheidet die Rechtsprüfung. Bis dahin gilt die Regel wie gebaut: genaue Anzahl, 14 Tage.

**Messung über den Umbau hinweg:** `phone_click` zählt Tipps auf Anruf-Links, keine Anrufe. Seit diesem Umbau tragen Start- und Umlandseite je 10 statt 6 Anruf-Links (die übrigen Seiten unverändert 3 bis 5; gezählt am Bau vom 20.11.2026), die Zahl steigt also auch ohne einen einzigen Anruf mehr. Über den Umbau vergleichbar sind nur die Anrufliste (eingegangene Anrufe) und abgeschickte Formulare. Seit dem Umbau vom 23.11.2026 trägt die Startseite 5 Anruf-Links statt 10, die übrigen Seiten 3 oder 4 (gezählt am Bau vom 23.11.2026); `phone_click` sinkt also auch ohne einen Anruf weniger.

## Messung ohne Konfiguration

Solange `konfig.js` Platzhalter trägt, lädt `einwilligung.js` kein Google-Skript und feuert keine Conversion, auch nach „Erlauben“ nicht; die Konsole meldet „Messung nicht konfiguriert“. Das Banner und die Speicherung der Entscheidung funktionieren trotzdem.

## Seiten, Menü und Bildplätze (Umbau 23.11.2026)

Die Seite ist seit dem 23.11.2026 eine Website mit Seitenmenü, keine Landingpage mit Sprungmarken.

- **Menü:** Die Liste `MENUE` in `bauen.py` füllt die Kopfzeile (ab 1024 px) und das Menü darunter (`<details class="menue">`, ohne JavaScript). Die Punkte führen auf Seiten: Start, Nach dem Unfall, Wer zahlt?, Einsatzgebiet, Kontakt und Anfahrt. „Abends und am Wochenende“, Impressum und Datenschutz stehen im Fuß.
- **Anrufstellen:** Kopf (am Handy als Symbol, ab 600 px mit Nummer), ein Knopf im Hero der Startseite, auf den Unterseiten die Zeile `{{ruf}}` im Seitenkopf (Nummer als Text und Link, `RUF_ZEILE` in `bauen.py`), die Anrufleiste am Handy und der Kontaktabschnitt (Startseite unten, `kontakt.html`). Große Anrufknöpfe am Ende der Abschnitte gibt es nicht mehr; dort steht ein Textlink zum nächsten Schritt. Auf jeder Seite steht 02161 688 86 91 als Text und als `tel:+4921616888691`.
- **Sprache:** kein „wir“ (Einzelunternehmen) und keine Ich-Form (nicht bestätigt), sondern dritte Person und direkte Anrede. Zeitzusagen (Termin am selben Tag, 24 Stunden, Dauer der Besichtigung) und „Sie strecken nichts vor“ stehen nicht auf der Seite, bis der Kunde sie bestätigt.
- **Bagatellgrenze:** steht je Seite einmal: Startseite im Hero, `kosten.html` unter „Kleiner Schaden“ (dazu die Tabellenzeile 750 der BVSK-Übersicht). Sternchen und Fußnoten gibt es nicht mehr.

Bildplätze: jeder Platz ist einzeln schaltbar über die Tabelle `BILDER` in `bauen.py`. Ein Platz erscheint genau dann, wenn dort Datei, alt-Text, Maße und Bildnachweis eingetragen sind und die Datei unter `bilder/` liegt. Sonst fehlt seine Zeile ganz (kein Kasten, kein „Foto folgt“). `FOTOS_ZEIGEN` ist der Hauptschalter (Vorgabe an; aus blendet alle Bilder und die Bildnachweise aus). Ist ein Platz eingetragen, aber unvollständig, bricht `python bauen.py` ab (Zeuge G12).

| Platz in `BILDER` | Stelle | Seitenverhältnis | Stand 23.11.2026 |
|---|---|---|---|
| `start` | Startseite oben, über den Adressen (`{{bild_start}}`), lädt bevorzugt | 4:3, 1600 px breit | leer, wartet auf das Foto des Kunden (Begutachtung am Fahrzeug) |
| `schadendetail` | Startseite, „So läuft es ab“, unter der Überschrift | 4:3 | `bilder/schadendetail-lack.jpg`, 800 x 600, 49 KB, Symbolbild |
| `streifschaden` | `kosten.html`, Zeile „Kleiner Schaden“ | 4:3 | `bilder/streifschaden-kotfluegel.jpg`, 560 x 420, Symbolbild; der Ausschnitt lässt das Markenzeichen auf der Felge weg |
| `ort` | `umland.html`, neben den Ortslisten | 3:2 | `bilder/moenchengladbach-muenster.jpg`, 960 x 640, 154 KB, Unterschrift nennt den Ort |
| `unfall` | `ablauf.html`, vor „An der Unfallstelle“ | 16:9, 1600 px breit | leer |
| `hebebuehne` | `umland.html`, Abschnitt Hebebühne | 16:9, 1600 px breit | leer, kein freies Bild |
| `unterlagen` | `kosten.html`, vor „In der Regel zahlen Sie nichts“ | 16:9, 1600 px breit | leer, kein freigegebenes Bild |

Die drei Bilder sind Ausschnitte aus den geprüften Vorschauen (560 bis 960 px breit), ohne EXIF, als JPEG, jedes unter 200 KB. Die Originale ließen sich am 23.11.2026 nicht automatisch laden (Unsplash antwortet einem Abrufwerkzeug mit einer Browserprüfung, Wikimedia mit „Too many requests“). Wer die Originale von Hand lädt: auf dasselbe Seitenverhältnis zuschneiden, höchstens 1600 px breit, unter etwa 200 KB, EXIF entfernen, Datei ersetzen und `breite` und `hoehe` in `BILDER` anpassen. Beim Bild `streifschaden` bleibt das Markenzeichen auf der Felge außerhalb des Ausschnitts.

Jedes `<img>` trägt `width`, `height`, `alt` und `loading="lazy"` (oben `fetchpriority="high"`). Die Unterschrift beginnt mit „Symbolbild“ bei Bildern, die nicht den Betrieb zeigen; bei einem echten Foto des Betriebs bleibt `unterschrift` leer. Bildnachweise der gezeigten Plätze erscheinen als Abschnitt im Impressum. Die Bilder liegen lokal in `bilder/`, nichts wird von fremden Servern geladen.

Offen (Stand 23.11.2026):

- `einwilligung.js`, `FREI_HALTEN` nennt noch `.hero .stern`. Den Sternchentext gibt es nicht mehr, der Wähler trifft auf keiner Seite etwas. Der Zeuge S2 prüft nur den Wortlaut der Konstante und bleibt grün. Die Datei blieb beim Umbau bis auf den Fragesatz des Balkens unverändert; beim nächsten Eingriff den Wähler entfernen und Zeuge und Rotprobe mitziehen.
- Die Lage des Bewertungskastens (siehe „Bewertung und Name“) ist am neuen Hero nicht angesehen und nicht mit der Rechtsprüfung abgestimmt.
- Der Leuchtstift (Marker) steht nur noch in der h1 der Startseite, die Ortszeile über den Überschriften der Unterseiten gibt es nicht mehr.
