# Roadmap

WI-PlanArchiv wird schrittweise von der Konzeption zur zuverlässig betriebenen Archivierung von Vorlesungsplänen entwickelt. Diese Roadmap beschreibt geplante Ergebnisse; abgeschlossene Änderungen werden in der [Timeline](timeline.md) dokumentiert.

## Aktueller Stand

Konzept / Entwicklungsstart. Die aktuelle Version ist in [version.py](../version.py) festgehalten und lautet `V0.0.18`. Das Flask-Grundgerüst mit Startseite, Umgebungs-Konfiguration und zentraler Version im Footer ist implementiert. Laut Nutzerprotokoll vom 2026-10-20 bestehen im Debian-13-LXC alle drei Tests; systemd-Einrichtung und lokale HTTP-Prüfung sind erfolgreich. Der User bestätigt nach erneutem Test den laufenden Server und Zugriff im internen Netz. Der erste Live-Quellzugriff für Studiengangsuche, Plan und Wochenwechsel ist verifiziert; ein automatisierter Datenimport ist noch nicht implementiert. Ein interaktives Installationsskript für Debian-13-LXC mit automatischem Git-Bezug und systemd und eine [Installationsanleitung](install.md) liegen vor; die Erstinstallation im Zielcontainer ist durch das Nutzerprotokoll bestätigt. Ein separates Update-Skript mit vorbereiteten Releases, Sicherung und Rückkehr zum alten Anwendungsstand liegt vor; der erfolgreiche Update-Praxistest ist durch den User bestätigt; ein absichtlich ausgelöster Fehler mit Rollback wurde im LXC noch nicht nachgewiesen. M0 ist in der [Quellenanalyse](source-analysis.md) begonnen: HTTP-Abruf, Wochenwechsel und zwei Detailseiten sind geprüft. Ein Detailparser mit fiktiver Testgrundlage liegt vor; Sonderfälle, Quellidentität und Semester-Vollständigkeit bleiben offen; M1 bis M5 bleiben offen.

Die neue Kalendervorschau erzeugt UTC-Termine und prüft Ausfälle; ein separater Wochenabgleich erkennt Lücken und Fehler. Sonderregeln und Quellzuordnung sind technisch vorbereitet, aber noch nicht live verifiziert. M0/M1 bleiben offen. Siehe [Entscheidung zur Kalendervorschau](decisions/002-kalendervorschau.md).

Ein begrenzter HTTP-Abrufadapter und seine Verbindung zum Detailparser sind implementiert. Der manuelle [Quelltest](source-check.md) ist im Container ausführbar; die Implementierung ist mit simulierten Antworten sowie dem Studiengangsablauf live geprüft. Die generische [Formularnavigation](form-navigation.md) ist implementiert und mit fiktiven Daten getestet. Die konkrete Studiengangsnavigation ist in V0.0.7 live geprüft; Die [Wochennavigation](week-navigation.md) ist in V0.0.8 für zwei Wochen live geprüft und mit dem Abgleich eines unabhängig vorgegebenen Zeitraums verbunden. Vollständiger Semesterimport und Sonderfallprüfung stehen noch aus.

Eine [Detailstichprobe](detail-sample.md) verbindet erkannte Veranstaltungslinks mit Semesterprüfung, Parser und Normalisierung. Gleiche Ziele werden innerhalb des Prüflaufs einmal abgerufen. Zwei Details sind live geprüft; dauerhafte Quellidentität und vollständige Detailerfassung bleiben offen.

Der [gemeinsame Import-Prüflauf](import-check.md) verbindet Navigation, Wochenabgleich und Detailstichprobe mit einem bereinigten JSON-Bericht. Zwei Wochen und zwei Details wurden gemeinsam live geprüft. Vollständigkeit und Archivveröffentlichung sind weiterhin gesperrt; offene Punkte stehen im Bericht.

Ein [live belegter Sonderfall](special-dates.md) aus wöchentlicher Serie, Einzeltermin und Ausfallhinweis wird in V0.0.11 unterstützt. Ausfälle bleiben separat erhalten. Stabile Quellidentität, weitere Sonderfälle und vollständige Semestererfassung sind weiterhin offen; M0/M1 sind noch nicht abgeschlossen.

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

Als Nächstes werden anhand der [Quellenanalyse](source-analysis.md) echte Sonderfälle ergänzt und der HTTP-Abrufadapter mit belastbarer Quellidentität und Vollständigkeitsprüfung vorbereitet. Zeitliche Zusagen werden erst nach Klärung dieser Abhängigkeiten getroffen.

Bei jeder Änderung die [Timeline](timeline.md) mit Version, Beschreibung, Prüfstatus und Commit-Kurzbeschreibung ergänzen. Versionsvorschläge werden anhand des tatsächlich erreichten Stands bewertet; die dritte Stelle bleibt dem User vorbehalten.

