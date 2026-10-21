# Unvollständige Import-Vorschau ab V0.0.21

Die Startseite verlinkt auf `/vorschau`. Dort erscheinen eingelesene Termine als
responsive Liste mit Kalenderwochenfilter, Raum, Lehrperson und lokalem Datum
(Europe/Berlin). Die Warnung „Unvollständig · kein freigegebener Archivstand“ bleibt
immer sichtbar. Blockierte Veranstaltungen fehlen in der Liste und werden gezählt.
Fachlich prüfpflichtige Termine sind markiert. Freitextbemerkungen und Quelladressen
werden nicht in die Vorschau übernommen. Die Quelle bleibt für die Prüfung maßgeblich.

## 1. Aktualisieren und Anzeige vorbereiten

Zuerst V0.0.25 auf GitHub veröffentlichen und das [Update](install.md#vorhandene-installation-aktualisieren)
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

## Wochenansicht ab V0.0.22

Nach dem Update öffnet der Vorschau-Link standardmäßig die Wochenansicht. Vorhandene
Vorschau-Dateien aus V0.0.21 bleiben lesbar: Für die neue Darstellung sind weder
Datenmigration noch erneuter Import nötig. Ohne Vorschau-Datei weiterhin zuerst
die Einrichtung oben durchführen.

- Montag bis Sonntag erscheinen mit Datum und zeitlich sortierten Terminen.
- Am Desktop stehen die Tage nebeneinander; auf kleineren Bildschirmen werden sie
  in zwei Spalten oder untereinander angezeigt. Zeitgleiche Termine bleiben erhalten.
- Standardauswahl ist die aktuelle Woche in Europe/Berlin, sofern sie Termine enthält.
  Sonst erscheint die nächste erfasste Woche, nach Semesterende die letzte vorhandene.
- „Vorherige/Nächste erfasste Woche“ navigiert zwischen Wochen mit Vorschauterminen.
  Lücken werden ausdrücklich nicht als freie Wochen interpretiert.
- „Listenansicht“ behält die gewählte Woche bei. Dort kann zusätzlich „Alle erfassten
  Wochen“ ausgewählt werden. Der Wechsel zurück wählt wieder eine einzelne Woche.
- Tage ohne Einträge zeigen „Keine erfassten Termine. Abdeckung ungeprüft.“

Die Ansicht ist weiterhin unvollständig; sie bestätigt weder Semesterabdeckung noch
Archivfreigabe. Alle Termine und Warnhinweise stammen aus derselben lokalen Vorschau.


## Web-Vorschau ab V0.0.25 mit wiederverwendbarer Auswahl

Die Auswahl aus der ursprünglichen Quellenanalyse ist **Wirtschaftsingenieurwesen /
Management und Technik, Prüfungsordnung 2024**, Wintersemester 2026/27. Der
erneute Live-Lauf erfasst 66 bekannte Details. Daraus entstehen 65 Vorschauen mit
942 Terminen; ein Detail mit ungeklärten Einführungsbemerkungen bleibt blockiert.
23 der erzeugten Vorschauen bleiben fachlich prüfpflichtig. Dies ist keine
vollständige Semesterfreigabe.

Der lokale Test hat Speichern, Laden und die Ausgabe über beide Webansichten
geprüft. Die temporäre Datei wurde anschließend entfernt. Damit wurden weder die
LXC-Vorschau aktualisiert noch ein Deployment oder eine Archivfreigabe durchgeführt.
Ein Update allein lädt weiterhin keine Termine.

### Einmalig im LXC einrichten

Zuerst den Code von V0.0.25 auf GitHub veröffentlichen und das bestehende
[Update](install.md#vorhandene-installation-aktualisieren) ausführen. In der
Container-Konsole als root `/etc/wi-planarchiv/app.env` öffnen:

```bash
nano /etc/wi-planarchiv/app.env
```

Die folgenden Werte ergänzen oder vorhandene Einträge ändern, niemals doppelt
anlegen. `LSF_BASE_URL`, `LSF_ID_PARAMETER` und `LSF_ID_NAMESPACE` aus der bisherigen
lokalen Konfiguration beibehalten; vertrauliche Werte nicht veröffentlichen.

```text
PREVIEW_FILE=/var/lib/wi-planarchiv/import.preview.json
LSF_STUDY_QUERY='Wirtschaftsingenieur'
LSF_STUDY_TITLE='BWING MT | Wirtschaftsingenieurwesen / Management und Technik (PO-Version 2024)'
LSF_SEMESTER='WiSe 2026/27'
```

Zusätzlich `LSF_STUDY_KEY` und `LSF_REGULATIONS_KEY` mit den **bisher für diese
Auswahl verwendeten opaken Kennungen** belegen. Falls diese bisher nur als
`--study-key` und `--regulations-key` eingegeben wurden, dieselben Werte übernehmen.
Keine URL und keine Veranstaltungskennung eintragen. Falls für diese Auswahl
noch keine lokalen Kennungen festgelegt wurden, können beispielsweise `WI-MT`
und `PO-2024` gewählt und fortan beibehalten werden. Diese lokalen Namen ersetzen
keinen fachlichen Nachweis der Quellzuordnung.

Nach dem Speichern von `PREVIEW_FILE` den Dienst einmal neu starten, damit er den
Dateipfad übernimmt:

```bash
systemctl restart wi-planarchiv
```

### Vorschautermine einlesen und später erneut aktualisieren

Standardpfade und Dienstkonto der Installation verwenden; abweichende Werte lokal
anpassen. Die Konfigurationsdatei muss vom Administrator gepflegt und vertrauenswürdig
sein. Ihre Inhalte nicht ins Terminal ausgeben.

```bash
cd /opt/wi-planarchiv
set -a
. /etc/wi-planarchiv/app.env
set +a
runuser -u wi-planarchiv -- env PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m flask --app backend source-semester-check \
  --details --detail-budget 80 --save-preview --json
```

Die fünf Auswahlwerte werden aus der exportierten Umgebung übernommen. Explizite
Optionen wie `--title` haben Vorrang. Alle fünf Werte bleiben lokal; die Anwendung
lädt `.env` oder `app.env` nicht selbst. Auch eine reine Ansichtsprüfung ohne
`--details` bleibt mit hinterlegten Detailwerten möglich.

Im JSON-Bericht (Schema 7) den neuen Abschnitt `preview_save` kontrollieren:

```json
"preview_save": {
  "requested": true,
  "saved": true,
  "event_count": 942
}
```

942 ist die Zahl des Live-Nachweises, kein fest vorgeschriebener Sollwert für
spätere Läufe. `saved: true` bestätigt den abgeschlossenen Dateiaustausch. Bei
`false` wurde durch diesen Lauf keine neue Vorschau gespeichert; eine ältere
Datei kann weiterhin vorhanden sein. Ohne `--save-preview` ist `requested` false.
Die Textausgabe meldet den Speicherstatus ebenfalls. Dateipfade und Auswahlwerte
erscheinen nicht im bereinigten Bericht.

Der Befehl endet weiterhin mit **Exitcode 1**, auch nach erfolgreichem Speichern:
`needs_review`, `complete: false` und `published: false` betreffen die fehlende
Archivfreigabe. `preview_save.saved` betrifft ausschließlich die ausdrücklich
aktivierte unvollständige Web-Vorschau. Bei `status: failed` Fehlerursache prüfen;
fehlgeschlagene oder leere Importe ersetzen die bisherige Datei nicht.

Anschließend `/vorschau` öffnen und **Studiengang, Prüfungsordnung, Semester und
Erstellungszeitpunkt** kontrollieren. Der neue Studiengangstext stammt aus der
gewählten Trefferbeschriftung; er bestätigt noch keine vollständige Quellzuordnung.
Wochen- und Listenansicht lesen die neue Datei ohne weiteren Neustart. Ältere
Vorschaudateien bleiben lesbar und zeigen, dass der Studiengang noch nicht
hinterlegt ist. Zum Aktualisieren denselben Importblock erneut ausführen; parallele
Vorschauimporte weiterhin vermeiden.


## Ergänzung V0.0.26 – Abgleich ohne Vorschauänderung

Der separate [Ansichtsabgleich](view-comparison.md) prüft Veranstaltungsziele aus
Wochen- und Semesteransichten. Er verändert die hier angezeigten Termine nicht.
Der bisherige manuelle Vorschauimport wurde vom Nutzer als erfolgreich bestätigt.
Zum erneuten Einlesen weiterhin `source-semester-check --details --save-preview`
mit der eingerichteten Auswahl verwenden.
