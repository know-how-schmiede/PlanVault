# WI-PlanArchiv

![WI-PlanArchiv – Vorlesungsplanung sichern. Immer verfügbar.](images/WI-PlanArchiv_%20Vorlesungsplanung%20sichern.png)

**Vorlesungsplanung sichern. Immer verfügbar.**

WI-PlanArchiv ist eine eigenständige, interne Webanwendung zur automatisierten Sicherung, Versionierung und übersichtlichen Anzeige von Vorlesungsplänen. Ausgangspunkt ist die Vorlesungsplanung der Wirtschaftsingenieurwesen-Studiengänge (WI) der Hochschule Pforzheim im QIS-LSF-System. Die Architektur soll eine spätere Erweiterung auf andere Studiengänge ermöglichen.

> **Projektstatus:** Konzept / Entwicklungsstart. Die technische Struktur der LSF-Seiten und der konkrete Abrufmechanismus sind noch nicht verifiziert. Alle gezeigten Beispieltermine sind fiktiv.

## Ziele

- Ausgewählte Studiengänge bzw. standardmäßig die relevanten WI-Studiengänge regelmäßig sichern.
- Im Administrationsbereich getrennt festlegen, **welche Studiengänge archiviert** und **welche öffentlich innerhalb des berechtigten Hochschulnetzes angezeigt** werden.
- Die Sicherungen unabhängig vom ursprünglichen LSF-System verfügbar halten, auch bei einem Ausfall der Quelle.
- Den letzten **erfolgreich und vollständig** gesicherten Stand stets abrufbar halten.
- Stundenpläne in einer modernen, responsiven Oberfläche statt primär in der ursprünglichen LSF-Darstellung anzeigen.
- Änderungen zwischen Sicherungsständen später nachvollziehbar machen.
- Eine archivierte Originaldarstellung als Ergänzung zur Prüfung vorhalten, soweit technisch und rechtlich zulässig.

## Datenquelle

Hinweise zur internen QIS-LSF-Datenquelle und zum vertraulichen Umgang mit der Quell-URL stehen in der [Dokumentation zur Datenquellenkonfiguration](docs/source-configuration.md).

## Funktionsumfang

### Stundenplanansicht

- Studiengang, Fachsemester, Hochschulsemester und Kalenderwoche auswählen.
- **Wochenansicht** als Standard mit farblich unterscheidbaren Veranstaltungstypen.
- **Listenansicht** für schmale Bildschirme und barrierearme Nutzung.
- Veranstaltungsdetails: Titel, Datum, Start/Ende, Raum, Lehrperson, Veranstaltungstyp, soweit in der Quelle vorhanden.
- Anzeige von **Archivstand** und Zeitpunkt der letzten erfolgreichen Sicherung; keine irreführende Live-Darstellung.
- Später: Änderungsansicht, Suche, PDF- und iCal-Export.

### Administrationsbereich

- Erkannte Studiengänge sichten, aktivieren und deaktivieren.
- Pro Studiengang getrennt konfigurieren: `backup_enabled`, `display_enabled`, ggf. Priorität oder Gruppierung.
- Sicherungszeitpunkte und Zeitzone einstellen (Vorgabe: `Europe/Berlin`).
- Backups manuell starten und Ergebnis, Dauer und Fehler einsehen.
- Speicher- und Aufbewahrungsregeln einstellen, Versionen durchsuchen.
- Datenquelle und Importstatus überwachen.
- Administrative Funktionen nur nach Anmeldung und entsprechender Berechtigung anbieten.

### Sicherung und Historie

