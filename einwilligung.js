/* Einwilligung und Messung (§ 25 TDDDG, Google Consent Mode v2) · Kfz Gutachter Es · S&S Connect
 *
 * Regeln, die dieses Skript technisch einhält:
 *  - Modus aus konfig.js (einwilligungsModus). "einfach" (Basic, gilt auch bei fehlendem oder falsch
 *    geschriebenem Schalter): vor dem Erlauben lädt nichts von Google und es geht keine Anfrage an Google.
 *    "erweitert" (cookielose Pings ohne Ja) ist von der Rechtsrolle am 10.11.2026 VERNEINT (§ 25 Abs. 1 TDDDG,
 *    der Ping liest Bildschirmmaße; docs/rollen-recht-consent-mode-2026-11-10.md im Repo leadmaschine).
 *    Der Code dafür bleibt nur für den Fall einer neuen Rechtsprüfung; nicht ohne sie einschalten.
 *  - gtag('consent','default', alles denied, wait_for_update 500) steht vor dem Google-Tag und vor jedem
 *    config oder event; 'update' beim Klick als arguments-Aufruf, nie als Array (Google-Entwicklerdoku).
 *  - Konfiguration (AW-ID, Labels, Telefonanzeige) kommt aus konfig.js. Enthält sie noch Platzhalter,
 *    lädt nichts und die Konsole sagt "Messung nicht konfiguriert".
 *  - Conversion-Aktionen: phone_click, whatsapp_click (Klicks auf data-messung), form_submit (ruft
 *    formular.js nach ok:true über window.kgeMessung auf). Jede mit send_to "AW-…/Label".
 *  - Banner höchstens 110 px hoch, sitzt über der Sticky-Callbar. Er steht ab dem Laden im DOM, bleibt aber
 *    verborgen, bis der Besucher scrollt oder vier Sekunden vergangen sind (Künstler K4), und erscheint nie,
 *    solange er einen Hero-Knopf verdecken würde. Beobachtet wird mit IntersectionObserver, kein Scroll-Lauscher.
 *    Über den Fußlink erscheint er sofort.
 *  - Entscheidung in localStorage ('kge-einwilligung-v2'), Widerruf über den Fußlink
 *    data-einwilligung-oeffnen (Art. 7 Abs. 3 DSGVO). Wer erst erlaubt und dann ablehnt, bekommt sofort
 *    gtag('consent','update', alle vier Werte denied) als arguments-Aufruf, danach geht keine Conversion mehr
 *    raus, und gespeichert ist werbung:false, sodass nach dem Neuladen kein Google-Tag mehr lädt.
 */
