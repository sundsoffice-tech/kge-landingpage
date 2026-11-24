/* Zeuge für formular.js (Runde 7, Punkt 3): das Skript läuft je Fall in einem frischen Kontext mit nachgebautem DOM,
 * eigenem fetch, eigener Uhr und wahlweise ohne AbortController. Je Fall wird festgehalten, was im Status steht, ob
 * der Knopf frei ist, ob der Anrufsatz sichtbar ist und ob ein zweiter Versand möglich ist.
 *
 * Aufruf: node pruefen/zeuge-formular.js            (Exit 0 grün, 1 rot)
 * Als Modul: require("./zeuge-formular.js").pruefe(quelltext) liefert die roten Zeilen (für rotprobe-formular.js).
 * Vorlage: Programmierer-Prüfung von d255384 (werkzeug/formular_dom.js).
 */
"use strict";
const vm = require("vm");
const fs = require("fs");
const path = require("path");

const NUMMER = "02161 688 86 91";
const TEL_LINK = "tel:+4921616888691";
const KNOPF = "Rückruf anfordern";
const ERFOLG = "Danke. Erfolg.";
const FEHLER = "Das hat leider nicht geklappt. Bitte rufen Sie direkt an: " + NUMMER;
const UNKLAR = "Wir konnten den Eingang nicht bestätigen. Bitte rufen Sie an: " + NUMMER;

function el(tag, attrs) {
  return {
    tagName: tag, attrs: Object.assign({}, attrs || {}), kinder: [], textContent: "", value: "", className: "",
    disabled: false, checked: false, hidden: false, h: {},
    getAttribute(n) { return n in this.attrs ? this.attrs[n] : null; },
    setAttribute(n, v) { this.attrs[n] = String(v); },
    removeAttribute(n) { delete this.attrs[n]; },
    addEventListener(t, f) { this.h[t] = f; },
    appendChild(k) { this.kinder.push(k); this.textContent += k.textContent; },
    focus() {},
  };
}

function aufgeschoben() {
  const d = {};
  d.promise = new Promise((ja, nein) => { d.resolve = ja; d.reject = nein; });
  return d;
}

function antwort(httpOk, daten) {
  return { ok: httpOk, status: httpOk ? 200 : 500,
    json: () => (daten instanceof Error ? Promise.reject(daten) : Promise.resolve(daten)) };
}

let abgelehnt = 0;
process.on("unhandledRejection", () => { abgelehnt += 1; });

// Baut DOM und Umgebung, lädt das Skript und gibt die Bedienung für einen Fall zurück.
function lade(quelle, opt) {
  opt = opt || {};
  const knopf = el("button"); knopf.textContent = KNOPF; knopf.disabled = true; // Markup: disabled
  const satz = el("p", { "data-ohne-skript": "" }); // Markup: sichtbar
  const tel = el("input"), nm = el("input"), tx = el("textarea"), honig = el("input"), status = el("p");
  const form = el("form", { "data-erfolg": ERFOLG });
  const felder = { "button[type=submit]": knopf, "#f-tel": opt.ohneTelefonfeld ? null : tel, "#f-name": nm,
    "#f-text": tx, "#f-website": honig, "[data-ohne-skript]": satz };
  form.querySelector = (s) => (s in felder ? felder[s] : null);
  form.querySelectorAll = () => [tel, nm, tx];
  const uhren = [], aufrufe = [], gemessen = [];
  let abgebrochen = false;
  const win = { KGE_KONFIG: "konfig" in opt ? opt.konfig : { telefonAnzeige: NUMMER } };
  win.kgeMessung = opt.messungWirft ? () => { throw new Error("gtag weg"); } : (x) => gemessen.push(x);
  class AC {
    constructor() { this.signal = { l: [] }; }
    abort() { abgebrochen = true; this.signal.l.forEach((f) => f()); }
  }
  const ctx = {
    window: win, location: { pathname: "/" }, console: { error() {} },
    document: { getElementById: (i) => (i === "rueckruf-formular" ? form : i === "f-status" ? status : null),
      createElement: (t) => el(t) },
    setTimeout: (f, ms) => { uhren.push({ f, ms }); return uhren.length; },
    clearTimeout: (i) => { if (uhren[i - 1]) uhren[i - 1].weg = true; },
    AbortController: opt.ohneAbort ? undefined : AC,
    fetch: (u, o) => {
      const d = aufgeschoben();
      aufrufe.push(d);
      if (o && o.signal) o.signal.l.push(() => d.reject(Object.assign(new Error("abgebrochen"), { name: "AbortError" })));
      return d.promise;
    },
  };
  let ladefehler = null;
  try { vm.runInNewContext(quelle, ctx); } catch (e) { ladefehler = e.message; }
  const h = {
    ladefehler,
    klick(nummer) {
      if (!form.h.submit) return false;
      // Absichtlich auch bei gesperrtem Knopf: der Handler selbst muss einen zweiten Versand verweigern (Absenden per
      // Skript oder Eingabetaste darf nicht an der Sperre des Knopfs allein hängen).
      tel.value = nummer === undefined ? "0177 1234567" : nummer;
      form.h.submit({ preventDefault() {} });
      return true;
    },
    uhr() { uhren.forEach((u) => { if (!u.weg) { u.weg = true; u.f(); } }); },
    antworte(i, a) { aufrufe[i].resolve(a); },
    scheitere(i, e) { aufrufe[i].reject(e); },
    async ruhe() { for (let i = 0; i < 20; i++) await new Promise((r) => setImmediate(r)); },
    stand() {
      return { status: status.textContent, klasse: status.className, knopf: knopf.textContent, frei: !knopf.disabled,
        satzSichtbar: !satz.hidden, aufrufe: aufrufe.length, gemessen: gemessen.join(","),
        telLink: (status.kinder[0] || {}).href || "", telWert: tel.value, abgebrochen,
        zeitgrenze: uhren.length ? uhren[0].ms : null, uhrGeloescht: uhren.length ? !!uhren[0].weg : null };
    },
  };
  return h;
}

