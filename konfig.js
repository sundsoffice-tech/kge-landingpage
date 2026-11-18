/* Konfiguration der Messung für die Landingpage Kfz Gutachter Es.
 *
 * Die Werte kommen am Tag der Kontoanlage aus dem Google-Ads-Konto (Tools > Conversions):
 *  - googleTag: die Conversion-ID des Kontos, Form "AW-XXXXXXXXXX".
 *  - labels: je Conversion-Aktion das Label hinter dem Schrägstrich ("AW-XXXXXXXXXX/<Label>").
 *    phone_click   Klick auf eine Telefonnummer (sekundär: ein Tipp auf die Nummer ist kein Gespräch, und
 *                  neben dem Anruf ab 60 s zählte derselbe Mensch sonst doppelt)
 *    whatsapp_click Klick auf WhatsApp (sekundär)
 *    form_submit   Rückruf-Formular erfolgreich abgeschickt, erst nach ok:true des Endpunkts (primär)
 *    website_call  Aktion „Anrufe über eine Telefonnummer auf Ihrer Website“, Anruf ab 60 s (primär, wie der
 *                  Anruf aus der Anzeige, der ohne diese Seite zählt). Mit diesem Label tauscht die Seite nach
 *                  Einwilligung und Anzeigenklick die Nummer in den Telefon-Links mit data-messung="phone_click"
 *                  gegen Googles Weiterleitungsnummer; der Link im Impressum bleibt die echte Nummer. Leer
 *                  lassen heißt: kein Tausch, die echte Nummer bleibt stehen, gezählt wird nur phone_click.
 *                  Erlaubt sind Buchstaben, Ziffern, Bindestrich und Unterstrich; alles andere verwirft
 *                  einwilligung.js mit einer Konsolenzeile, und bauen.py bricht ab, sobald NOINDEX aus ist.
 *    Rang nach Marketing-Bericht vom 18.11.2026, Frage 4 (kampagnen-steuerung/berichte/
 *    marketing-kge-v6-vor-start-2026-11-18.md); eingestellt wird der Rang im Google-Ads-Konto, nicht hier.
 *  - einwilligungsModus: "einfach" (Basic: vor dem Erlauben lädt nichts von Google). Das ist der einzige
 *    zulässige Wert. "erweitert" (cookielose Pings ohne Einwilligung) hat die Rechtsrolle am 10.11.2026
 *    verneint (§ 25 Abs. 1 TDDDG, docs/rollen-recht-consent-mode-2026-11-10.md im Repo leadmaschine);
 *    ein Wechsel braucht eine neue Rechtsprüfung und eine geänderte Datenschutzerklärung (Abschnitt 8).
 *  - telefonAnzeige: die Nummer genau so, wie sie sichtbar auf der Seite steht; Schreibweise muss stimmen,
 *    sonst findet der Tausch (website_call) sie nicht.
 *
 * AW-ID und Labels stehen fuer die Seite NUR hier (eine Stelle). Dieselben Werte gehoeren am selben Tag in
 * leadmaschine kunden/kfz-gutachter-es/ads/wache.json (ads.conversion_id, conversions.*.label) und go-live.json
 * (tracking.conversion_id, tracking.conversion_label), sonst meldet die Messkette-Wache rot. Für website_call
 * fehlt dort am 18.11.2026 noch der Platz (Programmierer r1, Fund 2): erst nachziehen, dann das Label eintragen.
 *
 * Solange ein Wert noch "XXXX" enthält, lädt einwilligung.js kein Google-Tag und feuert keine Conversion;
 * die Konsole sagt dann "Messung nicht konfiguriert". So bleibt Staging ehrlich und nichts läuft ins Leere.
 */
window.KGE_KONFIG = {
  googleTag: "AW-XXXXXXXXXX",
  labels: {
    phone_click: "XXXXXXXXXXXXXXXXXXX",
    whatsapp_click: "XXXXXXXXXXXXXXXXXXX",
    form_submit: "XXXXXXXXXXXXXXXXXXX",
    website_call: ""
  },
  einwilligungsModus: "einfach",
  telefonAnzeige: "02161 622 57 68",
  leadEndpunkt: "https://leads.sundsconnect.de/lead",
  kunde: "kge"
};
