/* Zeuge für einwilligung.js: Einwilligung, Nummerntausch (website_call) und Widerruf.
 *
 * Aufruf: node pruefen/zeuge-einwilligung.js [Pfad zu einwilligung.js]
 * Exit 0, wenn jeder Fall stimmt; Exit 1 bei der ersten Abweichung (jede steht als Zeile "ROT").
 *
 * Ohne Browser und ohne Fremdpaket: das Skript läuft in node vm gegen ein Mini-DOM, das die Telefonstellen der
 * gebauten Startseite nachbildet (Kopf, Hero-Knopf mit verschachteltem Text, Adressliste mit Klartext daneben,
 * Kontaktliste, Fuß mit Klartext daneben, Anrufleiste) und dazu den Impressum-Link ohne data-messung.
 * Keim: Logikprobe des Programmierers zu Runde 1 (Tabelle „Was hält“), erweitert um die Auflagen 4, 5, 6, 7, 10
 * und um den Widerruf über Neuladen, zweiten Tab und Zurück-Taste.
 * Was der Zeuge nicht sieht: Layout, echte Browser-Ereignisse, Googles echten Aufruf des Callbacks. Das Mini-DOM kennt
 * keine Klassen und keine Zeit; der mobile Teil (Banner weicht dem Hero, Anrufleiste, FREI_HALTEN) läuft hier nicht
 * mit Wirkung, B2 prüft davon nur, dass das Ereignis kge-banner gemeldet wird.
 * Die Rotprobe dazu: node pruefen/rotprobe-einwilligung.js. */
"use strict";
const fs = require("fs"), path = require("path"), vm = require("vm");
const DATEI = process.argv[2] || path.join(__dirname, "..", "einwilligung.js");
const QUELLE = fs.readFileSync(DATEI, "utf8");
const SCHL = "kge-einwilligung-v2";
const ECHT = "02161 622 57 68", ECHT_TEL = "tel:+4921616225768";
const G = ["02161 000 11 22", "+49 2161 0001122"], G_ZIEL = "tel:+4921610001122";
const ZIELE_ECHT = [ECHT_TEL, ECHT_TEL, ECHT_TEL, ECHT_TEL, ECHT_TEL, ECHT_TEL];
const ZIELE_G = [G_ZIEL, G_ZIEL, G_ZIEL, G_ZIEL, G_ZIEL, G_ZIEL];
const TEXTE_ECHT = [ECHT, "Jetzt anrufen/" + ECHT, ECHT, ECHT, ECHT, "Anrufen"];
const TEXTE_G = [G[0], "Jetzt anrufen/" + G[0], G[0], G[0], G[0], "Anrufen"];

function text(v) { return { nodeValue: v }; }
function el(tag, attrs, kinder) {
  const e = { tag: tag, attrs: Object.assign({}, attrs), kinder: kinder || [], hidden: false, style: {}, isConnected: true, _h: {} };
  e.getAttribute = k => (k in e.attrs ? e.attrs[k] : null);
  e.setAttribute = (k, v) => { e.attrs[k] = String(v); };
  e.addEventListener = (t, f) => { e._h[t] = f; };
  e.getBoundingClientRect = () => ({ top: 0, bottom: 0, height: 0 });
  return e;
}
function texte(e) { return e.kinder.reduce((l, k) => l.concat(k.tag ? texte(k) : [k]), []); }
/* Versteht Tag und Attribut-Wähler ([a], [a="w"], [a^="w"]), mehrere durch Komma. Klassen und Nachfahren kennt
   das Modell nicht: solche Wähler treffen nichts (FREI_HALTEN, .callbar). */
function passt(e, sel) {
  sel = sel.trim();
  if (/[ .#>:]/.test(sel.replace(/\[[^\]]*\]/g, ""))) return false;
  const m = sel.match(/^([a-z]*)((?:\[[^\]]+\])*)$/i);
  if (!m || (m[1] && m[1] !== e.tag)) return false;
  return (m[2].match(/\[[^\]]+\]/g) || []).every(a => {
    const t = a.slice(1, -1).match(/^([\w-]+)(?:(\^?=)"([^"]*)")?$/);
    if (!t) return false;
    const v = e.getAttribute(t[1]);
    if (v === null) return false;
    return !t[2] ? true : (t[2] === "=" ? v === t[3] : v.indexOf(t[3]) === 0);
  });
}