- Automatisierte Sicherung zu konfigurierten Zeiten.
- Möglichst vollständigen Semesterzeitraum berücksichtigen, nicht nur die aktuell sichtbare Woche.
- Für jeden Durchlauf Ergebnisstatus, Quelle, Abrufzeit und Umfang protokollieren.
- Gleiche Inhalte mittels kanonischer Daten / Hash erkennen, um unnötige neue Versionen zu vermeiden.
- **Atomare Veröffentlichung:** Erst nach erfolgreicher Erfassung und Validierung wird ein neuer Stand als „aktuell“ markiert.
- Bei Fehlern bleibt der letzte gültige Stand sichtbar; Fehlversuche überschreiben keine Daten.
- Original-HTML und nötige statische Ressourcen optional sichern; zusätzliche strukturierte Speicherung als Grundlage der eigenen Webansicht.
- Später: Unterschiede zwischen Versionen (neu, verschoben, geändert, entfallen).

## Empfohlener Technologie-Stack

| Bereich | Vorgesehene Technik |
| --- | --- |
| Laufzeit | Python 3, Debian-LXC auf Proxmox |
| Web-Backend | Flask |
| Web-Frontend | Servergerenderte Templates, Bootstrap 5, wenig JavaScript |
| Datenbank | SQLite (Startphase) mit Migrationskonzept |
| HTTP-Abruf | `httpx` oder `requests`, bei Bedarf Playwright |
| Zeitsteuerung | systemd-Timer **oder** APScheduler; nur ein aktiver Scheduler |
| App-Server | Gunicorn und optional Nginx |
| Tests | pytest, Fixture-basierte Parser- und Integrationstests |
| Archivdateien | Versionierte Ablage außerhalb des Webroots |

Keine unnötig komplexe Infrastruktur im MVP. Parser und Abrufcode sollen unabhängig von der Weboberfläche sein.

## Architektur (geplant)

```text
QIS-LSF / Intranet
       |
       v
Abrufadapter (HTTP; ggf. Browser)
       |
       v
Parser + Normalisierung + Plausibilitätsprüfung
       |
       +--> Originalsnapshot / Rohdaten (optional)
       |
       v
Versioniertes Archiv (SQLite + Dateien)
       |
       +--> Sicherungs-/Statusverwaltung
       |
       v
Flask-Webanwendung
       +--> Wochenansicht / Listenansicht
       +--> Archivhistorie / später Änderungsansicht
       +--> geschützter Adminbereich
```

### Datenmodell (konzeptionell)

- **StudyProgram**: Quellkennung, Name, Zuordnung, `backup_enabled`, `display_enabled`.
- **AcademicTerm**: Bezeichnung, Zeitraum, ggf. LSF-Kennung.
- **ProgramPlan**: Studiengang, Fachsemester/Vertiefung, Semester und Datenquellenzuordnung.
- **BackupRun**: Start/Ende, Auslöser, Status, Fehlerdiagnose, geprüfte/gesicherte Einheiten.
- **Snapshot**: Planbezug, Erfassungszeit, Inhaltshash, Vollständigkeitsstatus, Dateipfade.
- **Event**: Veranstaltungstitel, Termin, Uhrzeit, Raum, Lehrperson und Typ mit Herkunftsbezug.

Da wiederkehrende Veranstaltungen, Gruppen, Blocktermine und Semesterwochen vorkommen können, darf die konkrete Struktur erst nach Sichtung realistischer Quelldaten festgelegt werden. Unbekannte Felder dürfen nicht stillschweigend als leerer, gesicherter Fakt dargestellt werden.

## Sicherungsstrategie

Empfohlener Start: alle relevanten WI-Studiengänge als Standardauswahl, andere Studiengänge technisch unterstützbar, aber nicht ungeprüft massenhaft abrufen. Die Einstellung zur **Archivierung** ist von der Einstellung zur **Anzeige** getrennt. Ein Studiengang kann gesichert, aber in der allgemeinen Übersicht ausgeblendet sein.

Zeitplanbeispiel: täglich 06:00, 12:00 und 18:00 Uhr in `Europe/Berlin` (nur Vorschlag, konfigurierbar). Abrufe seriell bzw. mit enger Begrenzung, angemessenen Pausen, Timeouts und zurückhaltenden Wiederholungen ausführen. Vor umfangreicher automatisierter Erfassung die verantwortliche Hochschul-IT/LSF-Administration einbeziehen.

