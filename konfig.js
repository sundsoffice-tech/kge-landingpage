/* Konfiguration der Messung für die Landingpage Kfz Gutachter Es.
 *
 * Die Werte kommen am Tag der Kontoanlage aus dem Google-Ads-Konto (Tools > Conversions):
 *  - googleTag: die Conversion-ID des Kontos, Form "AW-XXXXXXXXXX".
 *  - labels: je Conversion-Aktion das Label hinter dem Schrägstrich ("AW-XXXXXXXXXX/<Label>").
 *    phone_click   Klick auf eine Telefonnummer (primär)
 *    whatsapp_click Klick auf WhatsApp (sekundär)
 *    form_submit   Rückruf-Formular erfolgreich abgeschickt, erst nach ok:true des Endpunkts (primär)
 *    website_call  Aktion „Anrufe über eine Telefonnummer auf Ihrer Website“ (Anruf ab Mindestdauer).
 *                  Mit diesem Label tauscht Google nach Einwilligung und Anzeigenklick die Nummer in allen
 *                  Telefon-Links gegen eine Weiterleitungsnummer. Leer lassen heißt: kein Tausch, die echte
 *                  Nummer bleibt stehen, gezählt wird nur phone_click.
 *  - einwilligungsModus: "einfach" (Basic: vor dem Erlauben lädt nichts von Google). Das ist der einzige
 *    zulässige Wert. "erweitert" (cookielose Pings ohne Einwilligung) hat die Rechtsrolle am 10.11.2026
 *    verneint (§ 25 Abs. 1 TDDDG, docs/rollen-recht-consent-mode-2026-11-10.md im Repo leadmaschine);
 *    ein Wechsel braucht eine neue Rechtsprüfung und eine geänderte Datenschutzerklärung (Abschnitt 8).
 *  - telefonAnzeige: die Nummer genau so, wie sie sichtbar auf der Seite steht; Schreibweise muss stimmen,
 *    sonst findet der Tausch (website_call) sie nicht.
 *
 * AW-ID und Labels stehen fuer die Seite NUR hier (eine Stelle). Dieselben Werte gehoeren am selben Tag in
 * leadmaschine kunden/kfz-gutachter-es/ads/wache.json (ads.conversion_id, conversions.*.label) und go-live.json
 * (tracking.conversion_id, tracking.conversion_label), sonst meldet die Messkette-Wache rot.
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
