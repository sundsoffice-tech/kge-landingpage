# Deployment: Landingpage Kfz Gutachter Es

Zwei Seiten, deploy-fertig für die Kampagnen aus `../kampagnen-vorbereitung/`:

| Datei | Zweck | Kampagnen-Ziel-URL (nach DNS-Umstellung) |
|---|---|---|
| `index.html` | Haupt-Landingpage (identisch mit Portal-Prototyp) | `https://kfz-gutachter-moenchengladbach.de/` |
| `umland.html` | Stadt-Variante für die Umland-Kampagne (Viersen, Korschenbroich, Neuss, Kaarst, Grevenbroich) | `https://kfz-gutachter-moenchengladbach.de/umland.html` |

**Staging (sofort erreichbar):** https://sundsoffice-tech.github.io/kge-landingpage/ — beide Seiten stehen auf `noindex`, Google indexiert nichts.

## Nach der Domain-Registrierung (10 Minuten)

1. **CNAME-Datei anlegen:** eine Datei `CNAME` (ohne Endung) mit genau einer Zeile `kfz-gutachter-moenchengladbach.de` ins Repo legen und pushen.
2. **DNS beim Registrar setzen:**
   - 4× A-Record auf `@`: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - 1× CNAME-Record `www` → `sundsoffice-tech.github.io`
3. **GitHub Pages:** Repo → Settings → Pages → Custom domain `kfz-gutachter-moenchengladbach.de` eintragen, nach dem DNS-Check „Enforce HTTPS" aktivieren (Zertifikat kommt automatisch, dauert bis ~1 h).
4. **Zweitdomain** unfallgutachten-mg.de beim Registrar per Weiterleitung (301) auf die Hauptdomain zeigen lassen.
5. **Vor Kampagnenstart:** `noindex` aus beiden Seiten entfernen (Zeile `<meta name="robots" content="noindex">`), Google Tag einbauen (siehe Kampagnen-Mappe, Blatt „Einstellungen & Tracking"), echte Betriebsfotos einsetzen.

## Änderungen deployen

Dateien hier bearbeiten, dann `git add -A && git commit && git push` — GitHub Pages baut automatisch (1–2 Min).
