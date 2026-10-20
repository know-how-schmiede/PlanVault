# Quellenanalyse – M0

## Stand

Die Anwendung und das Update wurden vom Projektverantwortlichen erfolgreich getestet; der Server ist im internen Netz erreichbar. Dies bestätigt den Anwendungsbetrieb, noch nicht den Zugriff auf die LSF-Datenquelle.

Am 2026-10-20 wurden Einstieg, Studiengangsauswahl, Plananzeige und zwei Wochenwechsel per HTTP erfolgreich geprüft. Die vertrauliche Einstiegsadresse wurde vom User bereitgestellt und ausschließlich im Arbeitsspeicher verwendet. Rohseiten und Sitzungsdaten wurden nicht gespeichert. Anschließend wurden eine reguläre Veranstaltung und eine Laborveranstaltung mit dem ersten Detailparser erfolgreich geprüft (eine bzw. zwei Terminserien). Eine vollständig fiktiv befüllte Testdatei bildet die beobachtete Tabellenstruktur nach. Die aktuelle Anwendungsversion lautet `V0.0.10`. M0 ist begonnen, aber noch nicht vollständig abgeschlossen.

## Geprüfte Auswahl und Rahmenbedingungen

- Hochschulsemester: Wintersemester 2026/27, auf der Einstiegsseite voreingestellt.
- Exemplarischer Studiengang: Wirtschaftsingenieurwesen / Management und Technik, Prüfungsordnung 2024. Diese Auswahl dient der Analyse und legt noch keine Standardauswahl für die spätere Archivierung fest.
- Suche nach Wirtschaftsingenieurwesen liefert mehrere Studiengänge und Prüfungsordnungen; Studiengangsname allein genügt daher nicht als eindeutige Zuordnung.
- Keine Anmeldung für die getestete Suche und Plananzeige erforderlich. Die Quelle zeigt einen Notbetrieb-Hinweis: Studiengangpläne sind ohne Anmeldung abrufbar; eine Anmeldung für Studierende ist derzeit nicht möglich. Diese Beobachtung gilt für den Testzeitpunkt.
- Keine Fachsemestergrenzen, Kategorie- oder Studienphasenfilter gesetzt. Die Quelle warnt ausdrücklich, dass Semestergrenzen Veranstaltungen ohne entsprechende Zuordnung ausblenden können.
- Aufruf aus der aktuellen Arbeitsumgebung erfolgreich. Der Zugriff aus dem produktiven LXC ist separat zu prüfen; aus dem erfolgreichen Abruf folgt keine Aussage über alle anderen Netzwerke.

Für den vertraulichen Umgang mit der Quelle gelten die [Konfigurationshinweise](source-configuration.md). Zugangsdaten waren für die bisherigen Tests nicht erforderlich.

## Untersuchung und Nachweise

| Untersuchung | Beobachtung / Nachweis | Status |
| --- | --- | --- |
| Erreichbarkeit | Einstieg, Suche und Plan liefern HTTP 200 | Geprüft aus der Arbeitsumgebung |
| Anmeldung und Sitzung | Suche und Plan ohne Login; Cookies nur in einer temporären HTTP-Sitzung gehalten | Grundablauf geprüft; Sitzungsablauf noch offen |
| Studiengangsauswahl | Suchformular → Trefferliste → Auswahl des Studiengangs → Suchformular mit Auswahl → Plan | Geprüft |
| Datenbereitstellung | Plan und Wochenauswahl werden im gelieferten HTML dargestellt | HTTP genügt für den geprüften Ablauf |
| Wochenwechsel | KW 44 zeigt 26.–30.10.2026; KW 53 zeigt 28.12.2026–01.01.2027 mit Weihnachtsferien-Hinweisen | Geprüft, einschließlich Jahreswechsel |
| Semesterumfang | Auswahl bietet 26 Wochen vom 31.08.2026 bis 28.02.2027 sowie Semester-, Vorlesungszeit- und Blockterminansichten | Auswahl geprüft; vollständige Erfassung noch offen |
| Terminstruktur | Detailseiten mit Titelüberschrift, paarweisen Metadaten und Terminspalten für Tag, Zeit, Rhythmus, Dauer, Raum, Lehrperson, Durchführung, Bemerkung und Ausfälle | An zwei Veranstaltungen geprüft; erster Parser liest eine bzw. zwei Serien |
| Sonderfälle | Ferienhinweise sichtbar; Block-/Einzelterminansicht aufgerufen, dort keine Blöcke nach dem bisher identifizierten Muster erkannt | Noch kein Nachweis für tatsächliche Block-/Einzeltermine, Gruppen oder Ausfälle |
| Semesterwechsel | Nur voreingestelltes Wintersemester untersucht | Offen |

