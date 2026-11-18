/* Rotprobe zum Zeugen pruefen/zeuge-einwilligung.js: Kann der Zeuge überhaupt rot werden?
 *
 * Aufruf: node pruefen/rotprobe-einwilligung.js
 * Zuerst der unveränderte Stand (muss grün sein), dann je Mutation eine Kopie von einwilligung.js mit genau einer
 * gezielten Beschädigung im Temp-Ordner; der Zeuge muss jede mit Exit 1 abweisen. Exit 0 nur, wenn der Stand grün
 * ist und jede Mutation rot wurde. Greift eine Ersetzung nicht genau einmal, ist das ein Fehler der Rotprobe
 * (der Quelltext hat sich geändert): Exit 1, Mutation nachziehen.
 * Ohne Fremdpaket; läuft in Sekunden. */
"use strict";
const fs = require("fs"), os = require("os"), path = require("path"), cp = require("child_process");
const ZEUGE = path.join(__dirname, "zeuge-einwilligung.js");
const QUELLE = fs.readFileSync(path.join(__dirname, "..", "einwilligung.js"), "utf8").replace(/\r\n/g, "\n");

const MUTATIONEN = [
  ["M1 Label-Bedingung weg (config mit Callback auch bei leerem Label)",
    'if (anruf && konfig.telefonAnzeige && /^[A-Za-z0-9_-]+$/.test(anruf) && !/X{4,}/.test(anruf)) {',
    "if (konfig.telefonAnzeige) {"],
  ["M2 Rückweg weg (widerrufe stellt die Nummer nicht zurück)",
    "    nummerZurueck();\n    var warErlaubt",
    "    var warErlaubt"],
  ["M3 Auswahl wieder auf alle tel:-Links (Impressum wird mitgetauscht)",
    "'a[href^=\"tel:\"][data-messung=\"phone_click\"]'",
    "'a[href^=\"tel:\"]'"],
  ["M4 Einmal-Sperre weg (zweiter Callback wirkt)",
    "if (!tagGeladen || !alt || !geliefert || getauscht.length) return;",
    "if (!tagGeladen || !alt || !geliefert) return;"],
  ["M5 Einwilligungsprüfung im Tausch weg (Callback wirkt ohne Erlaubnis)",
    "if (!tagGeladen || !alt || !geliefert || getauscht.length) return;",
    "if (!alt || !geliefert || getauscht.length) return;"],
  ["M6 Ziffernprüfung weg (Callback ohne brauchbare Ziffern tauscht)",
    "if (anzeige.replace(/\\D/g, \"\").length < MIN_ZIFFERN || ziffern.length < MIN_ZIFFERN) return;",
    ""],
  ["M7 Klartext der echten Nummer bleibt neben dem getauschten Link sichtbar",
    "klartext[k].hidden = true;",
    "klartext[k].hidden = false;"],
  ["M8 Neuladen nach dem Widerruf weg",
    "if (warErlaubt && skriptAngehaengt && !erweitert) window.location.reload();",
    ""],
  ["M9 Cookies werden beim Widerruf nicht gelöscht",
    "loescheGoogleCookies();  /* Widerruf: Cookies weg */",
    ""],
  ["M10 anderer Tab erfährt den Widerruf nicht (storage-Lauscher weg)",
    'window.addEventListener("storage", function (e) { if (e.key === SCHLUESSEL) pruefeGespeichert(); });',
    ""],
  ["M11 Zurück-Taste erfährt den Widerruf nicht (pageshow-Lauscher weg)",
    'window.addEventListener("pageshow", function (e) { if (e.persisted) pruefeGespeichert(); });',
    ""],
  ["M12 Fußlink löscht schon beim Öffnen die gespeicherte Wahl",
    "    /* Nur den Banner zeigen; gespeichert und widerrufen wird erst mit der Entscheidung (Fund 7). */\n",
    "    try { localStorage.removeItem(SCHLUESSEL); } catch (fehler) { /* egal */ }\n"],
  ["M13 gemerkte Nummer wird beim erneuten Erlauben nicht wieder angewendet",
    "    wendeNummerAn();  /* schon gelieferte",
    "    /* schon gelieferte"],
  ["M14 jedes storage- oder pageshow-Ereignis gilt als Widerruf",
    "if (tagGeladen && wahl && wahl.werbung === false) widerrufe();",
    "if (tagGeladen) widerrufe();"],
  ["M15 Klartext kommt beim Widerruf nicht zurück",
    "verborgen.forEach(function (v) { v[0].hidden = v[1]; });",
    ""],
  ["M16 unbrauchbares Label wird stumm verworfen (keine Konsolenzeile)",
    'console.info("[Messung] labels.website_call verworfen',
    'void ("[Messung] labels.website_call verworfen']
];

function zeuge(datei) {
  const lauf = cp.spawnSync(process.execPath, [ZEUGE, datei], { encoding: "utf8" });
  const roteZeilen = (lauf.stdout || "").split("\n").filter(z => z.indexOf("ROT  ") === 0).map(z => z.slice(5).split(":")[0].trim());
  return { exit: lauf.status, rot: roteZeilen, fehler: (lauf.stderr || "").trim().split("\n")[0] };
}

const ordner = fs.mkdtempSync(path.join(os.tmpdir(), "kge-rotprobe-"));
let fehler = 0;
const grund = path.join(ordner, "unveraendert.js");
fs.writeFileSync(grund, QUELLE);
const basis = zeuge(grund);
console.log((basis.exit === 0 ? "GRÜN " : "FEHLER ") + "unveränderter Stand: Exit " + basis.exit + (basis.rot.length ? " · rot: " + basis.rot.join("; ") : ""));
if (basis.exit !== 0) fehler++;

MUTATIONEN.forEach(function (m, i) {
  const treffer = QUELLE.split(m[1]).length - 1;
  if (treffer !== 1) { fehler++; console.log("FEHLER " + m[0] + ": Ersetzung greift " + treffer + "-mal statt einmal"); return; }
  const datei = path.join(ordner, "mutation-" + (i + 1) + ".js");
  fs.writeFileSync(datei, QUELLE.replace(m[1], m[2]));
  const e = zeuge(datei);
  if (e.exit === 1 && e.rot.length) console.log("ROT   " + m[0] + " · " + e.rot.length + " Prüfungen rot, zuerst: " + e.rot[0]);
  else { fehler++; console.log("ÜBERLEBT " + m[0] + ": Exit " + e.exit + " " + e.fehler); }
});
fs.rmSync(ordner, { recursive: true, force: true });
console.log(fehler ? "ROTPROBE NICHT BESTANDEN: " + fehler + " Fehler" : "ROTPROBE BESTANDEN: Stand grün, " + MUTATIONEN.length + " von " + MUTATIONEN.length + " Mutationen rot");
process.exit(fehler ? 1 : 0);