// Je Fall: Ablauf und erwartete Werte. Ein Fall ist rot, wenn ein Wert abweicht oder eine Ablehnung unbehandelt blieb.
const FAELLE = [
  ["L1", "Laden: Knopf frei, Anrufsatz aus, Handler da", async (q) => {
    const h = lade(q);
    return [h, { ladefehler: null, frei: true, satzSichtbar: false, status: "" }];
  }],
  ["L2", "Ladefehler vor dem Handler (kein Telefonfeld): Knopf gesperrt, Anrufsatz sichtbar", async (q) => {
    const h = lade(q, { ohneTelefonfeld: true });
    return [h, { ladefehlerDa: true, frei: false, satzSichtbar: true, klickGeht: false }];
  }],
  ["L3", "Rufnummer in konfig.js keine Zeichenkette: lädt, Link stimmt", async (q) => {
    const h = lade(q, { konfig: { telefonAnzeige: 21616888691 } });
    h.klick(); h.antworte(0, antwort(false, { ok: false })); await h.ruhe();
    // Die Zahl wird als Text übernommen (ohne führende 0); entscheidend ist: kein Ladefehler, Knopf frei, Nummer im Hinweis.
    return [h, { ladefehler: null, frei: true, status: "Das hat leider nicht geklappt. Bitte rufen Sie direkt an: 21616888691" }];
  }],
  ["L4", "konfig.js fehlt: Rückfallwerte, Erfolg", async (q) => {
    const h = lade(q, { konfig: undefined });
    h.klick(); h.antworte(0, antwort(true, { ok: true })); await h.ruhe();
    return [h, { ladefehler: null, status: ERFOLG }];
  }],
  ["V1", "ungültige Nummer: Hinweis, kein Versand", async (q) => {
    const h = lade(q); h.klick("12"); await h.ruhe();
    return [h, { aufrufe: 0, frei: true, klasse: "status fehler",
      status: "Bitte geben Sie eine Telefonnummer an, unter der Sie erreichbar sind." }];
  }],
  ["A1", "Erfolg: Erfolgstext, Knopf gesperrt, Messung, kein zweiter Versand", async (q) => {
    const h = lade(q); h.klick();
    const unterwegs = h.stand();
    h.antworte(0, antwort(true, { ok: true })); await h.ruhe();
    const geleert = h.stand().telWert === "";
    h.klick(); await h.ruhe();
    return [h, { status: ERFOLG, klasse: "status ok", knopf: "Anfrage eingegangen", frei: false, gemessen: "form_submit",
      aufrufe: 1, zeitgrenze: 15000, uhrGeloescht: true, geleert,
      unterwegs: unterwegs.knopf === "Wird gesendet …" && !unterwegs.frei }];
  }],
  ["A2", "Messfunktion wirft: Erfolgstext bleibt", async (q) => {
    const h = lade(q, { messungWirft: true }); h.klick();
    h.antworte(0, antwort(true, { ok: true })); await h.ruhe();
    return [h, { status: ERFOLG, klasse: "status ok", frei: false }];
  }],
  ["B1", "Serverfehler 500 mit JSON: Fehlertext mit Nummer, Knopf frei, zweiter Versand möglich", async (q) => {
    const h = lade(q); h.klick();
    h.antworte(0, antwort(false, { ok: false, fehler: "x" })); await h.ruhe();
    const zwischen = h.stand(); h.klick();
    return [h, { status: "Einen Moment …", knopf: "Wird gesendet …", frei: false, aufrufe: 2,
      vorher: zwischen.frei && zwischen.status === FEHLER && zwischen.klasse === "status fehler"
        && zwischen.telLink === TEL_LINK && zwischen.knopf === KNOPF && zwischen.telWert === "0177 1234567" }];
  }],
  ["B2", "Serverfehler 500 ohne lesbares JSON: sicher gescheitert", async (q) => {
    const h = lade(q); h.klick(); h.antworte(0, antwort(false, new Error("kein JSON"))); await h.ruhe();
    return [h, { status: FEHLER, frei: true, knopf: KNOPF }];
  }],
  ["B3", "200 mit lesbarem JSON ohne ok:true (ok: \"true\"): sicher gescheitert", async (q) => {
    const h = lade(q); h.klick(); h.antworte(0, antwort(true, { ok: "true" })); await h.ruhe();
    return [h, { status: FEHLER, frei: true, gemessen: "" }];
  }],
  ["C1", "200 mit unlesbarem JSON: unklar, Knopf gesperrt mit Text, Eingaben bleiben, kein zweiter Versand", async (q) => {
    const h = lade(q); h.klick(); h.antworte(0, antwort(true, new Error("kein JSON"))); await h.ruhe(); h.klick();
    return [h, { status: UNKLAR, klasse: "status fehler", telLink: TEL_LINK, knopf: KNOPF, frei: false,
      telWert: "0177 1234567", aufrufe: 1, gemessen: "" }];
  }],
  ["C2", "Netzfehler beim Versand: unklar", async (q) => {
    const h = lade(q); h.klick(); h.scheitere(0, new TypeError("Failed to fetch")); await h.ruhe(); h.klick();
    return [h, { status: UNKLAR, frei: false, knopf: KNOPF, aufrufe: 1, uhrGeloescht: true }];
  }],
  ["Z1", "Zeitgrenze mit AbortController: der Zeitgeber meldet unklar sofort, Versand abgebrochen", async (q) => {
    const h = lade(q); h.klick(); h.uhr();
    const sofort = h.stand(); await h.ruhe(); h.klick();
    return [h, { status: UNKLAR, frei: false, knopf: KNOPF, abgebrochen: true, aufrufe: 1,
      sofort: sofort.status === UNKLAR && !sofort.frei }];
  }],
  ["Z2", "Zeitgrenze ohne AbortController: unklar statt Hängen, späte Erfolgsantwort zählt", async (q) => {
    const h = lade(q, { ohneAbort: true }); h.klick(); h.uhr(); await h.ruhe();
    const zwischen = h.stand();
    h.antworte(0, antwort(true, { ok: true })); await h.ruhe();
    return [h, { status: ERFOLG, gemessen: "form_submit", frei: false,
      zwischen: zwischen.status === UNKLAR && !zwischen.frei && zwischen.knopf === KNOPF }];
  }],
  ["Z3", "Zeitgrenze ohne AbortController, späte Fehlantwort: bleibt unklar, Knopf gesperrt", async (q) => {
    const h = lade(q, { ohneAbort: true }); h.klick(); h.uhr(); await h.ruhe();
    h.antworte(0, antwort(false, { ok: false })); await h.ruhe(); h.klick();
    return [h, { status: UNKLAR, frei: false, aufrufe: 1 }];
  }],
];