Die sichtbaren Tagesüberschriften umfassen Montag bis Freitag. Daraus darf nicht geschlossen werden, dass es keine Wochenendtermine gibt. Die zusätzlichen Semesteransichten müssen daraufhin geprüft werden. Die 26 angebotenen Wochen sind ein Ausgangspunkt für den späteren Vollständigkeitsabgleich, noch kein Nachweis eines vollständigen Imports.

Ergebnisse jeweils mit Testdatum, geprüfter Auswahl und Beobachtung ergänzen. Reale Quelladressen, URL-Bestandteile, Cookies und personenbezogene Testdaten dürfen nicht in das Repository gelangen. Technische Kennungen oder Navigationsparameter nur soweit dokumentieren, wie dies ohne vertrauliche URL-Bestandteile möglich ist.

## Grundlage für Parser-Tests

Unter `tests/fixtures/course_detail.html` liegt eine auf der geprüften Struktur beruhende, vollständig fiktiv befüllte Testdatei. Sie enthält keine Originaltermine oder realen Identitäten. Weitere repräsentative, anonymisierte Fixtures bei zusätzlichen Beobachtungen ergänzen. Vor Aufnahme sämtliche Adressen, Links, Formulardaten, eingebetteten Skriptdaten, Sitzungswerte und personenbezogenen Inhalte prüfen. Originalantworten bleiben außerhalb des Repositorys.

Die Fixtures sollen mindestens einen regulären Termin, eine leere Woche und einen tatsächlich in der Quelle beobachteten Sonderfall abdecken. Erwartete Ergebnisse werden anhand der geprüften Quelle festgelegt. Eine leere Woche darf nicht mit einem fehlgeschlagenen Abruf oder einer Anmeldeseite verwechselt werden.

## Abschluss und Übergang zu M1

M0 ist abgeschlossen, wenn ein geprüfter Navigations- und Abrufweg, eine freigegebene Testgrundlage und ein nachvollziehbares Verfahren zur Prüfung des vollständigen Semesterumfangs vorliegen. Offene Einschränkungen müssen ausdrücklich dokumentiert sein.

Danach entsteht der Import-Prototyp für genau den geprüften Studiengang und Zeitraum. Die Versionslinie `V0.1.x` wird erst anhand der erreichten Ergebnisse vorgeschlagen; die dritte Stelle bestimmt der User.

## Erster Detailparser

`backend.parser.parse_course_detail(html, expected_semester=...)` liest eine Veranstaltungsdetailseite und liefert Metadaten sowie Terminserien. Der Veranstaltungstitel wird aus der beobachteten Überschrift gelesen; Langtext und Veranstaltungsnummer dürfen fehlen. Eine fehlende Nummer erzeugt einen Prüfhinweis, da der Titel keine stabile Identität garantiert.

Im geprüften regulären Termin steht der Rhythmus `woch`; die Terminzeilen enthalten Start- und Enddatum sowie lokale Tageszeiten. Mehrere Serien werden erhalten. Unbekannte Rhythmen, Bemerkungen, Ausfalltexte und mehrere Termintabellen erzeugen Prüfhinweise. Es findet keine Expansion zu einzelnen Kalenderterminen statt. Die Hintergründe stehen in der [Entscheidung zu Terminserien](decisions/001-terminserien.md).