Archivdaten selbst zusätzlich unabhängig sichern (z. B. zweiter Server/NAS, konsistente DB-Sicherung, Wiederherstellungstest). Ein Archiv ist kein vollständiges Backup, solange es nur an einem Speicherort existiert.

## Timeline

Änderungen, Versionsvorschläge und Commit-Kurzbeschreibungen stehen in der [Timeline](docs/timeline.md).

## Meilensteine

Die [Roadmap](docs/roadmap.md) beschreibt Umsetzungsschritte, Versionsziele und Abschlusskriterien.

1. **M0 – Quellenanalyse:** Ablauf der Studiengangsuche, IDs, Sessions, Semester-/Wochenwechsel und erreichbare Datenformate dokumentieren; ggf. Test-Fixtures speichern.
2. **M1 – Import-Prototyp:** Einen ausgewählten WI-Studiengang vollständig abrufen und valide, normalisierte JSON-Daten erzeugen; Rohantwort optional separat sichern.
3. **M2 – Persistenz:** SQLite-Modelle, Importläufe, unveränderliche Snapshots und atomare Aktualisierung des gültigen Stands.
4. **M3 – Web-MVP:** Responsive Wochen-/Listenansicht, Filter und Sicherungszeitpunkt anzeigen.
5. **M4 – Administration:** Geschützte Studiengangverwaltung, Zeitsteuerung, manueller Start, Protokolle und Aufbewahrung.
6. **M5 – Erweiterungen:** Versionsvergleich, Änderungsansicht, Suche, Exporte und zusätzliche Studiengänge.

## Lokale Entwicklung und Deployment

Die konkreten Installations- und Startbefehle werden nach dem initialen Codegerüst ergänzt. Zielumgebung ist ein Debian-LXC auf Proxmox; für die Entwicklung sind ein Python-Virtualenv und eine lokale SQLite-Datenbank ausreichend. Konfiguration über Umgebungsvariablen bzw. nicht eingecheckte Konfigurationsdateien.

**Wichtig:** Der produktive Sicherungsdienst muss die Quelle aus dem Hochschulnetz tatsächlich erreichen können. Die öffentliche Erreichbarkeit der Archivansicht und deren Berechtigungen sind unabhängig davon zu prüfen.

## Sicherheit, Datenschutz und Verantwortung

- Nur mit Berechtigung auf Quellen zugreifen und Abruflast gering halten.
- Keine Passwörter, Session-Cookies, API-Tokens oder privaten Zugangsdaten ins Repository aufnehmen.
- Adminzugriff authentifizieren; schreibende Endpunkte absichern (u. a. CSRF, Eingabevalidierung).
- Archivierte Quellseiten nicht ungeprüft als aktives HTML ausführen: Inhalte sanitizen, Sicherheitsheader verwenden, fremde Skripte grundsätzlich nicht weiterreichen.
- Personenbezogene Daten (z. B. Lehrpersonennamen) nur im erforderlichen, zulässigen Umfang speichern und sichtbar machen; Aufbewahrungsfristen abstimmen.
- Keine Behauptung, dass archivierte Angaben den jeweils aktuellsten LSF-Stand darstellen.

## Projektdateien

```text
README.md               Projektüberblick
AGENTS.md               Verbindliche Arbeitsanweisungen für Codex
assets/                 Logos, Banner und spätere Screenshots
backend/                Backend und Import-Logik (geplant)
frontend/               Templates und statische Dateien (geplant)
tests/                  Automatische Tests und Test-Fixtures (geplant)
docs/                   Architektur, Entscheidungen, Installation (geplant)
```

## Lizenz

Noch festzulegen. Bis eine Lizenzdatei hinzugefügt wurde, wird keine Nutzungslizenz für Dritte eingeräumt. Hochschulinterne Anforderungen und mögliche Rechte an archivierten Inhalten sind vor Veröffentlichung zu klären.
