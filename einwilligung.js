/* Einwilligung und Messung (§ 25 TDDDG, Google Consent Mode v2) · Kfz Gutachter Es · S&S Connect
 *
 * Regeln, die dieses Skript technisch einhält:
 *  - Vor einer Entscheidung lädt nichts: kein gtag.js, kein Cookie, keine Anfrage an Google (Basic-Modus,
 *    keine cookielosen Pings; Recherche 02 Abschnitt 5, § 25 TDDDG).
 *  - gtag('consent','default', alles denied, wait_for_update 500) steht vor dem Google-Tag und vor jedem
 *    config oder event; 'update' beim Klick als arguments-Aufruf, nie als Array (Google-Entwicklerdoku).
 *  - Konfiguration (AW-ID, Labels, Telefonanzeige) kommt aus konfig.js. Enthält sie noch Platzhalter,
 *    lädt nichts und die Konsole sagt "Messung nicht konfiguriert".
 *  - Conversion-Aktionen: phone_click, whatsapp_click (Klicks auf data-messung), form_submit (ruft
 *    formular.js nach ok:true über window.kgeMessung auf). Jede mit send_to "AW-…/Label".
 *  - Banner höchstens 110 px hoch, sitzt über der Sticky-Callbar und verdeckt die Hero-Knöpfe nicht.
 *  - Entscheidung in localStorage ('kge-einwilligung-v2'), Widerruf über den Fußlink
 *    data-einwilligung-oeffnen (Art. 7 Abs. 3 DSGVO).
 */
(function () {
  "use strict";
  var SCHLUESSEL = "kge-einwilligung-v2";
  var konfig = window.KGE_KONFIG || {};
  var tagGeladen = false;

  function konfiguriert() {
    if (!konfig.googleTag || /X{4,}/.test(konfig.googleTag)) return false;
    var l = konfig.labels || {};
    return ["phone_click", "whatsapp_click", "form_submit"].every(function (k) {
      return l[k] && !/X{4,}/.test(l[k]);
    });
  }

  function lies() {
    try { var roh = localStorage.getItem(SCHLUESSEL); return roh ? JSON.parse(roh) : null; }
    catch (e) { return null; }
  }
  function schreibe(werbung) {
    try { localStorage.setItem(SCHLUESSEL, JSON.stringify({ werbung: !!werbung, zeit: new Date().toISOString() })); }
    catch (e) { /* Privatmodus: Entscheidung gilt nur für diesen Aufruf */ }
  }

  /* gtag-Funktion exakt nach Google-Snippet: dataLayer.push(arguments), kein Array. */
  function stelleGtag() {
    window.dataLayer = window.dataLayer || [];
    if (typeof window.gtag !== "function") {
      window.gtag = function gtag() { window.dataLayer.push(arguments); };
    }
  }

  function consentDefault() {
    stelleGtag();
    window.gtag("consent", "default", {
      ad_storage: "denied",
      ad_user_data: "denied",
      ad_personalization: "denied",
      analytics_storage: "denied",
      wait_for_update: 500
    });
  }

  function ladeTag() {
    if (tagGeladen) return;
    if (!konfiguriert()) {
      console.info("[Messung] Messung nicht konfiguriert: konfig.js enthält Platzhalter, es wird nichts geladen.");
      return;
    }
    tagGeladen = true;
    consentDefault();
    window.gtag("consent", "update", {
      ad_storage: "granted",
      ad_user_data: "granted",
      ad_personalization: "denied",
      analytics_storage: "denied"
    });
    window.gtag("js", new Date());
    window.gtag("config", konfig.googleTag, {
      phone_conversion_number: konfig.telefonAnzeige || "",
      allow_ad_personalization_signals: false
    });
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(konfig.googleTag);
    document.head.appendChild(s);
  }

  /* Conversion melden. Ohne Einwilligung oder ohne Konfiguration passiert nichts. */
  window.kgeMessung = function (aktion) {
    if (!tagGeladen) {
      if (!konfiguriert()) console.info("[Messung] Messung nicht konfiguriert: " + aktion + " nicht gesendet.");
      return false;
    }
    var label = (konfig.labels || {})[aktion];
    if (!label) return false;
    window.gtag("event", "conversion", { send_to: konfig.googleTag + "/" + label });
    return true;
  };

  document.addEventListener("click", function (e) {
    var el = e.target.closest && e.target.closest("[data-messung]");
    if (!el) return;
    var aktion = el.getAttribute("data-messung");
    if (aktion === "phone_click" || aktion === "whatsapp_click") window.kgeMessung(aktion);
  });

  var stil = document.createElement("style");
  stil.textContent =
    "#kge-einwilligung{position:fixed;left:0;right:0;bottom:calc(var(--callbar-h,64px) + env(safe-area-inset-bottom));z-index:60;" +
    "background:#F3F6F8;color:#16222D;border-top:2px solid #0D1B27;font-family:Archivo,system-ui,sans-serif;max-height:110px;overflow:hidden;" +
    "padding:10px 16px}" +
    "@media (min-width:900px){#kge-einwilligung{bottom:0}}" +
    "#kge-einwilligung .innen{max-width:1100px;margin:0 auto;display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;justify-content:space-between}" +
    "#kge-einwilligung p{margin:0;font-size:13px;line-height:1.35;flex:1 1 220px;max-width:none}" +
    "#kge-einwilligung a{color:#16222D;font-weight:600}" +
    "#kge-einwilligung .knoepfe{display:flex;gap:8px;flex:0 0 auto}" +
    "#kge-einwilligung button{font:inherit;font-size:14px;font-weight:700;cursor:pointer;border-radius:6px;padding:9px 14px;min-width:104px;border:2px solid #0D1B27;color:#0D1B27;background:#fff}" +
    "#kge-einwilligung button.ja{background:#F5A00A}" +
    "#kge-einwilligung button:hover{background:#FFB42E}" +
    "#kge-einwilligung button.nein:hover{background:#E4E9EE}" +
    "#kge-einwilligung button:focus-visible{outline:3px solid #F5A00A;outline-offset:2px}" +
    "@media (max-width:420px){#kge-einwilligung .knoepfe{flex:1 1 100%}#kge-einwilligung button{flex:1 1 0;min-width:0}}";

  function zeige() {
    if (document.getElementById("kge-einwilligung")) return;
    if (!stil.parentNode) document.head.appendChild(stil);
    var kasten = document.createElement("div");
    kasten.id = "kge-einwilligung";
    kasten.setAttribute("role", "dialog");
    kasten.setAttribute("aria-label", "Einwilligung zur Werbe-Messung");
    kasten.innerHTML =
      '<div class="innen">' +
      "<p><b>Werbe-Messung erlauben?</b> Wir messen nur mit Ihrer Einwilligung, ob nach einem Anzeigenklick angerufen oder angefragt wird (Google Ads). " +
      '<a href="datenschutz.html#messung">Details</a></p>' +
      '<div class="knoepfe"><button type="button" class="nein" id="kge-e-nein">Ablehnen</button>' +
      '<button type="button" class="ja" id="kge-e-ja">Erlauben</button></div></div>';
    document.body.appendChild(kasten);
    document.getElementById("kge-e-nein").addEventListener("click", function () { schreibe(false); kasten.remove(); });
    document.getElementById("kge-e-ja").addEventListener("click", function () { schreibe(true); kasten.remove(); ladeTag(); });
  }

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
    if (wahl.werbung) ladeTag();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
