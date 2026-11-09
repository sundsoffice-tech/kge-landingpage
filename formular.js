/* Rückruf-Formular an den Lead-Endpunkt von S&S Connect (Server in Deutschland).
 *
 * Reihenfolge im Endpunkt: erst auf Platte, dann Mail (60-LEKTIONEN E1). Hier gilt:
 *  - Nur die Telefonnummer ist Pflicht (Recherche 03 B7: drei Felder, ein Pflichtfeld).
 *  - Honigtopf ist eine Checkbox und wird über .checked gelesen, nie über .value (Lektion E2).
 *  - Erfolg wird erst gemeldet, wenn der Endpunkt mit ok:true antwortet; sonst Fehlertext mit tippbarer
 *    Telefonnummer (tel:-Link). Der Erfolgstext steht im Attribut data-erfolg am Formular, gesetzt von
 *    bauen.py aus der einen Rückrufzusage (RUECKRUF_WERKTAGS, RUECKRUF_SONST).
 *  - Conversion form_submit erst nach ok:true über window.kgeMessung (einwilligung.js).
 */
(function () {
  "use strict";
  var konfig = window.KGE_KONFIG || {};
  var ENDPUNKT = konfig.leadEndpunkt || "https://leads.sundsconnect.de/lead";
  var KUNDE = konfig.kunde || "kge";
  var TELEFON = konfig.telefonAnzeige || "02161 622 57 68";
  var TELEFON_LINK = "tel:+" + (TELEFON.replace(/\D/g, "").replace(/^0/, "49"));

  var form = document.getElementById("rueckruf-formular");
  if (!form) return;
  var status = document.getElementById("f-status");
  var knopf = form.querySelector("button[type=submit]");
  var knopfText = knopf.textContent;
  var telFeld = form.querySelector("#f-tel");
  var ERFOLG = form.getAttribute("data-erfolg") || "Danke. Wir rufen Sie zurück.";

  function melde(text, art) {
    status.textContent = text;
    status.className = "status" + (art ? " " + art : "");
  }

  function telefonGueltig(wert) {
    var ziffern = wert.replace(/\D/g, "");
    return ziffern.length >= 6 && ziffern.length <= 16;
  }

  telFeld.addEventListener("input", function () {
    if (telFeld.getAttribute("aria-invalid") === "true" && telefonGueltig(telFeld.value)) {
      telFeld.removeAttribute("aria-invalid");
      melde("");
    }
  });

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var tel = telFeld.value.trim();
    if (!telefonGueltig(tel)) {
      telFeld.setAttribute("aria-invalid", "true");
      melde("Bitte geben Sie eine Telefonnummer an, unter der wir Sie erreichen.", "fehler");
      telFeld.focus();
      return;
    }
    knopf.disabled = true;
    knopf.textContent = "Wird gesendet …";
    melde("Einen Moment …");

    var honig = form.querySelector("#f-website");
    fetch(ENDPUNKT, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify({
        kunde: KUNDE,
        telefon: tel,
        name: form.querySelector("#f-name").value.trim(),
        nachricht: form.querySelector("#f-text").value.trim(),
        seite: location.pathname,
        botcheck: honig && honig.checked ? "bot" : ""
      })
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (d) { return { ok: r.ok, daten: d }; });
    }).then(function (a) {
      if (!(a.ok && a.daten && a.daten.ok === true)) {
        throw new Error((a.daten && a.daten.fehler) || "Antwort ohne ok:true");
      }
      form.querySelectorAll("input:not([type=checkbox]), textarea").forEach(function (f) { f.value = ""; });
      knopf.textContent = "Anfrage eingegangen";
      melde(ERFOLG, "ok");
      if (typeof window.kgeMessung === "function") window.kgeMessung("form_submit");
    }).catch(function (err) {
      knopf.disabled = false;
      knopf.textContent = knopfText;
      melde("Das hat leider nicht geklappt. Bitte rufen Sie uns direkt an: ", "fehler");
      var anruf = document.createElement("a");
      anruf.href = TELEFON_LINK;
      anruf.className = "ziel";
      anruf.setAttribute("data-messung", "phone_click");
      anruf.textContent = TELEFON;
      status.appendChild(anruf);
      console.error("[Rueckruf] Versand fehlgeschlagen:", err);
    });
  });
})();
