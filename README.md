# WI-PlanArchiv

![WI-PlanArchiv – Vorlesungsplanung sichern. Immer verfügbar.](images/WI-PlanArchiv_%20Vorlesungsplanung%20sichern.png)

**Vorlesungsplanung sichern. Immer verfügbar.**

WI-PlanArchiv ist eine eigenständige, interne Webanwendung zur automatisierten Sicherung, Versionierung und übersichtlichen Anzeige von Vorlesungsplänen. Ausgangspunkt ist die Vorlesungsplanung der Wirtschaftsingenieurwesen-Studiengänge (WI) der Hochschule Pforzheim im QIS-LSF-System. Die Architektur soll eine spätere Erweiterung auf andere Studiengänge ermöglichen.

> **Projektstatus:** Grundgerüst installiert und Update getestet. Die Quellenanalyse läuft: Studiengangsuche, Planabruf und Wochenwechsel sind per HTTP ohne Anmeldung verifiziert. Ein erster Detailparser liest Terminserien und ist mit fiktiven Testdaten sowie zwei Live-Detailseiten geprüft. Eine JSON-fähige Kalendervorschau und ein Wochenabgleich sind implementiert und mit fiktiven Grenzfällen getestet. Ein begrenzter HTTP-Abrufadapter, ein manueller [Quelltest](docs/source-check.md) und eine zusätzlich live geprüfte [Studiengangsnavigation](docs/form-navigation.md) sind vorhanden. Die [Wochennavigation](docs/week-navigation.md) ist für zwei Wochen live geprüft und erkennt fehlende oder prüfpflichtige Wochen. Eine begrenzte [Detailstichprobe](docs/detail-sample.md) verbindet Planlinks mit Parser und Kalendervorschau und wurde an zwei Details live geprüft. Ein [gemeinsamer Import-Prüflauf](docs/import-check.md) verbindet diese Schritte und liefert einen bereinigten JSON-Bericht. Ein erster [Einzeltermin mit Ausfallhinweis](docs/special-dates.md) ist live belegt und wird unterstützt. Ab V0.0.12 ist eine [sitzungsunabhängige Veranstaltungskennung](docs/source-identity.md) lokal konfigurierbar und über getrennte Sitzungen geprüft. Ab V0.0.13 prüft eine [Bestandsaufnahme zusätzlicher Semesteransichten](docs/semester-check.md) die Semester- und Block-/Einzelterminansicht; live wurden 54 unterschiedliche Detailziele erfasst. Ab V0.0.14 kann derselbe Befehl alle bekannten Detailziele innerhalb eines festen Budgets gegen das erwartete Semester prüfen. V0.0.15 unterstützt mehrere Ausfallangaben mit optionalen Hinweisen und unterscheidet blockierte Normalisierungen von Vorschauen mit Prüfhinweisen. V0.0.16 erhält Verlegungshinweise ohne automatisch abgeleitete Ersatztermine und unterstützt die belegten Serienhinweise zu Vorlesung, Nachholtermin und Laborraum; fachliche Prüfhinweise bleiben erhalten. V0.0.17 erkennt eine zusätzliche Blockdarstellung und erfasst dadurch 66 statt zuvor 54 Veranstaltungsziele; die Zusatzansicht war nicht leer. V0.0.18 zeigt das vorhandene Logo im Seitenkopf, benötigt für Installation und Update kein curl und unterstützt ausdrücklich angegebene Klausurzeiten innerhalb eines Einzeltermins. V0.0.19 verwendet das gewünschte kompakte Logo mit Überschrift rechts daneben und zeigt die nächsten geplanten Schritte. Der User bestätigt den funktionierenden Stand nach V0.0.19. V0.0.20 ergänzt einen Wochentagsabgleich im Semesterbericht und verständliche Installations- und Update-Schritte mit aktuellem wget-Aufruf. Vollständiger Import, weitere Sonderfälle und Semestererfassung folgen. Siehe [Quellenanalyse](docs/source-analysis.md).

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

Aktueller Schritt ist die [Quellenanalyse (M0)](docs/source-analysis.md). Installation, Update und Betrieb wurden vom Projektverantwortlichen erfolgreich getestet.

Die [Roadmap](docs/roadmap.md) beschreibt Umsetzungsschritte, Versionsziele und Abschlusskriterien.