/* Eine Welt ist ein Dokument (ein Tab, ein Aufruf). speicher und kekse können zwei Welten teilen. */
function welt(opt) {
  const pc = { href: ECHT_TEL, "data-messung": "phone_click" };
  const klar1 = el("span", { "data-echte-nummer": "" }, [text("(international +49 2161 6225768)")]);
  const klar2 = el("span", { "data-echte-nummer": "" }, [text("(+49 2161 6225768)")]);
  const impressum = el("a", { href: ECHT_TEL }, [text(ECHT)]);
  const anrufLinks = opt.ohneLinks ? [] : [
    el("a", pc, [text(ECHT)]),
    el("a", pc, [el("span", {}, [text("Jetzt anrufen"), el("span", {}, [text(ECHT)])])]),
    el("a", pc, [text(ECHT)]),
    el("a", pc, [text(ECHT)]),
    el("a", pc, [text(ECHT)]),
    el("a", pc, [text("Anrufen")])];
  const alle = anrufLinks.concat(opt.ohneLinks ? [klar1, klar2] : [klar1, klar2, impressum]);
  const speicher = opt.speicher || {};
  if (opt.gespeichert !== undefined) speicher[SCHL] = JSON.stringify({ werbung: opt.gespeichert });
  /* Kekse mit der Domain, auf der sie gesetzt wurden; gelöscht wird nur mit derselben Domain-Angabe. */
  const kekse = opt.kekse || { _gcl_au: ".unfall-mg.de", _gac_UA1: "", _gcl_aw: ".www.unfall-mg.de", anderes: "" };
  const klick = [], nachId = {}, kopf = [], gemeldet = [], konsole = [], fenster = {}, neuladen = [];
  function neu(tag) {
    const e = el(tag, {}, []);
    e.remove = () => { if (e.id && nachId[e.id] === e) delete nachId[e.id]; e.isConnected = false; };
    return e;
  }
  const document = {
    readyState: "complete", documentElement: { classList: { contains: () => false } },
    addEventListener(t, f) { if (t === "click") klick.push(f); }, removeEventListener() {},
    dispatchEvent(ev) { gemeldet.push(ev.type); },
    createElement: neu,
    head: { appendChild(s) { kopf.push(s); s.parentNode = this; } },
    body: { appendChild(e) { if (e.id) { nachId[e.id] = e; nachId["kge-e-nein"] = neu("button"); nachId["kge-e-ja"] = neu("button"); } } },
    getElementById: id => nachId[id] || null,
    querySelector: () => null,
    querySelectorAll: sel => alle.filter(e => sel.split(",").some(s => passt(e, s))),
    createTreeWalker: wurzel => { const l = texte(wurzel); let i = 0; return { nextNode: () => l[i++] || null }; }
  };
  Object.defineProperty(document, "cookie", {
    get: () => Object.keys(kekse).map(k => k + "=1").join("; "),
    set: v => {
      const teile = v.split(";").map(s => s.trim());
      const name = teile[0].split("=")[0];
      const dom = (teile.find(s => /^domain=/i.test(s)) || "domain=").slice(7);
      if (/expires=Thu, 01 Jan 1970/.test(v)) { if (name in kekse && kekse[name] === dom) delete kekse[name]; }
      else kekse[name] = dom;
    }
  });
  const window = {
    KGE_KONFIG: opt.konfig, innerWidth: 390, innerHeight: 664,
    addEventListener(t, f) { (fenster[t] = fenster[t] || []).push(f); }, removeEventListener() {},
    location: { hostname: "www.unfall-mg.de", reload() { neuladen.push({ ziele: w.ziele(), gespeichert: speicher[SCHL] ? JSON.parse(speicher[SCHL]).werbung : null }); } }
  };
  const sb = {
    window: window, document: document, NodeFilter: { SHOW_TEXT: 4 },
    console: { info: s => konsole.push(String(s)), error() {} },
    Event: function (t) { this.type = t; },
    localStorage: { getItem: k => (k in speicher ? speicher[k] : null), setItem: (k, v) => { speicher[k] = String(v); }, removeItem: k => { delete speicher[k]; } },
    setTimeout: () => 0, clearTimeout() {}
  };
  const dl = () => (window.dataLayer || []).map(a => Array.prototype.slice.call(a));
  const w = {
    window: window, speicher: speicher, kekse: kekse, konsole: konsole, gemeldet: gemeldet, neuladen: neuladen,
    ziele: () => anrufLinks.map(l => l.getAttribute("href")),
    texte: () => anrufLinks.map(l => texte(l).map(t => t.nodeValue).join("/")),
    impressum: () => impressum.getAttribute("href") + "|" + texte(impressum).map(t => t.nodeValue).join("/"),
    klartextVerborgen: () => [klar1.hidden, klar2.hidden],
    klartext: () => [klar1.kinder[0].nodeValue, klar2.kinder[0].nodeValue],
    gespeichert: () => (speicher[SCHL] ? JSON.parse(speicher[SCHL]).werbung : null),
    configs: () => dl().filter(a => a[0] === "config").map(a => a[1] + (a[2].phone_conversion_callback ? " +callback" : "") + (a[2].phone_conversion_number ? " nr=" + a[2].phone_conversion_number : "")),
    callback: () => { const c = dl().filter(a => a[0] === "config" && a[2].phone_conversion_callback); return c.length ? c[c.length - 1][2].phone_conversion_callback : null; },
    consent: () => dl().filter(a => a[0] === "consent").map(a => a[1] + ":" + a[2].ad_storage),
    /* alle vier Werte je consent-Aufruf: ad_storage/ad_user_data/ad_personalization/analytics_storage */
    consentVoll: () => dl().filter(a => a[0] === "consent").map(a => a[1] + ":" + [a[2].ad_storage, a[2].ad_user_data, a[2].ad_personalization, a[2].analytics_storage].join("/")),
    personalisierung: () => dl().filter(a => a[0] === "config").map(a => a[2].allow_ad_personalization_signals),
    events: () => dl().filter(a => a[0] === "event").map(a => a[2].send_to),
    skripte: () => kopf.filter(s => s.src).map(s => s.src),
    dlLen: () => dl().length,
    verworfen: () => konsole.filter(s => s.indexOf("website_call verworfen") > -1).length,
    fusslink: () => klick.forEach(f => f({ target: { closest: s => (s.indexOf("einwilligung-oeffnen") > -1 ? {} : null) }, preventDefault() {} })),
    telKlick: () => klick.forEach(f => f({ target: { closest: s => (s === "[data-messung]" ? { getAttribute: () => "phone_click" } : null) }, preventDefault() {} })),
    ja: () => nachId["kge-e-ja"]._h.click(),
    nein: () => nachId["kge-e-nein"]._h.click(),
    bannerOffen: () => !!nachId["kge-einwilligung"] && !nachId["kge-einwilligung"].hidden,
    feuere: (typ, ev) => (fenster[typ] || []).forEach(f => f(ev))
  };
  vm.runInNewContext(QUELLE, sb, { filename: DATEI });
  return w;
}