(function () {
  "use strict";
  var SCHLUESSEL = "kge-einwilligung-v2";
  var konfig = window.KGE_KONFIG || {};
  var tagGeladen = false;     /* Einwilligung in diesem Aufruf erteilt und gemeldet */
  var skriptAngehaengt = false; /* gtag.js, default und config stehen schon in der Seite */
  var erweitert = konfig.einwilligungsModus === "erweitert";  /* fehlt der Schalter, gilt einfach (Rechtsrolle 10.11.2026, § 25 TDDDG) */

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

  var defaultGesetzt = false;
  function consentDefault() {
    if (defaultGesetzt) return;
    defaultGesetzt = true;
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
    /* Erneutes Erlauben nach einem Widerruf im selben Aufruf: nur das Update, kein zweites gtag.js. */
    consentDefault();  /* idempotent */
    window.gtag("consent", "update", {
      ad_storage: "granted",
      ad_user_data: "granted",
      ad_personalization: "denied",
      analytics_storage: "denied"
    });
    haengeTagAn();
  }

  /* default steht schon (consentDefault); haengt config und gtag.js genau einmal an. */
  function haengeTagAn() {
    if (skriptAngehaengt || !konfiguriert()) return;
    skriptAngehaengt = true;
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

  /* Widerruf: Lief der Tag schon, erfährt er sofort, dass nichts mehr erlaubt ist (gleicher arguments-Weg
   * wie das Erlauben). Danach meldet kgeMessung im Modus "einfach" nichts mehr, im Modus "erweitert" nur noch
   * cookielose Pings; gespeichert wird beim Aufrufer (schreibe(false)). */
  function widerrufe() {
    if (!tagGeladen) return;  /* nie erlaubt: default denied gilt weiter, nichts zu melden */
    tagGeladen = false;
    window.gtag("consent", "update", {
      ad_storage: "denied",
      ad_user_data: "denied",
      ad_personalization: "denied",
      analytics_storage: "denied"
    });
  }

  /* Conversion melden. Ohne Konfiguration passiert nichts; ohne Einwilligung nur im Modus "erweitert" (cookielos). */
  window.kgeMessung = function (aktion) {
    /* erweitert: gesendet wird immer, sobald der Tag haengt; ohne Einwilligung als cookieloser Ping. */
    if (!tagGeladen && !(erweitert && skriptAngehaengt)) {
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
    "background:#F3F6F8;color:#16222D;border-top:2px solid #0D1B27;font-family:Archivo,system-ui,sans-serif;" +
    "padding:9px 16px}" +
    "@media (min-width:900px){#kge-einwilligung{bottom:0}}" +
    "#kge-einwilligung .innen{max-width:1100px;margin:0 auto;display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;justify-content:space-between}" +
    "#kge-einwilligung[hidden]{display:none}" +
    "#kge-einwilligung p{margin:0;font-size:14px;line-height:1.35;flex:1 1 220px;max-width:none;min-width:0}" +
    "#kge-einwilligung a{color:#16222D;font-weight:700;display:inline-block;padding:13px 4px;margin:-13px 0}" +
    "#kge-einwilligung .knoepfe{display:flex;gap:8px;flex:0 0 auto}" +
    "#kge-einwilligung button{font:inherit;font-size:14px;font-weight:700;cursor:pointer;border-radius:6px;padding:9px 14px;min-width:104px;min-height:44px;border:2px solid #0D1B27;color:#0D1B27;background:#fff}" +
    "#kge-einwilligung button.ja{background:#F5A00A}" +
    "#kge-einwilligung button:hover{background:#FFB42E}" +
    "#kge-einwilligung button.nein:hover{background:#E4E9EE}" +
    "#kge-einwilligung button:focus-visible{outline:3px solid #F5A00A;outline-offset:2px}" +
    "@media (max-width:420px){#kge-einwilligung .knoepfe{flex:1 1 100%}#kge-einwilligung button{flex:1 1 0;min-width:0}}";

  var aufraeumen = [];
  function fertig() { aufraeumen.forEach(function (f) { f(); }); aufraeumen = []; }

  /* Baut den Banner verborgen ein; die Knöpfe sind ab dem Laden bedienbar (Funktionstest klickt sie direkt). */
  function baue() {
    var da = document.getElementById("kge-einwilligung");
    if (da) return da;
    if (!stil.parentNode) document.head.appendChild(stil);
    var kasten = document.createElement("div");
    kasten.id = "kge-einwilligung";
    kasten.hidden = true;
    kasten.setAttribute("role", "dialog");
    kasten.setAttribute("aria-label", "Einwilligung zur Werbe-Messung");
    kasten.innerHTML =
      '<div class="innen">' +
      "<p>Dürfen wir mit Google Ads messen, ob unsere Anzeige zu Ihrem Anruf geführt hat? " +
      '<a href="datenschutz.html#messung">Details</a></p>' +
      '<div class="knoepfe"><button type="button" class="nein" id="kge-e-nein">Ablehnen</button>' +
      '<button type="button" class="ja" id="kge-e-ja">Erlauben</button></div></div>';
    document.body.appendChild(kasten);
    document.getElementById("kge-e-nein").addEventListener("click", function () { schreibe(false); fertig(); kasten.remove(); widerrufe(); });
    document.getElementById("kge-e-ja").addEventListener("click", function () { schreibe(true); fertig(); kasten.remove(); ladeTag(); });
    return kasten;
  }

  function zeigeSofort() { fertig(); baue().hidden = false; }

  /* Würde der Banner einen Hero-Knopf verdecken? Banner und Callbar zusammen höchstens 110 + 64 px. */
  function verdecktHero() {
    var unten = window.innerWidth < 900 ? 64 + 110 : 110;
    var grenze = window.innerHeight - unten;
    var knoepfe = document.querySelectorAll(".hero .knoepfe .knopf");
    for (var i = 0; i < knoepfe.length; i++) {
      var r = knoepfe[i].getBoundingClientRect();
      if (r.bottom > grenze && r.top < window.innerHeight) return true;
    }
    return false;
  }

  function zeigeSpaeter() {
    var kasten = baue();
    var gescrollt = false;
    var zeitUm = false;
    function versuch() {
      if (!kasten.isConnected || !kasten.hidden) return;
      if (!(gescrollt || zeitUm) || verdecktHero()) return;
      kasten.hidden = false;
      fertig();
    }
    var uhr = setTimeout(function () { zeitUm = true; versuch(); }, 4000);
    aufraeumen.push(function () { clearTimeout(uhr); });
    if (!("IntersectionObserver" in window)) { gescrollt = true; return; }
    /* Merker oben auf der Seite: verlässt er den Sichtbereich, hat der Besucher gescrollt. */
    var merker = document.createElement("div");
    merker.setAttribute("aria-hidden", "true");
    merker.style.cssText = "position:absolute;top:0;left:0;width:1px;height:1px;pointer-events:none";
    document.body.appendChild(merker);
    var oben = new IntersectionObserver(function (eintraege) {
      if (!eintraege[0].isIntersecting) { gescrollt = true; versuch(); }
    });
    oben.observe(merker);
    /* Hero-Knöpfe: bei jeder Bewegung über die Bannerkante neu prüfen. */
    var hero = new IntersectionObserver(versuch, { rootMargin: "0px 0px -174px 0px", threshold: [0, 0.5, 1] });
    document.querySelectorAll(".hero .knoepfe .knopf").forEach(function (k) { hero.observe(k); });
    aufraeumen.push(function () { oben.disconnect(); hero.disconnect(); merker.remove(); });
  }

  document.addEventListener("click", function (e) {
    var el = e.target.closest && e.target.closest("[data-einwilligung-oeffnen]");
    if (!el) return;
    e.preventDefault();
    try { localStorage.removeItem(SCHLUESSEL); } catch (fehler) { /* egal */ }
    zeigeSofort();
  });

  function start() {
    var wahl = lies();
    if (erweitert && konfiguriert()) {
      consentDefault();
      if (wahl && wahl.werbung) { ladeTag(); return; }
      haengeTagAn();
    } else if (!konfiguriert()) {
      console.info("[Messung] Messung nicht konfiguriert: konfig.js enthält Platzhalter, es wird nichts geladen.");
    }
    if (wahl === null) { zeigeSpaeter(); return; }
    if (wahl.werbung && !erweitert) ladeTag();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
