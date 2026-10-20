# Veranstaltungsdetails prüfen – V0.0.9

Der neue Baustein verbindet erkannte Veranstaltungsblöcke mit ihren Detailseiten.
Die beobachtete Struktur besteht aus acht Tabellenzeilen; der Veranstaltungslink
steht im bekannten Block in der ersten Zeile. Raumlinks werden nicht als
Veranstaltungsziele verwendet. Abweichende Strukturen, mehrere Links in einem
Block, fremde Ziele oder widersprüchliche Beschriftungen führen zum Abbruch.

Ohne konfigurierte Quellkennung gilt weiterhin: Identische absolute Detailziele werden über alle übergebenen Planantworten
zusammengefasst. Unterschiedliche URLs werden auch bei gleichem Titel nicht
zusammengeführt. Das verhindert doppelte Abrufe innerhalb der Stichprobe,
beweist aber **keine dauerhafte Quellidentität**: Sitzungsabhängige URL-Varianten
können weiterhin mehrere Ziele erzeugen. Der interne Hash dient nur der
Zuordnung im Prüflauf; Rohadressen und Linkbeschriftungen bleiben im Arbeitsspeicher.

## Begrenzte Detailstichprobe

Standardmäßig werden zwei, höchstens zehn eindeutige Ziele in der Reihenfolge
ihres Auftretens abgerufen. Jeder Detailparser prüft das ausdrücklich erwartete
Semester. Abruf- oder Parserfehler brechen die gesamte Stichprobe ab; es wird
kein erfolgreiches Teilergebnis zurückgegeben.

Erfolgreich gelesene Serien werden an die Normalisierung übergeben.
Ungeklärte Rhythmen oder Ausnahmen erzeugen den Status
`normalization_requires_review` und keine Kalendervorschau für dieses Detail.
Auch erzeugte Vorschauen behalten ihre Prüfhinweise und `complete=false`.
Die Vorschau umfasst den Datumsbereich der Detailserien, nicht ausschließlich
die Woche, aus der der Link stammt.

## Manueller Prüfbefehl

Nach Veröffentlichung und Installation von V0.0.9, mit gesetztem `LSF_BASE_URL`:

```bash
python -m flask --app backend source-details-check \
  --query "Fiktiv" --title "Fiktives Studium (DEMO-PO)" \
  --semester "WiSe 2026/27" \
  --study-key DEMO-STUDIUM --regulations-key DEMO-PO \
  --week 2026-W44 --limit 2
```

Die Auswahl ist ein Beispiel mit **fiktiven Platzhaltern**. Suchtext, exakter
Treffertitel, erwartete Semesterbeschriftung und Woche müssen zur tatsächlichen
Auswahl passen. Die lokalen Kennungen sind selbst gewählte opake Bezeichner aus
Buchstaben, Ziffern, Bindestrich oder Unterstrich. Sie sind keine verifizierten
Kennungen des Quellsystems und dürfen keine URL enthalten.

Im LXC den [systemd-run-Aufbau](source-check.md) verwenden und den abschließenden
Flask-Befehl durch den obigen Unterbefehl samt Argumenten ersetzen. Es wird kein
Webdienst neu gestartet und kein Archivstand veröffentlicht.

Der Befehl prüft zuerst die explizit gewählte Wochenantwort. Bei Ferienhinweisen,
ungeklärter leerer Ansicht oder falschen Tagesdaten beginnt kein Detailabruf.
Anschließend meldet er nur Anzahlen: erkannte Blöcke, unterschiedliche Ziele,
geprüfte/ungeprüfte Details und ungeklärte Normalisierungen. Keine Quelladressen,
Titel, Räume oder Lehrpersonen werden ausgegeben.

Status 0 bestätigt nur die erfolgreiche begrenzte Stichprobe. Nicht besuchte
Detailziele bleiben ausdrücklich ungeprüft. Fehler oder nicht normalisierbare
Details führen zu Status 1.

## Nachweis und offene Punkte

Am 2026-10-20 lieferte der bisher geprüfte Plan 53 bekannte Blöcke und 47
unterschiedliche absolute Detailziele. Zwei Detailseiten wurden mit der neuen
Pipeline live gelesen: eine beziehungsweise zwei Serien; daraus entstanden
15 beziehungsweise 16 Vorschautermine. 45 Ziele blieben ungeprüft.
Der Ablauf einschließlich Studiengangsnavigation benötigte acht HTTP-Anfragen.
Es wurden keine Rohseiten oder Quelladressen gespeichert.

166 lokale Tests bestehen. Die Pipeline ist noch kein vollständiger
Semesterimport. Dauerhafte Veranstaltungsidentität, sämtliche Detailziele,
Sonderfälle, Wochenenden und Archivveröffentlichung bleiben offen. Die Website
zeigt weiterhin die Startseite mit Versionsfooter.

## Ergänzung V0.0.12

Optional werden Detailziele anhand einer [lokal konfigurierten Quellkennung](source-identity.md) zusammengeführt. Damit verändern Sitzungswerte und Titeländerungen zwischen Läufen die Kennung nicht. Fehlende oder mehrdeutige Kennungen brechen die Stichprobe ab. Studiengangs-/Prüfungsordnungszuordnung und Vollständigkeit bleiben prüfpflichtig.