Die Eingabeprüfung der Installations- und Update-Skripte entfernt jetzt Leerzeichen am Rand und Wagenrückläufe. 14 isolierte Eingabetests bestehen; die erneute Prüfung im Zielcontainer steht aus (siehe [Timeline](timeline.md)).

## Ergänzung V0.0.12 – Quellidentität

Eine [konfigurierbare Veranstaltungskennung](source-identity.md) ordnet Detailziele unabhängig von Sitzungswerten zu. Der Vergleich in getrennten Sitzungen bestätigt die beobachtete Stabilität. Ohne lokale Konfiguration bleibt die laufbezogene Zuordnung aktiv. Studiengangs-/Prüfungsordnungszuordnung, weitere Sonderfälle und vollständige Semestererfassung bleiben offen. Nächster Schritt: die vollständige Semestererfassung einschließlich zusätzlicher Ansichten absichern, danach Persistenz und Webanzeige.

## Ergänzung V0.0.13 – Semesteransichten

Die [zusätzliche Semesterprüfung](semester-check.md) ist implementiert und live geprüft: 54 eindeutige Detailziele in der Semesteransicht; keine erkannten Blöcke in der Block-/Einzelterminansicht. Die leere Ansicht bleibt ausdrücklich ungeklärt. Der neue Befehl prüft Auswahl und unverändertes Wochenangebot, erfasst zusätzliche Kennungen und veröffentlicht keine Daten. Nächster Schritt: Semesterzuordnung und vollständige Detailerfassung auf Basis dieser Ziele absichern; Wochenenden und die leere Zusatzansicht bleiben offen. M0/M1 sind noch nicht abgeschlossen.

## Ergänzung V0.0.14 – Vollständige Prüfung bekannter Detailziele

Der Semesterprüfbefehl unterstützt jetzt `--details`: Ziele beider Ansichten werden anhand ihrer Kennungen vereinigt und innerhalb eines ausdrücklichen Budgets vollständig geprüft. Jede Detailseite muss zum vorgegebenen Semester passen. Budgetüberschreitungen führen vor dem ersten Detailabruf zum Abbruch, Abruf- und Parserfehler liefern keine erfolgreiche Teilprüfung. Unbekannte Sonderfälle bleiben prüfpflichtig. Die Prüfung aller bekannten Ziele beweist noch keine vollständige Quellerfassung; leere Zusatzansicht, Wochenenden und Studiengangszuordnung bleiben offen. Siehe [Semesterprüfung](semester-check.md).


**Live-Prüfung V0.0.14 (2026-10-20):** Alle 54 bekannten Detailziele wurden mit insgesamt 62 HTTP-Anfragen geparst und gegen das erwartete Semester geprüft. 21 Details bleiben wegen Normalisierung oder fachlicher Prüfhinweise offen. Es wurden keine Rohseiten oder vertraulichen Quellwerte gespeichert. Nächster Schritt: diese offenen Normalisierungsfälle gezielt untersuchen und unterstützen; Vollständigkeit der Quelle weiterhin separat nachweisen.

## Ergänzung V0.0.15 – Ausfallnormalisierung

Die 21 bisherigen Prüffälle wurden aufgeschlüsselt: 19 technisch blockierte Normalisierungen und zwei erzeugte Vorschauen mit Prüfhinweisen. Beobachtet wurden mehrere aufeinanderfolgende Ausfallangaben, fehlende Hinweistextwerte und Raumnummern, die bisher als Datumsangaben gewertet wurden. Diese Formate werden nun verarbeitet; Ausfälle und Hinweise bleiben erhalten. Mögliche Ersatztermine werden nicht automatisch abgeleitet. Der Semesterbericht unterscheidet erzeugte Vorschauen, blockierte Details und Vorschauen mit fachlichen Prüfhinweisen. Vollständigkeit und Archivveröffentlichung bleiben gesperrt.


**Live-Ergebnis V0.0.15:** 54 bekannte Details geprüft, 50 Vorschauen erzeugt; davon 17 mit fachlichen Prüfhinweisen. Die Zahl technisch blockierter Details sinkt von 19 auf vier. Abschließender Prüflauf: 62 HTTP-Anfragen. Nächster Schritt: die verbleibenden Bemerkungs-/Verlegungsfälle gezielt klären und den Vollständigkeitsnachweis der Quelle weiterführen. Prüfhinweise werden nicht allein wegen erfolgreicher Normalisierung entfernt.

## Ergänzung V0.0.16 – Verlegungshinweise erhalten

Explizite Ausfalldaten können jetzt auch dann normalisiert werden, wenn der zugehörige Hinweis weitere Datums- oder Zeitangaben enthält. Der Hinweis bleibt unverändert erhalten und wird als `replacement_reference_requires_review` markiert; daraus wird weder ein Ersatztermin noch eine Verknüpfung mit vorhandenen Terminen erzeugt. Allgemeine ungeklärte Serienbemerkungen bleiben gesperrt. Ihre vollständig geparsten Veranstaltungsdaten werden im internen Ergebnis als `unresolved_course` für die weitere Prüfung erhalten, ausschließlich im Arbeitsspeicher und außerhalb des CLI-Berichts. Vollständigkeit und Veröffentlichung bleiben gesperrt.

