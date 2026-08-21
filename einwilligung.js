/* Einwilligung für Conversion-Messung (§ 25 TDDDG) · Kfz Gutachter Es · S&S Connect
 *
 * Regel aus der Datenschutzerklärung (Abschnitt 2.5): Ohne Einwilligung wird KEINE
 * Conversion-Messung geladen. Dieses Skript hält das Versprechen technisch ein:
 *  - Vor einer Entscheidung lädt nichts. Kein gtag, kein Cookie, keine Anfrage an Google Ads.
 *  - "Ablehnen" und "Einwilligen" sind gleichwertig gestaltet (ein Klick, gleiche Größe).
 *  - Die Entscheidung liegt in localStorage ('kge-einwilligung-v1') und ist über den
 *    Footer-Link "Cookie-Einstellungen" jederzeit änderbar (Art. 7 Abs. 3 DSGVO).
 *  - Erst wenn TAG_ID gesetzt ist UND Einwilligung vorliegt, wird gtag.js geladen —
 *    mit Google Consent Mode (ad_storage 'granted' erst nach Einwilligung).
 *
 * Vor Go-Live eintragen (Schritt 8 der Go-Live-Liste): TAG_ID = 'AW-XXXXXXXXXX'.
 * Solange TAG_ID leer ist, funktioniert das Banner, aber es wird nichts geladen —
 * die Seite bleibt damit auch auf Staging ehrlich.
 */
(function () {
  "use strict";
  var TAG_ID = "";                      /* AW-Konversions-ID, kommt aus dem Ads-Konto (go-live.json) */
  var SCHLUESSEL = "kge-einwilligung-v1";

  function lies() {
    try {
      var roh = localStorage.getItem(SCHLUESSEL);
      return roh ? JSON.parse(roh) : null;
    } catch (e) { return null; }
  }
  function schreibe(werbung) {
    try {
      localStorage.setItem(SCHLUESSEL, JSON.stringify({
        werbung: !!werbung, zeit: new Date().toISOString()
      }));
    } catch (e) { /* Privat-Modus: Entscheidung gilt nur für diesen Aufruf */ }
  }

  function ladeTag() {
    if (!TAG_ID || window.__kgeTagGeladen) return;
    window.__kgeTagGeladen = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
    window.gtag("consent", "default", {
      ad_storage: "granted", ad_user_data: "granted",
      ad_personalization: "denied", analytics_storage: "denied"
    });
    window.gtag("js", new Date());
    window.gtag("config", TAG_ID);
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(TAG_ID);
    document.head.appendChild(s);
  }

  var stil = document.createElement("style");
  stil.textContent =
    "#kge-einwilligung{position:fixed;left:0;right:0;bottom:0;z-index:2147483000;" +
    "background:#0D1B27;color:#F3F6F8;font-family:'Archivo',system-ui,sans-serif;" +
    "box-shadow:0 -6px 24px rgba(13,27,39,.35);padding:14px 16px calc(14px + env(safe-area-inset-bottom))}" +
    "#kge-einwilligung .kge-e-innen{max-width:960px;margin:0 auto;display:flex;flex-wrap:wrap;" +
    "gap:12px 18px;align-items:center;justify-content:space-between}" +
    "#kge-einwilligung p{margin:0;font-size:14px;line-height:1.5;flex:1 1 380px}" +
    "#kge-einwilligung a{color:#FFB42E;text-decoration:underline}" +
    "#kge-einwilligung .kge-e-knoepfe{display:flex;gap:10px;flex:0 0 auto}" +
    "#kge-einwilligung button{font:inherit;font-size:14px;font-weight:700;cursor:pointer;" +
    "border-radius:8px;padding:11px 18px;min-width:120px;border:1.5px solid transparent}" +
    "#kge-einwilligung button:focus-visible{outline:3px solid #FFB42E;outline-offset:2px}" +
    "#kge-e-nein{background:transparent;color:#F3F6F8;border-color:#4A5A68}" +
    "#kge-e-nein:hover{border-color:#F3F6F8}" +
    "#kge-e-ja{background:#F5A00A;color:#0D1B27}" +
    "#kge-e-ja:hover{background:#FFB42E}" +
    "@media (max-width:560px){#kge-einwilligung .kge-e-knoepfe{flex:1 1 100%}" +
    "#kge-einwilligung button{flex:1 1 0;min-width:0}}";

  function zeige() {
    if (document.getElementById("kge-einwilligung")) return;
    document.head.appendChild(stil);
    var kasten = document.createElement("div");
    kasten.id = "kge-einwilligung";
    kasten.setAttribute("role", "dialog");
    kasten.setAttribute("aria-label", "Einwilligung zur Conversion-Messung");
    kasten.innerHTML =
      '<div class="kge-e-innen">' +
      "<p><b>Werbe-Messung erlauben?</b> Wir möchten messen, ob Besucher nach einem " +
      "Anzeigenklick anrufen oder eine Anfrage senden (Google Ads Conversion-Messung). " +
      "Ohne Ihre Einwilligung wird nichts geladen. Details und Widerruf: " +
      '<a href="datenschutz.html">Datenschutzerklärung</a>.</p>' +
      '<div class="kge-e-knoepfe">' +
      '<button type="button" id="kge-e-nein">Ablehnen</button>' +
      '<button type="button" id="kge-e-ja">Einwilligen</button>' +
      "</div></div>";
    document.body.appendChild(kasten);
    document.getElementById("kge-e-nein").addEventListener("click", function () {
      schreibe(false); kasten.remove();
    });
    document.getElementById("kge-e-ja").addEventListener("click", function () {
      schreibe(true); kasten.remove(); ladeTag();
    });
  }

  /* Footer-Link "Cookie-Einstellungen" öffnet das Banner erneut (Widerruf). */
  document.addEventListener("click", function (e) {
    var el = e.target.closest && e.target.closest("[data-einwilligung-oeffnen]");
    if (!el) return;
    e.preventDefault();
    try { localStorage.removeItem(SCHLUESSEL); } catch (fehler) { /* egal */ }
    zeige();
  });

  function start() {
    var wahl = lies();
    if (wahl === null) { zeige(); return; }
    if (wahl.werbung) { ladeTag(); }
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
