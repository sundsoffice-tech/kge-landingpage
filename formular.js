/* Rückruf-Formular an den Lead-Endpunkt von S&S Connect (Server in Deutschland).
 *
 * Reihenfolge im Endpunkt: erst auf Platte, dann Mail (60-LEKTIONEN E1). Hier gilt:
 *  - Nur die Telefonnummer ist Pflicht (Recherche 03 B7: drei Felder, ein Pflichtfeld).
 *  - Honigtopf ist eine Checkbox und wird über .checked gelesen, nie über .value (Lektion E2).
 *  - Der Erfolgstext steht im Attribut data-erfolg am Formular, gesetzt von bauen.py aus den Telefonzeiten
 *    (TELEFONZEITEN, Runde 6, Punkt 12).
 *  - Drei Ausgänge (Runde 7, Punkt 1; Regeln seit Runde 8):
 *    a) Erfolg: 2xx mit lesbarem JSON und ok === true. Erfolgstext, Knopf bleibt gesperrt, danach Messung
 *       form_submit über window.kgeMessung (einwilligung.js); wirft die Messung, bleibt die Erfolgsmeldung stehen.
 *    b) Sicher gescheitert: NUR eine Antwort unter 500 mit lesbarem JSON, dessen ok nicht true ist (etwa 200 mit
 *       ok:false oder 400 mit JSON). Der Endpunkt hat dann selbst abgelehnt. Fehlertext mit tippbarer Nummer, Knopf
 *       wieder frei.
 *    c) Unklar: alles andere, das kein Erfolg ist: jeder Status ab 500 (mit oder ohne JSON; ein 502 oder 504 des
 *       vorgeschalteten Servers kann nach dem Speichern kommen), jede Antwort ohne lesbares JSON, Netzfehler beim
 *       Versand und die Zeitgrenze. Die Anfrage kann angekommen sein: Hinweis mit tippbarer Nummer, Knopf bleibt
 *       gesperrt mit seinem Text, Eingaben bleiben stehen, kein zweiter Versand. Den Ausgang meldet der Zeitgeber
 *       selbst. Er bricht den Versand nicht ab (kein AbortController): Eine später doch eintreffende Erfolgsantwort
 *       stellt die Anzeige noch auf Erfolg und zählt als form_submit; jede andere späte Antwort ändert nichts.
 *  - Ist telefonAnzeige in konfig.js keine Zeichenkette, gelten die Rückfallwerte für Anzeige und Link.
 *  - Laden (Runde 7, Punkt 2): Im Markup ist der Knopf gesperrt und darunter steht sichtbar „Bitte rufen Sie an: …“
 *    ([data-ohne-skript]). Erst als letzter Schritt, nach der Registrierung des Absende-Handlers, schaltet dieses
 *    Skript den Knopf frei und blendet den Satz aus. Lädt es nicht oder scheitert es vorher, bleiben Knopf gesperrt
 *    und Satz sichtbar. Zeuge: pruefen/zeuge-formular.js.
 */
