/* Konfiguration der Messung für die Landingpage Kfz Gutachter Es.
 *
 * Die Werte kommen am Tag der Kontoanlage aus dem Google-Ads-Konto (Tools > Conversions):
 *  - googleTag: die Conversion-ID des Kontos, Form "AW-XXXXXXXXXX".
 *  - labels: je Conversion-Aktion das Label hinter dem Schrägstrich ("AW-XXXXXXXXXX/<Label>").
 *    phone_click   Klick auf eine Telefonnummer (primär)
 *    whatsapp_click Klick auf WhatsApp (sekundär)
 *    form_submit   Rückruf-Formular erfolgreich abgeschickt, erst nach ok:true des Endpunkts (primär)
 *  - einwilligungsModus: "erweitert" (Consent Mode v2 advanced: gtag.js lädt mit default denied, ohne
 *    Einwilligung gehen cookielose Pings an Google, Conversions werden modelliert) oder "einfach" (basic:
 *    vor dem Erlauben lädt nichts). Bei "einfach" muss Abschnitt 8 der Datenschutzerklärung zurück auf den
 *    Wortlaut vor dem 10.11.2026 (git log inhalte/datenschutz.html).
 *  - telefonAnzeige: die Nummer genau so, wie sie sichtbar auf der Seite steht. Google tauscht sie nach
 *    Einwilligung gegen eine Weiterleitungsnummer (Website-Anruf-Conversion); Schreibweise muss stimmen.
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
    form_submit: "XXXXXXXXXXXXXXXXXXX"
  },
  einwilligungsModus: "erweitert",
  telefonAnzeige: "02161 622 57 68",
  leadEndpunkt: "https://leads.sundsconnect.de/lead",
  kunde: "kge"
};