const K = (wc, modus, platz) => ({
  googleTag: platz ? "AW-XXXXXXXXXX" : "AW-1234567890",
  labels: { phone_click: platz ? "XXXXXXXXXXXXXXXXXXX" : "LabKlick", whatsapp_click: "LabWa", form_submit: "LabForm", website_call: wc },
  einwilligungsModus: modus || "einfach", telefonAnzeige: ECHT
});
const CONFIG_GRUND = "AW-1234567890", CONFIG_ANRUF = "AW-1234567890/LabAnruf +callback nr=" + ECHT;
const GTAG = "https://www.googletagmanager.com/gtag/js?id=AW-1234567890";

let rot = 0, gezaehlt = 0;
function pruefe(name, ist, soll) {
  const a = JSON.stringify(ist), b = JSON.stringify(soll);
  gezaehlt++;
  if (a === b) { console.log("ok   " + name); return; }
  rot++;
  console.log("ROT  " + name + "\n       ist:  " + a + "\n       soll: " + b);
}
function fall(name, f) {
  try { f(); } catch (e) { rot++; gezaehlt++; console.log("ROT  " + name + ": Ausnahme " + (e && e.message)); }
}
const getauscht = konfig => { const w = welt({ konfig: konfig || K("LabAnruf"), gespeichert: true }); w.callback()(G[0], G[1]); return w; };

