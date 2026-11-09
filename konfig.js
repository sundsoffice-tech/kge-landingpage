/* Konfiguration der Messung für die Landingpage Kfz Gutachter Es.
 *
 * Die Werte kommen am Tag der Kontoanlage aus dem Google-Ads-Konto (Tools > Conversions):
 *  - googleTag: die Conversion-ID des Kontos, Form "AW-XXXXXXXXXX".
 *  - labels: je Conversion-Aktion das Label hinter dem Schrägstrich ("AW-XXXXXXXXXX/<Label>").
 *    phone_click   Klick auf eine Telefonnummer (primär)
 *    whatsapp_click Klick auf WhatsApp (sekundär)
 *    form_submit   Rückruf-Formular erfolgreich abgeschickt, erst nach ok:true des Endpunkts (primär)
 *  - telefonAnzeige: die Nummer genau so, wie sie sichtbar auf der Seite steht. Google tauscht sie nach
 *    Einwilligung gegen eine Weiterleitungsnummer (Website-Anruf-Conversion); Schreibweise muss stimmen.
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
  telefonAnzeige: "02161 622 57 68",
  leadEndpunkt: "https://leads.sundsconnect.de/lead",
  kunde: "kge"
};
