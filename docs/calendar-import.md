# Kalenderimport und Archiv ab V0.0.30

`source-calendar-import` verbindet beide Semesteransichten, alle Wochen des unabhängig angegebenen Semesters und die Detailseiten. Die bisherigen Diagnosebefehle bleiben unverändert. Ein Aufruf erzeugt ausschließlich einen **vorläufigen** SQLite-Importlauf. Das lokale Archiv unter `/archiv` zeigt ausschließlich freigegebene Snapshots; `/vorschau` bleibt davon unabhängig.

## Konfiguration und Semesterregeln

In `/etc/wi-planarchiv/app.env` ergänzen:

```sh
ARCHIVE_DATABASE=/var/lib/wi-planarchiv/archive.sqlite
```

Das bestehende Dienstkonto benötigt Schreibrechte im Datenverzeichnis. Keine Datenbank im Checkout oder Webroot ablegen. Neue Datenbank-, Sperr-, Sicherungs- und Prüfpaketdateien erhalten Dateirechte 0600. Die vorhandenen Quell- und Identitätswerte beibehalten. `LSF_STUDY_QUERY` liefert den Suchbegriff; die genaue Studiengangsauswahl und die restliche Zuordnung kommen aus der Regeldatei. Die App liest Konfiguration bei ihrem Start; nach Änderung den Dienst neu starten.

Die folgende **rein fiktive** Regeldatei erläutert das Schema. Tatsächliche Werte ausschließlich außerhalb des Repositorys ablegen, beispielsweise `/etc/wi-planarchiv/calendar-policy.json`:

```json
{
  "schema": 1,
  "semester": "DEMO-Semester",
  "study_key": "DEMO-STUDIUM",
  "regulations_key": "DEMO-PO",
  "study_title": "Fiktives Studium",
  "start": "2026-09-01",
  "end": "2027-02-28",
  "breaks": [
    {
      "start": "2026-12-24",
      "end": "2027-01-03",
      "evidence": "Fiktiver geprüfter Semesterkalender Stand 2026"
    }
  ],
  "annotation_rules": []
}
```

Alle Datumswerte sind ISO-Daten. Zeiträume dürfen sich nicht überlappen und müssen im Semester liegen. `evidence` ist die Bezeichnung eines tatsächlich geprüften Belegs, keine Quelladresse. Die früher dokumentierte aktuelle offizielle Semesterterminliste ist eine fachliche Grundlage für die echte Regeldatei; die fiktiven Beispieldaten dürfen dafür nicht übernommen werden. Die Anwendung lädt keinen externen Ferienkalender automatisch. Eine Änderung der Regeldatei wird erst beim nächsten Import wirksam.

Ferienregeln betreffen ausschließlich wiederkehrende `woch`-Termine: Ein an einem explizit freien Tag in der Wochenansicht fehlender Termin wird mit Datum, Detail- und Seriennummer als Ausnahme protokolliert. Sichtbare Termine bleiben auch während der Ferien erhalten. Einzel-, Nachhol- und Sondertermine werden niemals pauschal wegen Ferien entfernt. Unbenannte Tageshinweise sind nur innerhalb eines explizit belegten freien Zeitraums einordenbar; andere unbekannte Hinweise bleiben prüfpflichtig.

## Import und Einzelterminvergleich

```sh
cd /opt/wi-planarchiv
set -a
. /etc/wi-planarchiv/app.env
set +a
runuser -u wi-planarchiv -- env PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m flask --app backend source-calendar-import \
  --policy /etc/wi-planarchiv/calendar-policy.json --detail-budget 80
```

Der Import verwendet höchstens 100 serielle HTTP-Anfragen, eine Sekunde Abstand und keine automatischen Wiederholungen. Ein Fehler beim Abruf, unbekannte Tabellenstruktur, fehlende Woche oder zu kleines Budget führt zum gescheiterten Lauf; der letzte gültige Archivstand bleibt erhalten. Die Archivdatei wird während des gesamten Imports gegen einen zweiten Importprozess gesperrt. Normale Webseitenaufrufe importieren nichts.

