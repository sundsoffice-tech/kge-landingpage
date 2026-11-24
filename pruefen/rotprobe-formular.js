/* Rotprobe zu zeuge-formular.js (Runde 7, Punkt 3): je Mutation wird der Quelltext von formular.js im Speicher
 * verändert und der Zeuge darauf angesetzt. Bestanden ist eine Mutation nur, wenn der benannte Fall rot wird.
 *
 * Aufruf: node pruefen/rotprobe-formular.js   (Exit 0 bestanden, 1 nicht)
 */
"use strict";
const fs = require("fs");
const path = require("path");
const { pruefe } = require("./zeuge-formular.js");

const QUELLE = fs.readFileSync(path.join(__dirname, "..", "formular.js"), "utf8");

// [Name, erwarteter Fall, alt, neu]; alt muss genau einmal im Quelltext stehen.
const MUTATIONEN = [
  ["M1 unklar gibt den Knopf frei", "C1",
    "zustand = \"unklar\";\n    knopf.disabled = true;", "zustand = \"unklar\";\n    knopf.disabled = false;"],
  ["M2 der Zeitgeber meldet nicht", "Z1",
    "      unklar(\"Zeitgrenze \" + ZEITGRENZE_MS + \" ms\");\n", ""],
  ["M3 Freischaltung vor dem Handler", "L2",
    "  var ERFOLG = form.getAttribute", "  knopf.disabled = false;\n  var ERFOLG = form.getAttribute"],
  ["M4 späte Fehlantwort überschreibt unklar", "Z2",
    "  function gescheitert(grund) {\n    if (zustand !== \"sendet\") return;",
    "  function gescheitert(grund) {\n    if (zustand === \"erfolg\") return;"],
  ["M5 Erfolg ohne ok === true", "B3", "a.daten && a.daten.ok === true", "a.daten && a.daten.ok"],
  ["M6 2xx mit unlesbarem JSON gilt als gescheitert", "C1",
    "else unklar(\"HTTP \"", "else gescheitert(\"HTTP \""],
  ["M7 Netzfehler gilt als gescheitert", "C2",
    "      clearTimeout(uhr);\n      unklar(fehler);", "      clearTimeout(uhr);\n      gescheitert(fehler);"],
  ["M8 Zeitgrenze 30 s statt 15 s", "A1", "var ZEITGRENZE_MS = 15000;", "var ZEITGRENZE_MS = 30000;"],
  ["M9 Anrufsatz bleibt nach dem Laden sichtbar", "L1", "  if (ohneSkript) ohneSkript.hidden = true;\n", ""],
  ["M10 zweiter Versand nach unklar möglich", "C2",
    "    if (zustand !== \"offen\") return;\n", "    if (zustand === \"sendet\" || zustand === \"erfolg\") return;\n"],
  ["M11 Messung ohne eigenen try (wirft in den Ausgang)", "A2",
    "    try {\n      if (typeof window.kgeMessung === \"function\") window.kgeMessung(\"form_submit\");\n    } catch (fehler) {\n"
    + "      console.error(\"[Rueckruf] Messung fehlgeschlagen, Anfrage ist angekommen:\", fehler);\n    }\n",
    "    if (typeof window.kgeMessung === \"function\") window.kgeMessung(\"form_submit\");\n"],
  ["M12 Erfolg hält den Zustand nicht fest (zweiter Versand möglich)", "A1",
    "    zustand = \"erfolg\";\n", "    zustand = \"offen\";\n"],
  // Runde 8
  ["M13 Status ab 500 mit JSON wieder sicher gescheitert", "B1",
    "else if (a.lesbar && a.r.status < 500) gescheitert(", "else if (a.lesbar) gescheitert("],
  ["M14 alte Regel: jeder Nicht-2xx gescheitert, auch ohne JSON", "B2",
    "else if (a.lesbar && a.r.status < 500) gescheitert(", "else if (!a.r.ok || a.lesbar) gescheitert("],
  ["M15 späte Erfolgsantwort nach der Zeitgrenze wird verworfen", "Z1",
    "    if (zustand !== \"sendet\" && zustand !== \"unklar\") return;\n    zustand = \"erfolg\";",
    "    if (zustand !== \"sendet\") return;\n    zustand = \"erfolg\";"],
  ["M16 der Zeitgeber bricht den Versand wieder ab", "Z1",
    "      method: \"POST\",\n", "      method: \"POST\",\n"
    + "      signal: (function (c) { setTimeout(function () { c.abort(); }, ZEITGRENZE_MS); "
    + "return c.signal; })(new AbortController()),\n"],
  ["M17 Rufnummer ohne Typprüfung (Zahl ergibt falschen Link)", "L3",
    "typeof konfig.telefonAnzeige === \"string\" && konfig.telefonAnzeige ? konfig.telefonAnzeige\n    : \"02161 688 86 91\"",
    "String(konfig.telefonAnzeige || \"02161 688 86 91\")"],
];

(async () => {
  const stand = await pruefe(QUELLE);
  if (stand.length) {
    console.log("ABBRUCH: Der Zeuge ist schon ohne Mutation rot.\n" + stand.join("\n"));
    process.exit(1);
  }
  let rot = 0;
  for (const [name, fall, alt, neu] of MUTATIONEN) {
    const n = QUELLE.split(alt).length - 1;
    if (n !== 1) { console.log(`FEHL  ${name} · Muster steht ${n}-mal statt einmal`); continue; }
    const zeilen = await pruefe(QUELLE.replace(alt, neu));
    const treffer = zeilen.some((z) => z.startsWith(fall + " "));
    if (treffer) rot += 1;
    console.log(`${treffer ? "ROT " : "FEHL"}  ${name} · erwartet ${fall}, rot: ${zeilen.map((z) => z.split(" ")[0]).join(",") || "keiner"}`);
  }
  const ok = rot === MUTATIONEN.length;
  console.log(ok ? `ROTPROBE BESTANDEN: Stand grün, ${rot} von ${MUTATIONEN.length} Mutationen im benannten Fall rot`
    : `ROTPROBE NICHT BESTANDEN: ${rot} von ${MUTATIONEN.length} im benannten Fall rot`);
  process.exit(ok ? 0 : 1);
})();