Am 2026-10-20 bestehen 22 lokale Tests einschließlich der bisherigen App-Tests. Die Parser-Prüfungen umfassen unter anderem fehlende Felder, falsches Semester, ungültige Uhrzeiten und Daten, unbekannte Zeilen, Spaltenumordnung, Ausfallhinweise sowie Login-/Fehlerseiten. Zwei Live-Detailseiten wurden danach erfolgreich gelesen; nur zusammengefasste Ergebnisse wurden ausgegeben.

Der Parser allein bestätigt keine vollständige Semestererfassung. Der Aufruf der Sonderterminansicht ohne erkannte Blöcke darf nicht als Beleg für das Fehlen von Sonderterminen interpretiert werden.

## Nächster Umsetzungsschritt

1. Eine tatsächlich belegte Block-/Einzeltermin- oder Gruppenkonstellation und konkrete Ausfallangaben untersuchen; zusätzliche bereinigte Testdaten ergänzen.
2. Den vorhandenen HTTP-Abrufadapter an die Navigation anbinden. Formularziele und Navigationswerte aus der Antwort lesen, statt ungeprüfte Endpunkte fest einzubauen; Ereignisidentität aus der Navigation belastbar zuordnen.
3. Die erwarteten Wochen und tatsächlich verarbeiteten Wochen explizit vergleichen. Anmeldeseiten, Fehlerseiten und unvollständige Antworten dürfen nicht als leere Pläne gelten.

## Ergänzung V0.0.4

Eine getrennte Normalisierung erstellt jetzt Kalendertermine als JSON-fähige
Vorschau, einschließlich UTC-Umrechnung, lokaler ISO-Wochen und streng geprüfter
Ausfalldaten. Einzel- und Blockregeln sind mit fiktiven Daten getestet und nur
durch explizite Zuordnung nutzbar. Das ist kein neuer Live-Nachweis.

Ein Wochenabgleich für vorgegebene Semestergrenzen liegt vor. Sein Aufrufer muss
erfolgreiche und tatsächlich bestätigte leere Wochen liefern; Fehlantworten,
Lücken und Duplikate verhindern die Bestätigung der Wochenabdeckung.
Die Anbindung an die echte Navigation und die Verifizierung der Quellkennungen
bleiben offen. Ergebnisse sind ausdrücklich keine vollständigen Semesterimporte.
Details und Grenzen: [Kalendervorschau](decisions/002-kalendervorschau.md).

## Ergänzung V0.0.5

Der HTTP-Abrufadapter verwaltet jetzt eine temporäre Sitzung und begrenzt
Anfragen, Wiederholungen, Antwortgrößen und Wartezeiten. Navigation außerhalb
des konfigurierten HTTPS-Origins wird abgelehnt. Der Abruf einer beobachteten
Detailseite ist mit Parser und Normalisierung verbunden.

Der neue [manuelle Quelltest](source-check.md) prüft die konfigurierte
Einstiegsseite aus der jeweiligen Laufzeitumgebung. Die Implementierung ist
mit simulierten Antworten getestet; ein neuer Live-Nachweis liegt nicht vor.
Studiengangsauswahl, Wochen-Navigation und Quellkennungen sind weiterhin
gesondert zu verifizieren und anzubinden.

## Ergänzung V0.0.6

Eine generische [Formularnavigation](form-navigation.md) liest beobachtete Formulare, prüft Auswahlwerte und sendet GET/POST über die bestehende Sitzung. 106 lokale Tests bestehen. Die Zuordnung zu tatsächlichen LSF-Formularen und Trefferlinks sowie der vollständige Semesterablauf sind weiterhin offen; es gab keine neuen Live-Abrufe.

## Ergänzung V0.0.7