Das JSON-Ergebnis enthält die Lauf-ID, Inhaltsprüfsumme, Terminanzahl und Anzahlen harter bzw. fachlicher Befunde. Exitcode 1 bedeutet hier bewusst: **nicht veröffentlicht**, auch wenn ein vorläufiger Import erfolgreich gespeichert wurde. Erfolgreiche Archivfreigabe hat Exitcode 0.

Tageskolumnen werden einschließlich `rowspan`/`colspan` ausgewertet. Verglichen werden Veranstaltung, lokales Datum, Anfang, Ende, Raumcode und Veranstaltungsart als Multimenge. Doppelte Termine bleiben unterscheidbar; bloße Wochenpräsenz reicht nicht. Die Wochenansicht ergänzt teilweise eine Raumbezeichnung vor dem Detail-Raumcode. Nur eindeutige Zuordnungen zu einem vorhandenen Detailcode werden akzeptiert und bleiben im Prüfpaket nachvollziehbar. Explizite Klausurzeiten aus einem bereits unterstützten Detailhinweis haben Vorrang vor der ursprünglichen Blockzeit. Abweichungen, unerwartete Blöcke und Termine außerhalb des Semesters sind harte Freigabesperren.

Die Quelle zeigt nur Montag bis Freitag. Wochenendtermine aus Details bleiben im Kalender enthalten. Eine fünftägige Ansicht allein bestätigt keine Wochenendfreiheit. Gruppen und Lehrpersonen werden aus vorhandenen Detailangaben erhalten; ergänzende Blocktexte werden für die fachliche Prüfung mitgeführt. Eine Gruppenzuordnung wird nicht aus einem abgeschnittenen Titel geraten.

## Hinweise, Gruppen und Vollständigkeit prüfen

```sh
runuser -u wi-planarchiv -- .venv/bin/python -m flask --app backend archive-review-export \
  --run-id LAUF-ID-AUS-DEM-IMPORT \
  --output /var/lib/wi-planarchiv/calendar.review.json
```

Neue Ausgabedatei verwenden; vorhandene Dateien werden nicht überschrieben. Das Paket enthält personenbezogene Veranstaltungsangaben und gehört ausschließlich ins geschützte lokale Datenverzeichnis. Ein Export in das Repository ist gesperrt. Es enthält Originalterminserien, Hinweistexte, laufbezogene Veranstaltungsnummern, beobachtete Felder, Ferienausnahmen, harte Befunde und eine zunächst unbestätigte Entscheidungsvorlage.

Fachliche Prüfpunkte umfassen insbesondere Ausfall-/Verlegungshinweise, Klausur-/Raumhinweise, Gruppen und Lehrpersonen, Wochenendbestand, Semesterumfang, Studiengang und Prüfungsordnung sowie die verwendete Ferienregel. Vor einer Bestätigung den jeweiligen Sachverhalt anhand der Quelle bzw. eines unabhängigen Belegs prüfen. Bei fehlendem Wochenendnachweis bleibt die Freigabe offen; die Software liefert keinen Ersatzbeleg. Die Entscheidungsvorlage unter `approval.decisions` enthält pro Befund:

```json
{"decision": "pending", "evidence": ""}
```

Erst nach der konkreten Prüfung `decision` auf `confirmed` setzen und unter `evidence` einen nachvollziehbaren Prüfbeleg eintragen. Die Bestätigung gilt exakt für diesen kompletten Importinhalt einschließlich aller Serien, Blocktexte, Regeln und Befunde. Änderungen am Import oder fehlende/zusätzliche Bestätigungen machen den Beleg ungültig. Harte Fehler lassen sich damit nicht überstimmen.

Für einen bisher nicht unterstützten, nachweislich rein beschreibenden Serienhinweis kann die Regeldatei eine **exakt gebundene** Auslegung enthalten:

```json
{
  "series_digest": "64-kleine-hexadezimale-Zeichen-aus-dem-Pruefpaket",
  "field": "note",
  "effect": "annotation"
}
```

Das Beispiel ist ein Platzhalter, keine gültige Regel. Den tatsächlichen `series_digest` der betreffenden Serie aus dem Paket übernehmen. Zulässige Felder sind `note` und `execution_note`. Nur verwenden, wenn der gesamte Inhalt tatsächlich keine zusätzliche Zeit-, Raum-, Ausfall- oder Gruppenänderung bedeutet. Der Originalhinweis bleibt im Paket erhalten und benötigt weiterhin fachliche Bestätigung. Veränderte Serien passen nicht mehr auf die Regel; unbenutzte Regeln sperren die Freigabe. Anschließend erneut importieren und ein neues Prüfpaket exportieren. Die Funktion ist kein allgemeiner Freibrief für unbekannte Hinweise.

