# Quellenanalyse – M0

## Stand

Die Anwendung und das Update wurden vom Projektverantwortlichen erfolgreich getestet; der Server ist im internen Netz erreichbar. Dies bestätigt den Anwendungsbetrieb, noch nicht den Zugriff auf die LSF-Datenquelle.

Am 2026-10-20 wurden Einstieg, Studiengangsauswahl, Plananzeige und zwei Wochenwechsel per HTTP erfolgreich geprüft. Die vertrauliche Einstiegsadresse wurde vom User bereitgestellt und ausschließlich im Arbeitsspeicher verwendet. Rohseiten und Sitzungsdaten wurden nicht gespeichert. Die aktuelle Anwendungsversion lautet `V0.0.3`. M0 ist begonnen, aber noch nicht vollständig abgeschlossen.

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
| Terminstruktur | HTML-Plan mit Tagesüberschriften und verschachtelten Tabellen vorhanden | Feldzuordnung und Details noch zu prüfen |
| Sonderfälle | Ferienhinweise in der Jahreswechselwoche sichtbar | Gruppen, Ausfälle, Block- und Einzeltermine noch offen |
| Semesterwechsel | Nur voreingestelltes Wintersemester untersucht | Offen |

Die sichtbaren Tagesüberschriften umfassen Montag bis Freitag. Daraus darf nicht geschlossen werden, dass es keine Wochenendtermine gibt. Die zusätzlichen Semesteransichten müssen daraufhin geprüft werden. Die 26 angebotenen Wochen sind ein Ausgangspunkt für den späteren Vollständigkeitsabgleich, noch kein Nachweis eines vollständigen Imports.

Ergebnisse jeweils mit Testdatum, geprüfter Auswahl und Beobachtung ergänzen. Reale Quelladressen, URL-Bestandteile, Cookies und personenbezogene Testdaten dürfen nicht in das Repository gelangen. Technische Kennungen oder Navigationsparameter nur soweit dokumentieren, wie dies ohne vertrauliche URL-Bestandteile möglich ist.

## Grundlage für Parser-Tests

Nach Sichtung und Freigabe repräsentative, anonymisierte Fixtures unter `tests/fixtures/` vorbereiten. Vor Aufnahme sämtliche Adressen, Links, Formulardaten, eingebetteten Skriptdaten, Sitzungswerte und personenbezogenen Inhalte prüfen. Originalantworten bleiben außerhalb des Repositorys.

Die Fixtures sollen mindestens einen regulären Termin, eine leere Woche und einen tatsächlich in der Quelle beobachteten Sonderfall abdecken. Erwartete Ergebnisse werden anhand der geprüften Quelle festgelegt. Eine leere Woche darf nicht mit einem fehlgeschlagenen Abruf oder einer Anmeldeseite verwechselt werden.

## Abschluss und Übergang zu M1

M0 ist abgeschlossen, wenn ein geprüfter Navigations- und Abrufweg, eine freigegebene Testgrundlage und ein nachvollziehbares Verfahren zur Prüfung des vollständigen Semesterumfangs vorliegen. Offene Einschränkungen müssen ausdrücklich dokumentiert sein.

Danach entsteht der Import-Prototyp für genau den geprüften Studiengang und Zeitraum. Die Versionslinie `V0.1.x` wird erst anhand der erreichten Ergebnisse vorgeschlagen; die dritte Stelle bestimmt der User.

## Nächster Umsetzungsschritt

1. Feldzuordnung anhand einer regulären Veranstaltung sowie Detailansicht untersuchen und Block-/Einzeltermine mit der Wochenansicht abgleichen.
2. Eine kleine, bereinigte Testgrundlage erstellen; keine echten Quelladressen, Sitzungswerte oder personenbezogenen Angaben übernehmen.
3. Einen HTTP-Abrufadapter mit Laufzeitkonfiguration und temporärer Sitzung umsetzen. Formularziele und Navigationswerte aus der Antwort lesen, statt ungeprüfte Endpunkte fest einzubauen.
4. Die erwarteten Wochen und tatsächlich verarbeiteten Wochen explizit vergleichen. Anmeldeseiten, Fehlerseiten und unvollständige Antworten dürfen nicht als leere Pläne gelten.