fall("A/B/C Laden, Tausch, Widerruf im selben Tab", () => {
  const w = welt({ konfig: K("LabAnruf"), gespeichert: true });
  pruefe("A1 Laden mit gespeicherter Einwilligung: consent-Folge", w.consent(), ["default:denied", "update:granted"]);
  pruefe("A1 zwei configs, das zweite mit Label, Nummer und Callback", w.configs(), [CONFIG_GRUND, CONFIG_ANRUF]);
  pruefe("A1 consent vollständig: default alles denied, Erlauben gibt nur ad_storage und ad_user_data frei", w.consentVoll(), ["default:denied/denied/denied/denied", "update:granted/granted/denied/denied"]);
  pruefe("A1 beide configs tragen allow_ad_personalization_signals false", w.personalisierung(), [false, false]);
  pruefe("A1 genau ein Google-Skript", w.skripte(), [GTAG]);
  pruefe("A1 vor dem Callback alles echt", [w.ziele(), w.texte(), w.klartextVerborgen()], [ZIELE_ECHT, TEXTE_ECHT, [false, false]]);
  w.callback()(G[0], G[1]);
  pruefe("A2 Callback: alle 6 Ziele getauscht", w.ziele(), ZIELE_G);
  pruefe("A2 Callback: Text je Link getauscht, auch verschachtelt; „Anrufen“ bleibt", w.texte(), TEXTE_G);
  pruefe("A2 Fund 4: Impressum-Link (ohne data-messung) bleibt die echte Nummer", w.impressum(), ECHT_TEL + "|" + ECHT);
  pruefe("A2 Fund 5: Klartext neben getauschten Links ausgeblendet", w.klartextVerborgen(), [true, true]);
  pruefe("A2 Fund 5: Klartext selbst unverändert (nur ausgeblendet)", w.klartext(), ["(international +49 2161 6225768)", "(+49 2161 6225768)"]);
  w.callback()("02161 999 99 99", "+4921619999999");
  pruefe("A3 zweiter Callback mit anderer Nummer: ohne Wirkung", [w.ziele(), w.texte()], [ZIELE_G, TEXTE_G]);
  w.telKlick();
  pruefe("A4 Klick auf getauschten Link sendet phone_click", w.events(), ["AW-1234567890/LabKlick"]);
  w.fusslink();
  pruefe("B1 Fußlink offen, unentschieden: Banner da, Nummer bleibt getauscht", [w.bannerOffen(), w.ziele()], [true, ZIELE_G]);
  pruefe("B1 Fußlink ändert den Speicher nicht (erst die Wahl)", [w.gespeichert(), w.neuladen.length], [true, 0]);
  w.nein();
  pruefe("B2 Ablehnen: Ziele, Texte und Klartext wieder echt", [w.ziele(), w.texte(), w.klartextVerborgen()], [ZIELE_ECHT, TEXTE_ECHT, [false, false]]);
  pruefe("B2 Ablehnen: letzter consent setzt alle vier Werte auf denied, gespeichert werbung false", [w.consentVoll().slice(-1)[0], w.gespeichert()], ["update:denied/denied/denied/denied", false]);
  pruefe("B2 Ablehnen: _gcl_ und _gac_ auf Host und Elterndomains gelöscht, Fremdes bleibt", Object.keys(w.kekse), ["anderes"]);
  pruefe("B2 Ablehnen: genau ein Neuladen, davor echte Nummer und gespeicherte Ablehnung", w.neuladen, [{ ziele: ZIELE_ECHT, gespeichert: false }]);
  pruefe("B2 Ablehnen meldet kge-banner an leiste.js", w.gemeldet.filter(t => t === "kge-banner").length >= 2, true);
  w.callback()(G[0], G[1]);
  pruefe("C  später Callback nach Widerruf (vor dem Neuladen): bleibt echt", [w.ziele(), w.texte(), w.klartextVerborgen()], [ZIELE_ECHT, TEXTE_ECHT, [false, false]]);
  w.telKlick();
  pruefe("C2 Klick nach Widerruf sendet nichts mehr", w.events().length, 1);
  /* Das neu geladene Dokument: gleiche Speicher, frisches DOM. */
  const n = welt({ konfig: K("LabAnruf"), speicher: w.speicher, kekse: w.kekse });
  pruefe("D2 nach dem Neuladen: nichts von Google, echte Nummer, kein Banner", [n.dlLen(), n.skripte(), n.ziele(), n.bannerOffen()], [0, [], ZIELE_ECHT, false]);
  n.fusslink(); n.ja();
  pruefe("D2 erneut Erlauben im neuen Dokument: voller Weg mit Callback", [n.configs(), n.skripte(), n.gespeichert()], [[CONFIG_GRUND, CONFIG_ANRUF], [GTAG], true]);
  n.callback()(G[0], G[1]);
  pruefe("D2 Google ruft neu auf: Tausch greift wieder", [n.ziele(), n.klartextVerborgen()], [ZIELE_G, [true, true]]);
});