## Archivfreigabe, Anzeige und Historie

```sh
runuser -u wi-planarchiv -- .venv/bin/python -m flask --app backend archive-publish \
  --run-id LAUF-ID-AUS-DEM-IMPORT \
  --review /var/lib/wi-planarchiv/calendar.review.json
runuser -u wi-planarchiv -- .venv/bin/python -m flask --app backend archive-history
```

Die Freigabe prüft unter einer SQLite-Schreibtransaktion den unveränderten Importinhalt, sämtliche harten Sperren und alle Einzelbestätigungen. Erst danach wird der neue Snapshot letzter gültiger Stand für Studiengang, Prüfungsordnung und Semesterzeitraum. Fehler und leere/unvollständige Importe ändern den bisherigen Stand nicht. Identischer Kalenderinhalt einschließlich identischer Regeln verwendet den vorhandenen Snapshot und vermerkt einen erfolgreichen unveränderten Lauf. Historische Snapshots bleiben bestehen; diese Version löscht keine Archivstände automatisch.

Unter `/archiv` erscheinen Wochen-/Listenansicht, Terminart, vorhandene Gruppen-/Durchführungsangaben, Archivnummer, Zeitpunkt des gespeicherten Stands und letzte erfolgreiche Sicherung. Zeitpunkt und Status des letzten Importversuchs werden getrennt angezeigt. Alle Semesterwochen einschließlich leerer Wochen sind auswählbar. `?snapshot=NUMMER` wählt einen historischen Stand, der bei weiterer Navigation erhalten bleibt. Die Startseite verlinkt das Archiv. Die Oberfläche fragt die Quelle niemals ab und kennzeichnet die fehlende Live-Synchronisation.

## Datenmodell, Sicherung und Wiederherstellung

SQLite-Schemaversion 1 enthält `runs`, unveränderliche `snapshots` und `heads` je Importbereich. Ein neues leeres Archiv wird explizit angelegt; fremde Datenbanken und unbekannte Schemaversionen werden abgewiesen. Künftige Änderungen benötigen eine explizite Migration. Keine destruktive automatische Migration.

```sh
runuser -u wi-planarchiv -- .venv/bin/python -m flask --app backend archive-backup \
  --output /var/lib/wi-planarchiv/archive-backup.sqlite
runuser -u wi-planarchiv -- .venv/bin/python -m flask --app backend archive-restore \
  --input /var/lib/wi-planarchiv/archive-backup.sqlite \
  --output /var/lib/wi-planarchiv/archive-restored.sqlite
```

Beide Befehle verwenden die SQLite-Backup-API, prüfen Schema, Integrität und Fremdschlüssel und schreiben ausschließlich in eine neue Datei. Ein aktives Archiv wird nie durch den Restore-Befehl überschrieben. Für den tatsächlichen Wechsel den Dienst und manuelle Importe stoppen, den bisherigen Stand separat sichern, `ARCHIVE_DATABASE` in der externen Konfiguration auf die geprüfte wiederhergestellte Datei setzen, Dienst starten und `/archiv` sowie `archive-history` prüfen. Dateibesitzer und Rechte beibehalten. Der lokale Test deckt Sicherung, Wiederherstellung, Fehlversuche, Historie und letzten gültigen Stand ab; ein Restore im LXC ist gesondert zu prüfen.

## Prüfstand dieser Version

V0.0.30: 504 lokale Tests erfolgreich, einschließlich Betreiberumgebungsisolation und getestetem Backup/Restore. Abschließend live: 100 serielle Abrufe, 26 Wochen, 66 normalisierbare Details, 824 beobachtete und 824 abgeglichene Termine, 120 protokollierte Ferienausnahmen und keine harten Befunde. 29 fachliche Bestätigungen bleiben offen. Es wurde kein realer Archivstand veröffentlicht und kein Deployment oder Restore im LXC durchgeführt.
