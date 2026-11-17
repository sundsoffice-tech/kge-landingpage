/* leiste.js: Die Anrufleiste unten (Handy und Tablet) bleibt aus, solange der Anrufknopf im Hero bedienbar zu sehen
 * ist. Grund: Im ersten Bildschirm standen Anrufen und WhatsApp sonst doppelt, oben groß und unten in der Leiste
 * (Künstler 17.11.2026, SOLL 1). Beobachtet wird nur der Anrufknopf, nicht der ganze Knopfblock: sonst gab es je
 * nach Größe 42 bis 122 px Scrollweg ganz ohne Anrufknopf (Spieltheoretiker und Wissenschaftler r2, M1).
 *
 * Regel: Die Leiste kommt, wenn weniger als 66 % des Knopfs frei sind (44 von 67 px Trefferfläche), und geht erst
 * wieder ab 99 %. Das Band dazwischen verhindert Flattern bei kleinen Scrollbewegungen (Wissenschaftler r3, K1).
 * Solange der Einwilligungsbalken offen ist, zählt nur der Teil über seiner Kante: sonst lag der Knopf bei kleinen
 * Höhen und im Querformat unter dem Balken, während die Leiste aus war (Wissenschaftler r3, S1). einwilligung.js
 * meldet Auf und Zu mit dem Ereignis „kge-banner“.
 *
 * Die Klasse leiste-aus am <html> blendet die Leiste ohne Übergang aus und setzt --leiste-unten auf 0, damit der
 * Balken an den unteren Rand rückt. Ohne Hero (Unterseiten) oder ohne IntersectionObserver bleibt die Leiste immer
 * sichtbar. Steht synchron direkt VOR der Leiste in <body>: Solange das Skript lädt, ist die Leiste noch nicht
 * geparst und kann nicht gemalt werden (dahinter blitzte sie in 3 von 14 Ladevorgängen auf, Programmierer r3). */
(function () {
  var anruf = document.querySelector(".hero .knoepfe .knopf");
  if (!anruf || !("IntersectionObserver" in window)) return;
  var wurzel = document.documentElement;
  var KOMMT = 0.66, GEHT = 0.99;
  var STUFEN = [0, 0.25, 0.5, 0.65, 0.66, 0.67, 0.98, 0.99, 1];
  var voll = 1, ueberBalken = 1, balkenBeob = null, aus = null;

  function anteil(unten) {
    var r = anruf.getBoundingClientRect();
    if (r.height <= 0) return 0;
    return Math.max(0, Math.min(r.bottom, unten) - Math.max(r.top, 0)) / r.height;
  }
  function entscheide() {
    var a = Math.min(voll, ueberBalken), vorher = aus;
    aus = aus === null ? a >= KOMMT : (aus ? a >= KOMMT : a >= GEHT);
    wurzel.classList.toggle("leiste-aus", aus);
    /* einwilligung.js prüft dann neu, ob der Banner den Hero verdeckt (die Leiste schiebt ihn um 64 px hoch). */
    if (vorher !== null && vorher !== aus) document.dispatchEvent(new Event("kge-leiste"));
  }
  function balkenGeaendert() {
    if (balkenBeob) { balkenBeob.disconnect(); balkenBeob = null; }
    ueberBalken = 1;
    var b = document.getElementById("kge-einwilligung");
    var h = 0;
    if (b && !b.hidden && b.isConnected) {
      /* Gemessene Kante des Balkens bei ausgeblendeter Leiste (Höhe plus Safe-Area; Programmierer r4, SOLL 1). */
      var bar = document.querySelector(".callbar");
      var lh = !aus && bar ? bar.offsetHeight : 0;
      h = Math.round(window.innerHeight - b.getBoundingClientRect().top - lh);
    }
    if (h > 0) {
      ueberBalken = anteil(window.innerHeight - h);
      balkenBeob = new IntersectionObserver(function (e) {
        ueberBalken = e[e.length - 1].intersectionRatio; entscheide();
      }, { rootMargin: "0px 0px -" + h + "px 0px", threshold: STUFEN });
      balkenBeob.observe(anruf);
    }
    entscheide();
  }

  voll = anteil(window.innerHeight);
  entscheide();
  new IntersectionObserver(function (e) {
    voll = e[e.length - 1].intersectionRatio; entscheide();
  }, { threshold: STUFEN }).observe(anruf);
  document.addEventListener("kge-banner", balkenGeaendert);
  /* Drehen oder neue Fenstergröße bei offenem Balken: Kante neu messen (Programmierer r4, K5). */
  window.addEventListener("resize", balkenGeaendert);
})();