fall("E Erstbesuch", () => {
  let w = welt({ konfig: K("LabAnruf") });
  pruefe("E1 Erstbesuch vor der Entscheidung: nichts von Google", [w.dlLen(), w.skripte()], [0, []]);
  w.ja();
  pruefe("E2 Erlauben: zwei configs, ein Skript, gespeichert true", [w.configs(), w.skripte(), w.gespeichert()], [[CONFIG_GRUND, CONFIG_ANRUF], [GTAG], true]);
  w = welt({ konfig: K("LabAnruf") }); w.nein();
  pruefe("E3 Ablehnen als Erstwahl: nichts von Google, kein Neuladen", [w.dlLen(), w.skripte(), w.neuladen.length, w.gespeichert()], [0, [], 0, false]);
  pruefe("E3 Ablehnen räumt alte Google-Cookies auch ohne Ja in diesem Aufruf", Object.keys(w.kekse), ["anderes"]);
  w = welt({ konfig: K("LabAnruf"), gespeichert: false });
  pruefe("E4 Laden mit gespeicherter Ablehnung: nichts von Google, kein Banner", [w.dlLen(), w.skripte(), w.bannerOffen()], [0, [], false]);
});

fall("F Konfiguration", () => {
  let w = welt({ konfig: K(""), gespeichert: true });
  pruefe("F1 website_call leer: ein config ohne Nummer, keine Konsolenzeile", [w.configs(), w.verworfen()], [[CONFIG_GRUND], 0]);
  pruefe("F1 website_call leer: das eine config trägt allow_ad_personalization_signals false", w.personalisierung(), [false]);
  pruefe("F1 website_call leer: kein Callback, Seite echt", [w.callback(), w.ziele()], [null, ZIELE_ECHT]);
  w = welt({ konfig: K("XXXXXXXXXXXXXXXXXXX"), gespeichert: true });
  pruefe("F2 Fund 7: Platzhalter im Label: ein config, Konsolenzeile „verworfen“", [w.configs(), w.verworfen()], [[CONFIG_GRUND], 1]);
  w = welt({ konfig: K("Lab Anruf/x"), gespeichert: true });
  pruefe("F2 Fund 7: Label mit unzulässigen Zeichen: ein config, Konsolenzeile", [w.configs(), w.verworfen()], [[CONFIG_GRUND], 1]);
  w = welt({ konfig: K("LabAnruf", "einfach", true), gespeichert: true });
  pruefe("F3 Platzhalter-Konfiguration: nichts von Google", [w.dlLen(), w.skripte()], [0, []]);
  const ohne = K("LabAnruf"); delete ohne.telefonAnzeige;
  w = welt({ konfig: ohne, gespeichert: true });
  pruefe("F4 telefonAnzeige fehlt: ein config, Konsolenzeile", [w.configs(), w.verworfen()], [[CONFIG_GRUND], 1]);
  w = welt({ konfig: K("Lab-Anruf_1"), gespeichert: true });
  pruefe("F5 Label mit Bindestrich und Unterstrich gilt", w.configs().length, 2);
});

