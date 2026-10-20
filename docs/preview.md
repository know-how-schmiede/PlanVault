# Unvollständige Import-Vorschau ab V0.0.21

Die Startseite verlinkt auf `/vorschau`. Dort erscheinen eingelesene Termine als
responsive Liste mit Kalenderwochenfilter, Raum, Lehrperson und lokalem Datum
(Europe/Berlin). Die Warnung „Unvollständig · kein freigegebener Archivstand“ bleibt
immer sichtbar. Blockierte Veranstaltungen fehlen in der Liste und werden gezählt.
Fachlich prüfpflichtige Termine sind markiert. Freitextbemerkungen und Quelladressen
werden nicht in die Vorschau übernommen. Die Quelle bleibt für die Prüfung maßgeblich.

## 1. Aktualisieren und Anzeige vorbereiten

Zuerst V0.0.21 auf GitHub veröffentlichen und das [Update](install.md#vorhandene-installation-aktualisieren)
ausführen. Danach ist der Vorschau-Link sichtbar, zunächst ohne Termine.
Ein Update allein lädt keine Hochschuldaten. Es werden auch keine Demo-Termine eingespielt.

Die Vorschau verwendet dieselben Netzwerk-Zugriffsrechte wie die bisherige Webseite;
es gibt noch keine Anmeldung. Sie nur im berechtigten internen Netz aktivieren.
Mit dem Setzen des Dateipfads werden gespeicherte Vorschautermine für Besucher der
Webseite sichtbar. Die Datei liegt außerhalb des Git-Checkouts im vorhandenen Datenbereich.

Als root in der Container-Konsole die Konfiguration öffnen:

```bash
nano /etc/wi-planarchiv/app.env
```

Diese Zeile ergänzen (vorhandene Zeile gegebenenfalls ändern, nicht doppelt anlegen):

```text
PREVIEW_FILE=/var/lib/wi-planarchiv/import.preview.json
```

In nano mit Strg+O und Enter speichern, mit Strg+X schließen. Die vertraulichen Werte
`LSF_BASE_URL`, `LSF_ID_PARAMETER` und `LSF_ID_NAMESPACE` müssen ebenfalls lokal
konfiguriert sein; siehe [Quellkennung](source-identity.md). Keine Werte aus der Anleitung
erraten und keine Konfigurationsinhalte veröffentlichen.

```bash
systemctl restart wi-planarchiv
```

## 2. Einmalig Vorschautermine einlesen

Die folgenden Beispiele verwenden Standardpfad und Dienstkonto. Abweichende
Installationswerte anpassen. Die Konfiguration ist die vom Administrator gepflegte,
vertrauenswürdige Datei; ihre Inhalte nicht ins Terminal ausgeben.

```bash
cd /opt/wi-planarchiv
set -a
. /etc/wi-planarchiv/app.env
set +a
```

Im nächsten Block **alle fünf DEMO-Angaben lokal ersetzen**: Suchbegriff, exakt sichtbarer
Studiengangstitel, erwartete Semesterbezeichnung sowie die beiden eigenen opaken
Studiengangs-/Prüfungsordnungskennungen. Bereits beim Semesterprüflauf verwendete Werte
wiederverwenden. Die Kennungen enthalten keine URL. Dann als Dienstnutzer ausführen,
damit auch der Webdienst die Datei lesen kann:

```bash
runuser -u wi-planarchiv -- env PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m flask --app backend source-semester-check \
  --query "DEMO-Suchbegriff" --title "DEMO-Studiengangstitel" \
  --details --semester "DEMO-Semester" \
  --study-key "DEMO-STUDIUM" --regulations-key "DEMO-PO" \
  --detail-budget 80 --save-preview --json
```

Der Abruf bleibt begrenzt und gedrosselt. Auf den Abschluss warten. Bei `needs_review`
und `known_details_checked: true` ist der bekannte Detailbestand geprüft. Mit
`--save-preview` wird dessen normalisierbarer Anteil gespeichert, sofern mindestens
ein Termin vorliegt. Der Prüfprozess endet weiterhin mit **Exitcode 1**, weil kein
vollständiger Archivstand bestätigt wird. `complete` und `published` bleiben false;
`published` bezieht sich auf die Archivfreigabe, nicht auf die ausdrücklich aktivierte
Vorschau-Anzeige. Bei `failed` wurde keine neue Vorschau übernommen.

## 3. Webseite öffnen

Die bisherige Webadresse aufrufen und „Import-Vorschau öffnen“ wählen. Datum der
Vorschauerstellung kontrollieren. Mit „Kalenderwoche“ und „Anzeigen“ die Liste filtern.
Es ist kein weiterer Neustart nach einem erfolgreichen Import nötig.

- Ohne Konfiguration oder Datei erscheint eine verständliche Leeranzeige.
- Eine beschädigte Datei zeigt einen Hinweis statt eines Serverfehlers.
- Fehlgeschlagene oder leere Importe ersetzen die bisherige Vorschau nicht. Deshalb
  kann ein älterer Stand sichtbar bleiben; immer den Erstellungszeitpunkt beachten.
- Seitenaufrufe lesen ausschließlich die lokale Datei; keine automatischen Quellabrufe.
- Weitere Aktualisierungen erfolgen durch denselben manuellen Importaufruf.

## Speicherung und Grenzen

Eine begrenzte JSON-Datei wird zunächst temporär im gleichen Verzeichnis geschrieben
und danach atomar ersetzt. Kein HTML, keine Cookies und keine Quellverweise werden
gespeichert. Die Datei enthält Veranstaltungstitel, Raum und Lehrperson und gehört
weder ins Repository noch in Fehlerprotokolle. Das bestehende Update sichert den
Datenbereich bereits mit. Dies ist keine Snapshot-Datenbank und keine Historie;
parallele Vorschauimporte vermeiden (der zuletzt fertiggestellte Lauf ersetzt die Datei).

Zum Ausblenden `PREVIEW_FILE=` setzen und den Dienst neu starten. Die vorhandene
Datei bleibt dabei erhalten. Löschen und Aufbewahrung sind lokal zu verwalten.

Nächste Schritte: vollständigen Import absichern, geschützte Archivspeicherung
implementieren und daraus eine Wochenansicht entwickeln. Die lokale Funktion ist
mit fiktiven Daten getestet; ein echter Vorschauimport im Ziel-LXC steht noch aus.
