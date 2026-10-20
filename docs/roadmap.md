# Roadmap

WI-PlanArchiv wird schrittweise von der Konzeption zur zuverlässig betriebenen Archivierung von Vorlesungsplänen entwickelt. Diese Roadmap beschreibt geplante Ergebnisse; abgeschlossene Änderungen werden in der [Timeline](timeline.md) dokumentiert.

## Aktueller Stand

Konzept / Entwicklungsstart. Die aktuelle Version ist in [version.py](../version.py) festgehalten und lautet `V0.0.1`. Projektanweisungen und Dokumentation liegen vor; Webanwendung, Datenimport und Live-Quellzugriff sind noch nicht implementiert bzw. verifiziert. Alle folgenden Umsetzungsschritte sind offen.

## Versionsplanung

Die Versionsziele sind Vorschläge anhand der erreichten Meilensteine. `x` bezeichnet die vom User gewählte dritte Stelle. Eine Versionsanhebung erfolgt erst nach Umsetzung und Prüfung, nicht allein durch die Planung. Die Webseite übernimmt die aktuelle Version aus `version.py` in ihren gemeinsamen Footer.

| Phase | Versionsziel | Ergebnis |
| --- | --- | --- |
| Grundlagen | `V0.0.x` | Startfähiges Projektgerüst und sichere Konfiguration |
| M0/M1 | `V0.1.x` | Verifizierte Quellenanalyse und funktionierender Import-Prototyp |
| M2 | `V0.2.x` | Dauerhafte Speicherung und sichere Snapshot-Veröffentlichung |
| M3 | `V0.3.x` | Nutzbare Stundenplanansicht |
| M4 | `V0.4.x` | Administration und automatisierter Betrieb |
| M5 | `V0.5.x` | Optionale Erweiterungen nach dem stabilen Kern |
| MVP-Freigabe | `V1.0.x` | Vollständig umgesetzter und geprüfter MVP einschließlich Betrieb und Wiederherstellung |

Die MVP-Freigabe setzt M0 bis M4 und die unten genannten Betriebskriterien voraus. Optionale Erweiterungen aus M5 sind dafür nicht erforderlich und können vor oder nach der Freigabe umgesetzt werden.

## Grundlagen – Projektgerüst

- Flask-Projekt mit getrennten Modulen für Import, Parser, Speicherung, Scheduler und Web-Routen anlegen.
- Konfiguration über Umgebungsvariablen vorsehen; `.env.example` enthält `LSF_BASE_URL=` ohne Wert. Lokale Konfiguration und Laufzeitdaten von Git ausschließen.
- Gemeinsames Seitenlayout mit Version aus `version.py` im Footer erstellen.
- Lokale Installation, Start und Testausführung dokumentieren.

**Abschlusskriterium:** Die Anwendung startet lokal ohne Quellzugriff, zeigt die aktuelle Version an und benötigt keine vertraulichen Daten im Repository.

## M0 – Quellenanalyse

- Berechtigten Zugang und repräsentative Quelldaten mit dem Projektverantwortlichen klären; vertrauliche Adressen ausschließlich lokal bereitstellen, siehe [Datenquellenkonfiguration](source-configuration.md).
- Navigationsfluss, Studiengangskennungen, Authentifizierung sowie Semester- und Wochenwechsel untersuchen.
- Datenformate und Abrufmethode verifizieren; Gruppen, Blocktermine und wiederkehrende Termine berücksichtigen.
- Erkenntnisse und offene Fragen in `docs/source-analysis.md` festhalten; freigegebene, anonymisierte Fixtures vorbereiten.

**Abschlusskriterium:** Ein nachvollziehbar geprüfter Abrufweg und eine dokumentierte Grundlage zur Erfassung eines vollständigen Semesters liegen vor. Fiktive Fixtures ermöglichen Vorarbeiten, ersetzen jedoch keine Verifizierung der Quelle.

## M1 – Import-Prototyp

- Einen ausgewählten WI-Studiengang für ein vollständiges Semester abrufen und in strukturierte JSON-Daten normalisieren.
- Timeouts, begrenzte Wiederholungen und schonende Abrufe umsetzen; vertrauliche Adressen aus Diagnosen fernhalten.
- Parser gegen freigegebene Fixtures und Grenzfälle prüfen, insbesondere deutsche Datumsangaben, ISO-Wochen, Jahreswechsel und Zeitzonen.
- Fehlende Angaben und unvollständige Importe erkennen und kennzeichnen.