fall("G Seite ohne Telefon-Link", () => {
  const w = welt({ konfig: K("LabAnruf"), gespeichert: true, ohneLinks: true });
  w.callback()(G[0], G[1]);
  pruefe("G  Seite ohne Telefon-Link: Callback ohne Fehler, Klartext bleibt sichtbar", w.klartextVerborgen(), [false, false]);
});

fall("H/D Modus erweitert (verboten, Code bleibt)", () => {
  const w = welt({ konfig: K("LabAnruf", "erweitert") });
  pruefe("H1 erweitert ohne Entscheidung: configs hängen, consent nur default denied", [w.configs(), w.consent()], [[CONFIG_GRUND, CONFIG_ANRUF], ["default:denied"]]);
  w.callback()(G[0], G[1]);
  pruefe("H2 erweitert: Callback ohne Einwilligung tauscht nicht", [w.ziele(), w.texte(), w.klartextVerborgen()], [ZIELE_ECHT, TEXTE_ECHT, [false, false]]);
  w.ja();
  pruefe("H3 Fund 12: danach Erlauben zeigt die schon gelieferte Nummer", [w.ziele(), w.texte(), w.configs().length], [ZIELE_G, TEXTE_G, 2]);
  w.fusslink(); w.nein();
  pruefe("D1 erweitert: Ablehnen stellt zurück, ohne Neuladen", [w.ziele(), w.klartextVerborgen(), w.neuladen.length], [ZIELE_ECHT, [false, false], 0]);
  w.callback()("02161 333 44 55", "+4921613334455");
  pruefe("D1 Lieferung während der Ablehnung tauscht nicht", w.ziele(), ZIELE_ECHT);
  w.fusslink(); w.ja();
  pruefe("D1 Fund 6: erneut Erlauben ohne Neuladen bringt die zuletzt gelieferte Nummer", [w.ziele()[0], w.texte()[0], w.klartextVerborgen(), w.configs().length, w.skripte().length], ["tel:+4921613334455", "02161 333 44 55", [true, true], 2, 1]);
});

fall("I Unbrauchbare Aufrufe", () => {
  const echt = w => [w.ziele(), w.texte(), w.klartextVerborgen()];
  const SOLL = [ZIELE_ECHT, TEXTE_ECHT, [false, false]];
  let w = welt({ konfig: K("LabAnruf"), gespeichert: true });
  w.callback()("", G[1]); pruefe("I1 Callback ohne formatierte Nummer: kein Tausch", echt(w), SOLL);
  w.callback()(G[0], undefined); pruefe("I2 Callback ohne mobile Nummer: kein Tausch", echt(w), SOLL);
  w.callback()(G[0], "abc"); pruefe("I4 Fund 10: mobile Nummer ohne Ziffern: weder Text noch Ziel", echt(w), SOLL);
  w.callback()("abc", G[1]); pruefe("I5 Fund 10: Anzeige ohne Ziffern: weder Text noch Ziel", echt(w), SOLL);
  w.callback()(G[0], "+49 21"); pruefe("I6 Fund 10: zu wenige Ziffern im Ziel: kein Tausch", echt(w), SOLL);
  w.callback()(G[0], "tel:+49 (2161) 000-11 22");
  pruefe("I3 mobile Nummer mit tel: und Sonderzeichen: Ziel sauber", [w.ziele()[0], w.texte()[0]], [G_ZIEL, G[0]]);
  w = welt({ konfig: K("LabAnruf"), gespeichert: true });
  w.callback()("0800 123 4567", "08001234567");
  pruefe("I7 Nummer ohne Pluszeichen: Ziel ohne Plus", w.ziele()[0], "tel:08001234567");
});