(function () {
  "use strict";
  var konfig = window.KGE_KONFIG || {};
  var ENDPUNKT = konfig.leadEndpunkt || "https://leads.sundsconnect.de/lead";
  var KUNDE = konfig.kunde || "kge";
  var TELEFON = typeof konfig.telefonAnzeige === "string" && konfig.telefonAnzeige ? konfig.telefonAnzeige
    : "02161 688 86 91";
  var TELEFON_LINK = "tel:+" + (TELEFON.replace(/\D/g, "").replace(/^0/, "49"));
  var ZEITGRENZE_MS = 15000;

  var form = document.getElementById("rueckruf-formular");
  if (!form) return;
  var status = document.getElementById("f-status");
  var knopf = form.querySelector("button[type=submit]");
  var knopfText = knopf.textContent;
  var ohneSkript = form.querySelector("[data-ohne-skript]");
  var telFeld = form.querySelector("#f-tel");
  var ERFOLG = form.getAttribute("data-erfolg") || "Danke. Wir rufen Sie zurück.";
  // offen: Versand möglich; sendet: Anfrage unterwegs; unklar: Ausgang offen, kein zweiter Versand; erfolg: fertig.
  var zustand = "offen";

  function melde(text, art) {
    status.textContent = text;
    status.className = "status" + (art ? " " + art : "");
  }

  function meldeMitNummer(text) {
    melde(text, "fehler");
    var anruf = document.createElement("a");
    anruf.href = TELEFON_LINK;
    anruf.className = "ziel";
    anruf.setAttribute("data-messung", "phone_click");
    anruf.textContent = TELEFON;
    status.appendChild(anruf);
  }

  function telefonGueltig(wert) {
    var ziffern = wert.replace(/\D/g, "");
    return ziffern.length >= 6 && ziffern.length <= 16;
  }

  function erfolg() {
    if (zustand !== "sendet" && zustand !== "unklar") return;
    zustand = "erfolg";
    form.querySelectorAll("input:not([type=checkbox]), textarea").forEach(function (f) { f.value = ""; });
    knopf.disabled = true;
    knopf.textContent = "Anfrage eingegangen";
    melde(ERFOLG, "ok");
    try {
      if (typeof window.kgeMessung === "function") window.kgeMessung("form_submit");
    } catch (fehler) {
      console.error("[Rueckruf] Messung fehlgeschlagen, Anfrage ist angekommen:", fehler);
    }
  }

  function gescheitert(grund) {
    if (zustand !== "sendet") return;
    zustand = "offen";
    knopf.disabled = false;
    knopf.textContent = knopfText;
    meldeMitNummer("Das hat leider nicht geklappt. Bitte rufen Sie direkt an: ");
    console.error("[Rueckruf] Versand fehlgeschlagen:", grund);
  }

  function unklar(grund) {
    if (zustand !== "sendet") return;
    zustand = "unklar";
    knopf.disabled = true;
    knopf.textContent = knopfText;
    meldeMitNummer("Wir konnten den Eingang nicht bestätigen. Bitte rufen Sie an: ");
    console.error("[Rueckruf] Eingang nicht bestätigt:", grund);
  }

  telFeld.addEventListener("input", function () {
    if (telFeld.getAttribute("aria-invalid") === "true" && telefonGueltig(telFeld.value)) {
      telFeld.removeAttribute("aria-invalid");
      melde("");
    }
  });

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (zustand !== "offen") return;
    var tel = telFeld.value.trim();
    if (!telefonGueltig(tel)) {
      telFeld.setAttribute("aria-invalid", "true");
      melde("Bitte geben Sie eine Telefonnummer an, unter der Sie erreichbar sind.", "fehler");
      telFeld.focus();
      return;
    }
    zustand = "sendet";
    knopf.disabled = true;
    knopf.textContent = "Wird gesendet …";
    melde("Einen Moment …");

    var honig = form.querySelector("#f-website");
    // Die Zeitgrenze meldet nur „unklar“ und bricht nicht ab, damit eine späte Erfolgsantwort noch ankommt.
    var uhr = setTimeout(function () {
      unklar("Zeitgrenze " + ZEITGRENZE_MS + " ms");
    }, ZEITGRENZE_MS);
    var versand;
    try {
      versand = fetch(ENDPUNKT, {
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
      });
    } catch (fehler) {
      versand = Promise.reject(fehler);
    }
    versand.then(function (r) {
      return r.json().then(
        function (d) { return { r: r, lesbar: true, daten: d }; },
        function () { return { r: r, lesbar: false, daten: null }; });
    }).then(function (a) {
      clearTimeout(uhr);
      if (a.r.ok && a.lesbar && a.daten && a.daten.ok === true) erfolg();
      else if (a.lesbar && a.r.status < 500) gescheitert((a.daten && a.daten.fehler) || "HTTP " + a.r.status + ", ohne ok:true");
      else unklar("HTTP " + a.r.status + (a.lesbar ? "" : ", JSON nicht lesbar"));
    }, function (fehler) {
      clearTimeout(uhr);
      unklar(fehler);
    });
  });

  // Erst jetzt, mit registriertem Handler: Knopf frei, Anrufsatz für Besucher ohne Skript aus.
  knopf.disabled = false;
  if (ohneSkript) ohneSkript.hidden = true;
})();
