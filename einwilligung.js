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
 *    formular.js nach ok:true über window.kgeMessung auf). Jede mit send_to "AW-…/Label". Dazu wahlweise
 *    website_call: Nummerntausch gegen Googles Weiterleitungsnummer (Anruf ab Mindestdauer), siehe konfig.js.
 *    Getauscht wird nur in Links mit data-messung="phone_click"; der Widerruf stellt die echte Nummer in
 *    jedem Tab und nach der Zurück-Taste wieder her, bevor die Seite neu lädt. Zeuge: pruefen/zeuge-einwilligung.js.
 *  - Banner höchstens 110 px hoch, sitzt über der Sticky-Callbar. Er steht ab dem Laden im DOM, bleibt aber
 *    verborgen, bis der Besucher scrollt oder vier Sekunden vergangen sind (Künstler K4), und erscheint nie,
 *    solange er einen Hero-Knopf verdecken würde. Beobachtet wird mit IntersectionObserver, kein Scroll-Lauscher.
 *    Über den Fußlink erscheint er sofort.
 *  - Entscheidung in localStorage ('kge-einwilligung-v2'), Widerruf über den Fußlink
 *    data-einwilligung-oeffnen (Art. 7 Abs. 3 DSGVO). Wer erst erlaubt und dann ablehnt, bekommt sofort
 *    gtag('consent','update', alle vier Werte denied) als arguments-Aufruf, danach geht keine Conversion mehr
 *    raus, gespeichert ist werbung:false, und im Modus "einfach" lädt die Seite sofort neu, sodass kein
 *    Google-Tag mehr im Speicher läuft. Jedes Ablehnen löscht die Cookies _gcl_*, _gac_* und gwcc (Host und
 *    Elterndomains, Pfad /), auch ohne vorheriges Erlauben in diesem Aufruf und in beiden Modi; neu geladen
 *    wird nur, wenn in diesem Aufruf gtag.js angehängt war. Dazu fällt der localStorage-Schlüssel _gcl_ls.
 *    Der Fußlink selbst ändert nichts, erst die Wahl.
 *  - Zurück-Taste (bfcache, pageshow mit persisted) und andere Tabs (storage-Ereignis zum Schlüssel): Ein Dokument,
 *    das noch die alte Erlaubnis trägt, liest die gespeicherte Wahl neu und verfährt bei werbung:false wie beim
 *    Ablehnen (Update denied, Cookies löschen, neu laden nur mit angehängtem gtag.js). Es schreibt dabei nichts,
 *    deshalb stößt es in keinem Tab ein weiteres storage-Ereignis an (Programmierer-Fund 4, Auflage A6, 10.11.2026).
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
    wendeNummerAn();  /* schon gelieferte Weiterleitungsnummer wieder zeigen (Fund 6); ohne Lieferung wirkungslos */
  }

  /* default steht schon (consentDefault); haengt config und gtag.js genau einmal an. */
  function haengeTagAn() {
    if (skriptAngehaengt || !konfiguriert()) return;
    skriptAngehaengt = true;
    window.gtag("js", new Date());
    window.gtag("config", konfig.googleTag, { allow_ad_personalization_signals: false });
    /* Website-Anruf-Conversion: Google verlangt dafür ein eigenes config mit Label ("AW-…/Label") und
       tauscht nur dann die Nummer (Hilfe 6095883; ohne Label griff der Tausch nie, Fund 18.11.2026).
       Ist labels.website_call leer, bleibt die echte Nummer stehen und nur phone_click zählt. */
    var anruf = (konfig.labels || {}).website_call;
    if (anruf && konfig.telefonAnzeige && /^[A-Za-z0-9_-]+$/.test(anruf) && !/X{4,}/.test(anruf)) {
      window.gtag("config", konfig.googleTag + "/" + anruf, {
        allow_ad_personalization_signals: false,
        phone_conversion_number: konfig.telefonAnzeige,
        phone_conversion_callback: tauscheNummer
      });
    } else if (anruf) {
      /* Gesetzt, aber unbrauchbar: nicht stumm bleiben (Programmierer r1, Fund 7). bauen.py bricht in diesem
         Fall ab, sobald NOINDEX aus ist. */
      console.info("[Messung] labels.website_call verworfen (Platzhalter, unzulässige Zeichen oder telefonAnzeige fehlt): kein Nummerntausch, Anrufe über die Seite zählen nur als phone_click.");
    }
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(konfig.googleTag);
    document.head.appendChild(s);
  }

  /* Google ruft tauscheNummer nach einem Anzeigenklick mit der Weiterleitungsnummer auf (formatiert für die
   * Anzeige, mobil für tel:).
   *  - Getauscht wird nur in Links mit data-messung="phone_click" (Kopf, Hero, Inhalt, Fuß, Anrufleiste), Text und
   *    Ziel zusammen, damit nie eine Nummer sichtbar ist und eine andere gewählt wird. Der Telefon-Link im
   *    Impressum trägt das Attribut nicht und bleibt die echte Nummer (Programmierer r1, Fund 4).
   *  - Klartext der echten Nummer direkt neben einem getauschten Link (data-echte-nummer, etwa „(+49 2161 …)“)
   *    ist ausgeblendet, solange getauscht ist: sonst stünden zwei verschiedene Nummern als dieselbe
   *    nebeneinander (Fund 5). Impressum, JSON-LD, Meta und Datenschutztext tragen das Attribut nicht.
   *  - Brauchbar ist ein Aufruf nur, wenn beide Werte mindestens MIN_ZIFFERN und höchstens MAX_ZIFFERN Ziffern
   *    tragen und dieselbe Nummer sind (gleicheNummer). Sonst wird gar nichts getauscht, weder Text noch Ziel,
   *    und die echte Nummer bleibt (Fund 10; Paarprüfung nach dem Wissenschaftler-Bericht vom 18.11.2026, C4).
   *  - Gewirkt wird nur einmal (ein zweiter Aufruf ändert die Anzeige nicht) und nur bei erteilter Einwilligung.
   *    Die zuletzt gelieferte brauchbare Nummer bleibt in `geliefert`; ladeTag wendet sie wieder an, wenn nach
   *    einem Widerruf ohne Neuladen erneut erlaubt wird (Fund 6). Im Modus "einfach" lädt der Widerruf die
   *    Seite neu, dort kommt dieser Weg nicht vor; er trägt den Modus "erweitert", in dem Google nach dem
   *    Erlauben nicht noch einmal aufruft (Fund 12).
   *  - Die alte Fassung steht in `getauscht` und `verborgen`; nummerZurueck stellt alles wieder her. */
  var MIN_ZIFFERN = 6, MAX_ZIFFERN = 15;  /* 15: längste Rufnummer nach E.164 */
  var getauscht = [], verborgen = [], geliefert = null;
  function tauscheNummer(formatiert, mobil) {
    var anzeige = String(formatiert == null ? "" : formatiert).trim();
    var roh = String(mobil == null ? "" : mobil).replace(/^\s*tel:/i, "");
    var ziffern = roh.replace(/\D/g, "");
    var anzeigeZiffern = anzeige.replace(/\D/g, "");
    if (anzeigeZiffern.length < MIN_ZIFFERN || ziffern.length < MIN_ZIFFERN) return;
    if (anzeigeZiffern.length > MAX_ZIFFERN || ziffern.length > MAX_ZIFFERN) return;
    if (!gleicheNummer(anzeigeZiffern, ziffern)) return;
    geliefert = { anzeige: anzeige, ziel: "tel:" + (/^\s*\+/.test(roh) ? "+" : "") + ziffern };
    wendeNummerAn();
  }
  /* Paarprüfung: Anzeige und Ziel müssen dieselbe Nummer sein, sonst stünde eine Nummer da und eine andere würde
   * gewählt. Die Ziffern der Anzeige ohne führende Nullen (nationale Schreibweise) müssen am Ende der Ziffern des
   * Ziels stehen (das Ziel darf die Ländervorwahl tragen). Passt das Paar nicht, wird nichts getauscht. */
  function gleicheNummer(anzeigeZiffern, zielZiffern) {
    var kern = anzeigeZiffern.replace(/^0+/, "");
    return kern.length > 0 && zielZiffern.slice(-kern.length) === kern;
  }
  function wendeNummerAn() {
    var alt = konfig.telefonAnzeige;
    if (!tagGeladen || !alt || !geliefert || getauscht.length) return;
    var links = document.querySelectorAll('a[href^="tel:"][data-messung="phone_click"]');
    for (var i = 0; i < links.length; i++) {
      var eintrag = { el: links[i], href: links[i].getAttribute("href"), texte: [] };
      var lauf = document.createTreeWalker(links[i], NodeFilter.SHOW_TEXT, null);
      var knoten;
      while ((knoten = lauf.nextNode())) {
        if (knoten.nodeValue.indexOf(alt) === -1) continue;
        eintrag.texte.push([knoten, knoten.nodeValue]);
        knoten.nodeValue = knoten.nodeValue.split(alt).join(geliefert.anzeige);
      }
      links[i].setAttribute("href", geliefert.ziel);
      getauscht.push(eintrag);
    }
    if (!getauscht.length) return;
    var klartext = document.querySelectorAll("[data-echte-nummer]");
    for (var k = 0; k < klartext.length; k++) {
      verborgen.push([klartext[k], klartext[k].hidden]);
      klartext[k].hidden = true;
    }
  }
  function nummerZurueck() {
    getauscht.forEach(function (e) {
      e.el.setAttribute("href", e.href);
      e.texte.forEach(function (t) { t[0].nodeValue = t[1]; });
    });
    verborgen.forEach(function (v) { v[0].hidden = v[1]; });
    getauscht = [];
    verborgen = [];
  }

  /* Widerruf: Lief der Tag schon, erfährt er sofort, dass nichts mehr erlaubt ist (gleicher arguments-Weg
   * wie das Erlauben). Danach meldet kgeMessung im Modus "einfach" nichts mehr, im Modus "erweitert" nur noch
   * cookielose Pings; gespeichert wird beim Aufrufer (schreibe(false)). Die echte Telefonnummer kommt zurück,
   * damit nach dem Widerruf kein Anruf mehr über Googles Weiterleitung läuft. Das gilt in jedem Dokument, das den
   * Widerruf erfährt: im Tab des Widerrufs, in anderen Tabs (storage) und nach der Zurück-Taste (pageshow),
   * siehe pruefeGespeichert. Ein Tab, den der Browser eingefroren hat, erfährt es erst beim Aufwachen. */
  function widerrufe() {
    /* Zuerst und synchron die echte Telefonnummer, noch vor dem Neuladen: gilt für jeden Weg hierher
     * (Ablehnen im Banner, anderer Tab, Zurück-Taste). */
    nummerZurueck();
    var warErlaubt = tagGeladen;  /* nicht erlaubt in diesem Aufruf: default denied gilt weiter, nichts zu melden */
    if (warErlaubt) {
      tagGeladen = false;
      window.gtag("consent", "update", {
        ad_storage: "denied",
        ad_user_data: "denied",
        ad_personalization: "denied",
        analytics_storage: "denied"
      });
    }
    /* Bei jedem Ablehnen, in beiden Modi: Cookies aus einer früheren Erlaubnis dürfen nicht bleiben, auch wenn in
     * diesem Aufruf nie erlaubt wurde (Programmierer-Fund 3, Runde PR 2, 10.11.2026). */
    loescheGoogleCookies();  /* Widerruf: Cookies weg */
    /* Nur im Modus "einfach" und nur nach einem Erlauben in diesem Aufruf: die Seite lädt neu, damit gtag.js nicht
     * im Speicher weiterläuft (Programmierer-Fund 7, 10.11.2026). Die Ablehnung ist vorher gespeichert
     * (schreibe(false) beim Aufrufer). Ein halb ausgefülltes Formular geht dabei verloren; das ist in Kauf
     * genommen, weil sonst gtag.js weiterliefe. */
    if (warErlaubt && skriptAngehaengt && !erweitert) window.location.reload();
  }

  /* Löscht _gcl_* und _gac_* (Conversion-Linker) und gwcc (Speicher der Weiterleitungsnummer, Google-Hilfe 6095883)
   * für den Host und jede übergeordnete Domain (gtag setzt sie auf die oberste mögliche), dazu den localStorage-
   * Schlüssel _gcl_ls (Tag-Manager-Hilfe 7549390). Ob das echte gtag.js danach nichts zurückschreibt, zeigt erst
   * die Messung mit echtem Tag am Tag der Kontoanlage (DEPLOY.md). */
  function loescheGoogleCookies() {
    try { localStorage.removeItem("_gcl_ls"); } catch (e) { /* Speicher gesperrt: nichts zu löschen */ }
    var namen = document.cookie.split(";").map(function (c) { return c.split("=")[0].trim(); })
      .filter(function (n) { return /^_gcl_|^_gac_|^gwcc$/.test(n); });
    var teile = window.location.hostname.split(".");
    var domains = [""];
    for (var i = 0; i < teile.length - 1; i++) domains.push("; domain=." + teile.slice(i).join("."));
    namen.forEach(function (n) {
      domains.forEach(function (d) { document.cookie = n + "=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/" + d; });
    });
  }

  /* Conversion melden. Ohne Konfiguration passiert nichts; ohne Einwilligung nur im Modus "erweitert" (cookielos). */
  window.kgeMessung = function (aktion) {
    /* Vor jedem Senden den gespeicherten Stand lesen: Hat ein anderer Tab widerrufen und das storage-Ereignis kam
       hier nicht an (eingefrorener oder ausgesetzter Tab), läuft der Widerruf jetzt hier nach (echte Nummer,
       denied, Cookies, Neuladen), und gesendet wird nichts (Wissenschaftler 18.11.2026, C3). */
    pruefeGespeichert();
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
    /* --leiste-unten ist 0, solange die Anrufleiste ausgeblendet ist (leiste.js), sonst ihre Höhe (Mobil-Ausbau 17.11.2026) */
    /* Verschoben per transform statt bottom: ein Wechsel über bottom zählte als Layout-Verschiebung
       (0,0133 bis 0,0526 je Wechsel, Wissenschaftler r2, S1); transform zählt nicht. */
    "#kge-einwilligung{position:fixed;left:0;right:0;bottom:env(safe-area-inset-bottom);transform:translateY(calc(-1 * var(--leiste-unten,var(--callbar-h,64px))));z-index:60;" +
    "background:#F3F6F8;color:#16222D;border-top:2px solid #0D1B27;font-family:Archivo,system-ui,sans-serif;" +
    "padding:9px 16px}" +
    "@media (min-width:900px){#kge-einwilligung{bottom:0;transform:none}}" +
    "#kge-einwilligung .innen{max-width:1100px;margin:0 auto;display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;justify-content:space-between}" +
    /* Verborgen per visibility statt display:none: so bleibt der Banner vermessbar (Höhe, Safe-Area), und
       verdecktHero rechnet mit seiner echten Kante statt mit geschätzten 110 px (Programmierer r4, SOLL 1). */
    "#kge-einwilligung[hidden]{display:block;visibility:hidden}" +
    "#kge-einwilligung p{margin:0;font-size:14px;line-height:1.35;flex:1 1 220px;max-width:none;min-width:0}" +
    "#kge-einwilligung a{color:#16222D;font-weight:700;display:inline-block;padding:13px 4px;margin:-13px 0}" +
    "#kge-einwilligung .knoepfe{display:flex;gap:8px;flex:0 0 auto}" +
    "#kge-einwilligung button{font:inherit;font-size:14px;font-weight:700;cursor:pointer;border-radius:6px;padding:9px 14px;min-width:104px;min-height:44px;border:2px solid #0D1B27;color:#0D1B27;background:#fff}" +
    /* Erlauben und Ablehnen gleich gestaltet: Amber heißt auf der Seite nur „anrufen“, und keine Wahl wird
       optisch vorgezogen (Künstler 17.11.2026, MUSS 2: Tippen auf „das Orange“ landete in der Datenschutzfrage). */
    "#kge-einwilligung button:hover{background:#E4E9EE}" +
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
      "<p>Darf diese Seite mit Google messen, ob eine Google-Anzeige Sie zu Ihrem Anruf geführt hat? " +
      '<a href="datenschutz.html#messung">Details</a></p>' +
      '<div class="knoepfe"><button type="button" class="nein" id="kge-e-nein">Ablehnen</button>' +
      '<button type="button" class="ja" id="kge-e-ja">Erlauben</button></div></div>';
    document.body.appendChild(kasten);
    document.getElementById("kge-e-nein").addEventListener("click", function () { schreibe(false); fertig(); kasten.remove(); melde(); widerrufe(); });
    document.getElementById("kge-e-ja").addEventListener("click", function () { schreibe(true); fertig(); kasten.remove(); melde(); ladeTag(); });
    return kasten;
  }

  /* Sagt leiste.js, dass der Banner auf- oder zugegangen ist: solange er offen ist, misst die Leiste den
     Anrufknopf über der Bannerkante (Wissenschaftler r3, S1). */
  function melde() { document.dispatchEvent(new Event("kge-banner")); }

  function zeigeSofort() { fertig(); baue().hidden = false; melde(); }

  /* Würde der Banner einen Hero-Knopf oder die Sternchenerklärung verdecken? Gerechnet mit der gemessenen
     Kante von Banner und Anrufleiste (kante()). Die Sternchenerklärung gehört dazu, weil sie bei 390 x 664 sonst nach 4 s unter dem
     Banner lag (Spieltheoretiker 17.11.2026, M2). Bewertungskasten und Namenszeile (bauen.py, BEWERTUNG_ZEIGEN und
     NAME_ZEIGEN) gehören dazu, weil der Hinweis nach § 5b Abs. 3 UWG ohne Klick lesbar bleiben muss; ohne sie lag der
     Kasten bei 390 x 844 bis y 784 unter dem Banner ab y 734 (Bau kge-cta, 20.11.2026). */
  var FREI_HALTEN = ".hero .knoepfe .knopf, .hero .stern, .hero .bewertung, .hero .name-zeile";
  /* Gemessene Kante: Abstand der Banner-Oberkante vom unteren Rand bei ausgeblendeter Anrufleiste (Höhe plus
     Safe-Area) und die Höhe der Leiste, falls sie sichtbar ist. Die Leiste zählt nur mit, wenn sie sichtbar ist
     (leiste.js setzt leiste-aus; Programmierer und Spieltheoretiker r2, K1). */
  function kante() {
    var leiste = window.innerWidth < 900 && !document.documentElement.classList.contains("leiste-aus");
    var bar = document.querySelector(".callbar");
    var lh = leiste && bar ? bar.offsetHeight : 0;
    var k = document.getElementById("kge-einwilligung");
    var r = k ? k.getBoundingClientRect() : null;
    var basis = r && r.height > 0 ? Math.round(window.innerHeight - r.top - lh) : 110;
    return { basis: basis, leiste: lh };
  }
  function verdecktHero(zusatz) {
    var m = kante();
    var grenze = window.innerHeight - m.basis - m.leiste - (zusatz || 0);
    var knoepfe = document.querySelectorAll(FREI_HALTEN);
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
    /* Der Banner weicht dem Hero, solange er offen ist: Scrollt der Besucher zurück nach oben, deckte er sonst
       Sternchen und im Querformat den Anrufknopf (Spieltheoretiker r3, S1). Die Beobachter bleiben deshalb bis
       zur Entscheidung (Ablehnen oder Erlauben) verbunden; fertig() trennt sie dort.
       Hysterese: Er weicht, sobald er den Hero berührt, kommt aber erst wieder, wenn 32 px Luft sind. Ohne sie
       wechselte er beim Pendeln um 1 px an der Kante 20-mal in 20 Schritten (Wissenschaftler und Spieltheoretiker
       r4, S1). Die 32 px halten bei 390 x 664 auch die Öffnungszeiten frei (Spieltheoretiker r3, K1). */
    var LUFT = 32;
    function versuch() {
      if (!kasten.isConnected) return;
      beobachte();
      var verborgen = !(gescrollt || zeitUm) || verdecktHero(kasten.hidden ? LUFT : 0);
      if (verborgen === kasten.hidden) return;
      kasten.hidden = verborgen;
      melde();
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
    /* Hero-Knöpfe und Sternchenerklärung: bei jeder Bewegung über die Bannerkante neu prüfen. */
    /* Vier Kanten aus der gemessenen Bannerkante: ohne und mit sichtbarer Anrufleiste, je mit und ohne LUFT.
       Ändert sich die Messung (Drehen, Schriftgröße, Safe-Area), werden die Beobachter neu gesetzt;
       verdecktHero entscheidet. */
    var kanten = [], gemessen = "";
    function beobachte() {
      if (!("IntersectionObserver" in window)) return;
      var m = kante(), b = m.basis, l = m.leiste || (window.innerWidth < 900 ? 64 : 0);
      var schluessel = b + "/" + l;
      if (schluessel === gemessen) return;
      gemessen = schluessel;
      kanten.forEach(function (x) { x.disconnect(); });
      kanten = [b, b + LUFT, b + l, b + l + LUFT].map(function (px) {
        return new IntersectionObserver(versuch, { rootMargin: "0px 0px -" + px + "px 0px", threshold: [0, 0.5, 1] });
      });
      document.querySelectorAll(FREI_HALTEN).forEach(function (k) { kanten.forEach(function (x) { x.observe(k); }); });
    }
    beobachte();
    document.addEventListener("kge-leiste", versuch);
    window.addEventListener("resize", versuch);
    aufraeumen.push(function () {
      oben.disconnect(); kanten.forEach(function (x) { x.disconnect(); }); merker.remove();
      document.removeEventListener("kge-leiste", versuch);
      window.removeEventListener("resize", versuch);
    });
  }

  document.addEventListener("click", function (e) {
    var el = e.target.closest && e.target.closest("[data-einwilligung-oeffnen]");
    if (!el) return;
    e.preventDefault();
    /* Nur den Banner zeigen; gespeichert und widerrufen wird erst mit der Entscheidung (Fund 7). */
    zeigeSofort();
  });

  /* Widerruf aus einem anderen Dokument: nur wenn hier noch erlaubt ist und gespeichert ausdrücklich werbung:false
   * steht (ein leerer oder unlesbarer Speicher ist kein Widerruf). Kein schreibe(): der Speicher stimmt schon. */
  function pruefeGespeichert() {
    var wahl = lies();
    if (tagGeladen && wahl && wahl.werbung === false) widerrufe();
  }
  window.addEventListener("pageshow", function (e) { if (e.persisted) pruefeGespeichert(); });
  window.addEventListener("storage", function (e) { if (e.key === SCHLUESSEL) pruefeGespeichert(); });
  /* Tab kommt wieder nach vorn: storage-Ereignisse aus der Zeit im Hintergrund können fehlen (C3). */
  document.addEventListener("visibilitychange", function () { if (!document.hidden) pruefeGespeichert(); });

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