**Live-Ergebnis V0.0.16:** 54 Details geprüft, 51 Vorschauen erzeugt, davon 18 mit fachlichen Prüfhinweisen. Drei Veranstaltungen mit insgesamt vier Serienbemerkungen bleiben technisch gesperrt; ihre geparsten Daten sind im internen Ergebnis erhalten. Ein Prüflauf mit 62 HTTP-Anfragen. Nächster Schritt: die Bedeutung dieser Serienbemerkungen gezielt klären; zusätzlich bleiben leere Zusatzansicht, Wochenenden und Vollständigkeit der Quelle zu prüfen.

### Fortsetzung innerhalb V0.0.16 – Serienbemerkungen

Die vier Bemerkungen der drei zuvor gesperrten Veranstaltungen sind eingeordnet: zweimal eine Vorlesungskennzeichnung, einmal die Kennzeichnung eines expliziten Einzeltermins als Nachholtermin und einmal ein Laborraumhinweis. Die vermeintliche Datumsangabe war eine Raumkennung. Diese drei eng begrenzten Formate werden jetzt unverändert als `series_annotations` mit Serienindex erhalten. Sie ändern keine Termine und überschreiben kein Raumfeld. Alle Hinweise bleiben prüfpflichtig; beim Laborraumhinweis besteht eine Abweichung zum Raumfeld. Unbekannte Bemerkungen und Durchführungshinweise blockieren weiterhin die ganze Vorschau. Nächster Schritt: vollständigen Semesterumfang einschließlich Wochenenden und leerer Zusatzansicht nachweisen; danach sichere Speicherung und Webanzeige.

## Ergänzung V0.0.17 – Zusätzliche Veranstaltungsblöcke

Die bisher als ungeklärt leer gemeldete Block-/Einzelterminansicht enthält tatsächlich 98 Veranstaltungsblöcke einer zweiten Tabellenklasse. Die achtzeilige Struktur mit einem Detailverweis in der Kopfzeile wurde live geprüft und wird nun gemeinsam mit der bisherigen Variante erkannt. Auch die Semesteransicht enthält diese Variante: 162 Blöcke und 66 eindeutige Ziele statt zuvor 54. Die Zusatzansicht enthält 33 eindeutige Ziele, alle bereits in der Semesteransicht vorhanden. Der Sammler übersah bisher zwölf Ziele; die frühere Zahl 54 ist kein Vollständigkeitsnachweis.

Beide Ansichten zeigen Montag bis Freitag. Im untersuchten Auswahlformular wurde kein Wochenendschalter gefunden. Der Bericht erfasst sichtbare Wochentage nur als Beobachtung, nicht als Nachweis fehlender Wochenendveranstaltungen. Vollständigkeit und Veröffentlichung bleiben gesperrt. Für die 66 Ziele muss das bisherige Standard-Detailbudget von 60 ausdrücklich erhöht werden, beispielsweise auf 80.


**Abschließender Live-Lauf V0.0.17:** 74 HTTP-Anfragen, 66 Details geparst, 64 Vorschauen erzeugt (21 mit fachlichen Prüfhinweisen), zwei neu erfasste Details technisch blockiert. Keine Wochenendtermine in den erzeugten Vorschauen; dies ist kein Nachweis für die Abwesenheit weiterer Wochenendveranstaltungen. Nächster Schritt: die zwei neuen Normalisierungsfälle klären und die verbleibenden Vollständigkeitskriterien absichern.

## Ergänzung V0.0.18 – Logo, curl-freier Betrieb und Klausurzeiten

Das bestehende Logo wird lokal und responsiv im gemeinsamen Seitenkopf angezeigt. Installations- und Update-Skript benötigen kein curl mehr: wget dient im Schnellstart zum Download; lokale Gesundheitsprüfungen verwenden Python ohne Proxy und mit Timeout, Größenlimit und exakter Versionsprüfung beim Update. Die neue Skriptfassung ist lokal getestet, noch nicht im Ziel-LXC ausgeführt.

Die zwei offenen Normalisierungsfälle wurden untersucht. Eine Einzelterminserie enthält einen eindeutigen Klausurzeit-Hinweis innerhalb des größeren Tabellenzeitraums. Diese eng begrenzte Form wird nun übernommen; Originalzeiten, Hinweis und fachlicher Prüfstatus bleiben erhalten. Die Begrüßungs-/Einführungsbemerkungen der anderen Veranstaltung bleiben blockierend und intern erhalten. Abschließender gezielter Live-Test: zwei Details, eine Vorschau mit Klausurzeit-Annotation und ein ungeklärtes Detail, zehn HTTP-Anfragen. Kein erneuter vollständiger Lauf nach der Änderung. Wochenenden und vollständiger Semesterumfang bleiben separat nachzuweisen.