fall("T Zweiter Tab", () => {
  const speicher = {}, kekse = { _gcl_au: ".unfall-mg.de", anderes: "" };
  speicher[SCHL] = JSON.stringify({ werbung: true });
  const t1 = welt({ konfig: K("LabAnruf"), speicher: speicher, kekse: kekse });
  const t2 = welt({ konfig: K("LabAnruf"), speicher: speicher, kekse: kekse });
  t1.callback()(G[0], G[1]); t2.callback()(G[0], G[1]);
  /* T2 feuert bei gespeicherter Ablehnung: Nur so kann der Fall den Schlüsselfilter widerlegen (bei gespeicherter
     Erlaubnis täte pruefeGespeichert auch ohne Filter nichts). */
  const t5 = getauscht();
  t5.speicher[SCHL] = JSON.stringify({ werbung: false });
  t5.feuere("storage", { key: "anderer-schluessel" });
  pruefe("T2 storage-Ereignis zu fremdem Schlüssel bei gespeicherter Ablehnung: nichts (Schlüsselfilter)", [t5.ziele(), t5.neuladen.length], [ZIELE_G, 0]);
  t5.feuere("storage", { key: SCHL });
  pruefe("T2 dasselbe Dokument, Ereignis zum eigenen Schlüssel: Widerruf", [t5.ziele(), t5.neuladen.length], [ZIELE_ECHT, 1]);
  t2.feuere("storage", { key: SCHL });
  pruefe("T3 storage-Ereignis, gespeichert weiter werbung true: nichts", [t2.ziele(), t2.neuladen.length], [ZIELE_G, 0]);
  t1.fusslink(); t1.nein();
  pruefe("T1 Tab 1 widerruft: Tab 2 noch unberührt, bis das Ereignis kommt", t2.ziele(), ZIELE_G);
  t2.feuere("storage", { key: SCHL });
  pruefe("T1 Tab 2 erfährt den Widerruf: echte Nummer, Klartext da", [t2.ziele(), t2.texte(), t2.klartextVerborgen()], [ZIELE_ECHT, TEXTE_ECHT, [false, false]]);
  pruefe("T1 Tab 2: consent denied, ein Neuladen mit echter Nummer", [t2.consent().slice(-1)[0], t2.neuladen], ["update:denied", [{ ziele: ZIELE_ECHT, gespeichert: false }]]);
  delete speicher[SCHL];
  const t3 = getauscht();
  t3.speicher[SCHL] = undefined; delete t3.speicher[SCHL];
  t3.feuere("storage", { key: SCHL });
  pruefe("T4 leerer Speicher ist kein Widerruf", [t3.ziele(), t3.neuladen.length], [ZIELE_G, 0]);
});

fall("Z Zurück-Taste", () => {
  let w = getauscht();
  w.feuere("pageshow", { persisted: true });
  pruefe("Z3 pageshow aus dem Zurück-Speicher, weiter erlaubt: bleibt getauscht", [w.ziele(), w.neuladen.length], [ZIELE_G, 0]);
  w.speicher[SCHL] = JSON.stringify({ werbung: false });  /* Widerruf auf der Folgeseite */
  w.feuere("pageshow", { persisted: false });
  pruefe("Z2 pageshow ohne Zurück-Speicher: nichts", [w.ziele(), w.neuladen.length], [ZIELE_G, 0]);
  w.feuere("pageshow", { persisted: true });
  pruefe("Z1 Zurück-Taste nach Widerruf: echte Nummer, Klartext da, Neuladen", [w.ziele(), w.texte(), w.klartextVerborgen(), w.neuladen.length], [ZIELE_ECHT, TEXTE_ECHT, [false, false], 1]);
});

/* S1 ist eine Textsuche, keine Funktionsprüfung: Das Mini-DOM kennt keine Klassen und keine Zeit, verdecktHero,
   kante und zeigeSpaeter laufen hier nie mit Wirkung. Ob Banner und Anrufleiste zusammenspielen, zeigt nur der Browser. */
fall("S Textmerkmale des mobilen Umbaus", () => {
  const teile = ["FREI_HALTEN", "kge-leiste", "kge-banner", "translateY(calc(-1 * var(--leiste-unten", "#kge-einwilligung[hidden]{display:block;visibility:hidden}"];
  pruefe("S1 Textsuche: fünf Zeichenketten des mobilen Umbaus stehen im Quelltext (keine Funktionsprüfung)", teile.filter(t => QUELLE.indexOf(t) === -1), []);
});

console.log((rot ? "ROT: " + rot + " von " : "GRÜN: ") + gezaehlt + " Prüfungen" + (rot ? " weichen ab" : " stimmen") + " · " + DATEI);
process.exit(rot ? 1 : 0);