async function pruefe(quelle) {
  const rot = [];
  for (const [id, titel, ablauf] of FAELLE) {
    const vorher = abgelehnt;
    let h, soll;
    try {
      [h, soll] = await ablauf(quelle);
      await new Promise((r) => setImmediate(r));
    } catch (e) {
      rot.push(`${id} ${titel} · Ausnahme im Ablauf: ${e.message}`);
      continue;
    }
    const ist = Object.assign(h.stand(), { ladefehler: h.ladefehler, ladefehlerDa: !!h.ladefehler });
    if ("klickGeht" in soll) ist.klickGeht = h.klick();
    const abw = [];
    for (const k of Object.keys(soll)) {
      if (["unterwegs", "vorher", "sofort", "zwischen", "geleert"].includes(k)) {
        if (soll[k] !== true) abw.push(`${k}: Zwischenstand falsch`);
      } else if (ist[k] !== soll[k]) {
        abw.push(`${k}: ${JSON.stringify(ist[k])} statt ${JSON.stringify(soll[k])}`);
      }
    }
    if (abgelehnt !== vorher) abw.push("unbehandelte Ablehnung");
    if (abw.length) rot.push(`${id} ${titel} · ${abw.join("; ")}`);
  }
  return rot;
}

module.exports = { pruefe, FAELLE };

if (require.main === module) {
  const quelle = fs.readFileSync(path.join(__dirname, "..", "formular.js"), "utf8");
  pruefe(quelle).then((rot) => {
    const ids = new Set(rot.map((z) => z.split(" ")[0]));
    for (const [id, titel] of FAELLE) console.log(`${ids.has(id) ? "ROT" : "ok "}  ${id} ${titel}`);
    rot.forEach((z) => console.log("     " + z));
    console.log(rot.length ? `ROT: ${ids.size} von ${FAELLE.length} weichen ab` : `GRÜN: ${FAELLE.length} Fälle stimmen`);
    process.exit(rot.length ? 1 : 0);
  });
}