Die neue Implementierung hat am 2026-10-20 den vollständigen Navigationsweg vom Einstieg über die Studiengangssuche und den eindeutigen Treffer bis zur Planantwort live durchlaufen. Geprüft wurde die bereits dokumentierte Auswahl mit Prüfungsordnung 2024. Sichtbare Beschriftungen und label/for-Zuordnungen liefern die Formulardaten zur Laufzeit; keine echten Feldnamen oder Navigationsparameter sind im Repository gespeichert.

Normale Fieldsets, gleichwertige doppelte Suchschaltflächen und die schreibgeschützte Studiengangsanzeige ohne Feldnamen wurden berücksichtigt. Der erfolgreiche Ablauf benötigte sechs Anfragen einschließlich Weiterleitungen. 53 Blöcke des bekannten Veranstaltungsmusters wurden erkannt; daraus folgt keine Zahl eindeutiger Veranstaltungen oder vollständige Semesterabdeckung. 122 lokale Tests bestehen. Der neue Befehl [source-plan-check](source-check.md) erlaubt den manuellen Test im LXC; dieser Zielcontainer-Test und die automatisierte Wochennavigation bleiben offen.

## Ergänzung V0.0.8

Die [Wochennavigation](week-navigation.md) liest datierte Auswahloptionen und verwendet die beobachtete Schaltfläche zum Anzeigen. Wochennummer, ISO-Jahr, Datumsbereich, ausgewählte Woche und die fünf sichtbaren Tagesüberschriften werden geprüft. Ein unabhängiger Prüfzeitraum bestimmt die erwartete Wochenabdeckung.

Live am 2026-10-20: 26 angebotene Wochen; KW 44/2026 strukturell passend, KW 53/2026 mit prüfpflichtigen Ferienhinweisen. Acht HTTP-Anfragen einschließlich Studiengangsnavigation. 24 Wochen bleiben fehlend. 146 lokale Tests bestehen. Keine Rohseiten gespeichert; vollständige Erfassung, Wochenenden, Sonderansichten und Veranstaltungsdetails bleiben offen.

## Ergänzung V0.0.9

Die [Detailstichprobe](detail-sample.md) liest genau einen Veranstaltungslink aus der ersten Zeile der beobachteten achtzeiligen Blocktabelle. Raumlinks werden getrennt behandelt. Gleiche absolute Ziele werden innerhalb des Prüflaufs zusammengefasst; dies ist keine dauerhafte Veranstaltungsidentität.

Live am 2026-10-20: 53 Blöcke, 47 unterschiedliche Detailziele, zwei geprüfte Details mit einer beziehungsweise zwei Serien und 15 beziehungsweise 16 Vorschauterminen. 45 Ziele blieben ungeprüft. Acht HTTP-Anfragen einschließlich Studiengangsnavigation; keine Rohseiten gespeichert. 166 lokale Tests bestehen. Der Befehl source-details-check ermöglicht eine begrenzte Stichprobe aus einer ausdrücklich gewählten Woche; keine Archivveröffentlichung.

## Ergänzung V0.0.10

Der [gemeinsame Import-Prüflauf](import-check.md) verbindet Wochenabgleich und Detailstichprobe in einer Sitzung. Gleiche Detailziele aus mehreren Wochen werden vor dem Abruf zusammengeführt. Bereinigte Berichte enthalten Lauf-ID, Zeitstempel, Version, Phasen, Anzahlen und offene Punkte, jedoch keine Quelldaten oder Veranstaltungsinhalte.

Live am 2026-10-20: KW 43/2026 und KW 44/2026 strukturell passend, 51 unterschiedliche Detailziele, zwei geprüft; 24 Wochen und 49 Ziele bleiben offen. Zehn HTTP-Anfragen. 178 lokale Tests erfolgreich. Keine Rohseiten gespeichert, keine Archivveröffentlichung. Dauerhafte Quellidentität und fachliche Semester-Vollständigkeit bleiben zwingende offene Voraussetzungen.