**Abschlusskriterium:** Ein vollständiger Import ist reproduzierbar; Fehlerfälle werden erkannt und die normalisierten Ergebnisse durch Tests belegt.

## M2 – Persistenz und Archivintegrität

- SQLite-Datenmodell mit Migrationen für Studiengänge, Semester, Pläne, Importläufe, Snapshots und Termine implementieren.
- Snapshots zunächst vorläufig speichern und erst nach erfolgreicher Validierung atomar veröffentlichen.
- Identische Inhalte erkennen und unnötige Versionen vermeiden.
- Archivdateien außerhalb des Webroots ablegen; Aufbewahrung mit Schutz des letzten gültigen Stands umsetzen.

**Abschlusskriterium:** Tests belegen, dass fehlgeschlagene, leere oder unvollständige Importe keinen gültigen Stand überschreiben und gleiche Inhalte keine neuen Versionen erzeugen.

## M3 – Web-MVP

- Responsive Wochenansicht und Listenansicht für schmale Bildschirme erstellen.
- Studiengang, Fachsemester, Hochschulsemester und Kalenderwoche filterbar machen.
- Veranstaltungsdetails, Archivstand und Zeitpunkt der letzten erfolgreichen Sicherung anzeigen.
- Fehlerzustände, veraltete Stände und fehlende Daten verständlich darstellen; Tastaturbedienung und barrierearme Darstellung berücksichtigen.

**Abschlusskriterium:** Gespeicherte Pläne sind auf Desktop und Smartphone nutzbar; Filter und Statusanzeigen sind geprüft. Die Oberfläche stellt Archivdaten korrekt als solche dar.

## M4 – Administration und Automatisierung

- Adminbereich mit Anmeldung, Berechtigungsprüfung, CSRF-Schutz und Eingabevalidierung absichern.
- Archivierung (`backup_enabled`) und Anzeige (`display_enabled`) getrennt verwalten.
- Manuelle Sicherungen, Importhistorie, Fehlerdiagnosen und Aufbewahrung bereitstellen.
- Eine Scheduler-Strategie wählen, Zeitpläne in `Europe/Berlin` berücksichtigen und parallele doppelte Jobs verhindern.

**Abschlusskriterium:** Berechtigungen und Konfiguration sind getestet; geplante und manuelle Sicherungen funktionieren nachvollziehbar und ohne doppelte Ausführung.

## MVP-Freigabe – Betrieb und Wiederherstellung

- Deployment im Debian-LXC auf Proxmox mit Gunicorn und gegebenenfalls Nginx dokumentieren.
- Erreichbarkeit der Quelle aus der Betriebsumgebung und Berechtigungen der Archivansicht prüfen.
- Unabhängige Backups von Datenbank und Archivdateien einrichten und Wiederherstellung praktisch testen.
- Sicherheits- und Datenschutzanforderungen, Fehlerverhalten sowie vollständigen Ablauf von Import bis Anzeige prüfen.

**Abschlusskriterium:** M0 bis M4 sind abgeschlossen; Installation, automatisierter Betrieb, Fehlerbehandlung und Restore sind dokumentiert und erfolgreich geprüft.

## M5 – Optionale Erweiterungen

- Unterschiede zwischen Archivständen anzeigen: neue, verschobene, geänderte und entfallene Termine.
- Suche sowie PDF- und iCal-Export ergänzen.
- Weitere Studiengänge nach Prüfung der Quelle unterstützen.
- Eine archivierte Originaldarstellung bei Bedarf sicher isoliert oder sanitisiert anbieten.

**Abschlusskriterium:** Jede Erweiterung besitzt passende Tests und Dokumentation und erhält die Integritätsgarantien des Archivs.

## Pflege und nächste Schritte

Als Nächstes wird das Projektgerüst umgesetzt. Die Quellenanalyse folgt, sobald berechtigter Zugriff und geeignete Quelldaten vorliegen. Zeitliche Zusagen werden erst nach Klärung dieser Abhängigkeiten getroffen.

Bei jeder Änderung die [Timeline](timeline.md) mit Version, Beschreibung, Prüfstatus und Commit-Kurzbeschreibung ergänzen. Versionsvorschläge werden anhand des tatsächlich erreichten Stands bewertet; die dritte Stelle bleibt dem User vorbehalten.