1. **M0 – Quellenanalyse:** Ablauf der Studiengangsuche, IDs, Sessions, Semester-/Wochenwechsel und erreichbare Datenformate dokumentieren; ggf. Test-Fixtures speichern.
2. **M1 – Import-Prototyp:** Einen ausgewählten WI-Studiengang vollständig abrufen und valide, normalisierte JSON-Daten erzeugen; Rohantwort optional separat sichern.
3. **M2 – Persistenz:** SQLite-Modelle, Importläufe, unveränderliche Snapshots und atomare Aktualisierung des gültigen Stands.
4. **M3 – Web-MVP:** Responsive Wochen-/Listenansicht, Filter und Sicherungszeitpunkt anzeigen.
5. **M4 – Administration:** Geschützte Studiengangverwaltung, Zeitsteuerung, manueller Start, Protokolle und Aufbewahrung.
6. **M5 – Erweiterungen:** Versionsvergleich, Änderungsansicht, Suche, Exporte und zusätzliche Studiengänge.

## Lokale Entwicklung und Deployment

Für einen Debian-13-LXC stehen das [Installationsskript](scripts/install-debian13.sh) und ein [Update-Skript](scripts/update-debian13.sh) für vorhandene Installationen bereit. Der Installer lädt den gewählten Branch oder Tag automatisch aus GitHub. Die [Installationsanleitung](docs/install.md) enthält den Schnellstart ohne vorhandenen Checkout; [scripts/README.md](scripts/README.md) bietet den kurzen Einstieg sowie Hinweise zu den interaktiven Standardwerten.

Voraussetzung: Python 3.11 oder neuer. Im Repository-Hauptverzeichnis eine virtuelle Umgebung anlegen und die Abhängigkeiten installieren:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m flask --app backend:create_app run
```

Unter Linux entsprechend `.venv/bin/python` statt `.venv\Scripts\python` verwenden. Die lokale Startseite ist unter `http://127.0.0.1:5000` erreichbar. Der Flask-Entwicklungsserver ist für die lokale Entwicklung vorgesehen.

Tests ausführen:

```powershell
.venv\Scripts\python -m pytest
```

Flask stellt Web-Routen und Templates bereit. Beautiful Soup liest die beobachtete HTML-Tabellenstruktur. pytest prüft Startseite, Footer-Version, vertrauliche Konfiguration und den Detailparser. Die Startseite benötigt keine Datenquelle und führt keine Abrufe aus. `LSF_BASE_URL` wird nur bei Bedarf über die Prozessumgebung bereitgestellt. `.env.example` dokumentiert den Variablennamen; `.env` wird nicht automatisch geladen. Siehe [Datenquellenkonfiguration](docs/source-configuration.md).

Das Grundgerüst enthält getrennte Pakete für Import, Parser, Speicherung und Scheduler. Der Parser für Veranstaltungsdetails ist implementiert; Netzwerkimport, Persistenz und Zeitsteuerung folgen in den nächsten Meilensteinen. Der Parser erzeugt noch keine einzelnen Kalendertermine und bestätigt keine Semester-Vollständigkeit. Zielumgebung bleibt ein Debian-LXC auf Proxmox mit SQLite. Produktionsdeployment und Datenbank werden später ergänzt.

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
docs/AGENTS.md          Verbindliche Arbeitsanweisungen für Codex
images/                 Projektbanner
version.py              Zentrale Anwendungsversion
backend/                Flask-App und Pakete für die spätere Import-Logik
backend/templates/      Jinja-Templates mit gemeinsamem Footer
backend/static/         Stylesheets
tests/                  Automatische Tests
docs/                   Anweisungen, Roadmap und Timeline
```

## Lizenz

Noch festzulegen. Bis eine Lizenzdatei hinzugefügt wurde, wird keine Nutzungslizenz für Dritte eingeräumt. Hochschulinterne Anforderungen und mögliche Rechte an archivierten Inhalten sind vor Veröffentlichung zu klären.

Die Eingabeprüfung der Installations- und Update-Skripte entfernt jetzt Leerzeichen am Rand und Wagenrückläufe. 14 isolierte Eingabetests bestehen; der erfolgreiche Serverbetrieb wurde inzwischen vom User bestätigt (siehe [Timeline](docs/timeline.md)).
