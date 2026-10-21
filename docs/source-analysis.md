# Quellenanalyse – M0

## Stand

Die Anwendung und das Update wurden vom Projektverantwortlichen erfolgreich getestet; der Server ist im internen Netz erreichbar. Dies bestätigt den Anwendungsbetrieb, noch nicht den Zugriff auf die LSF-Datenquelle.

Am 2026-10-20 wurden Einstieg, Studiengangsauswahl, Plananzeige und zwei Wochenwechsel per HTTP erfolgreich geprüft. Die vertrauliche Einstiegsadresse wurde vom User bereitgestellt und ausschließlich im Arbeitsspeicher verwendet. Rohseiten und Sitzungsdaten wurden nicht gespeichert. Anschließend wurden eine reguläre Veranstaltung und eine Laborveranstaltung mit dem ersten Detailparser erfolgreich geprüft (eine bzw. zwei Terminserien). Eine vollständig fiktiv befüllte Testdatei bildet die beobachtete Tabellenstruktur nach. Die aktuelle Anwendungsversion lautet `V0.0.18`. M0 ist begonnen, aber noch nicht vollständig abgeschlossen.

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
| Sonderfälle | Ferienhinweise sichtbar; zusätzlich Kombination aus wöchentlicher Serie, `Einzel` und Ausfallangabe `Datum: Hinweis` in einer Detailseite geprüft | Einzeltermin und Ausfallformat ab V0.0.11 belegt; Blocktermine, Gruppen und Verlegungsbeziehungen bleiben offen |
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

1. Weitere Block-/Gruppenkonstellationen und Ausfallvarianten untersuchen; der erste Einzeltermin mit Ausfallhinweis ist belegt, die fachliche Beziehung noch offen.
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

## Ergänzung V0.0.11

Drei weitere Detailseiten wurden gezielt geprüft. Eine enthält eine wöchentliche Serie, den Rhythmus Einzel mit genau einem Datum sowie eine Ausfallangabe mit vollständigem Datum und nachfolgendem Hinweis. Die [erweiterte Normalisierung](special-dates.md) verarbeitet diese Struktur und erhält Ausfälle separat, ohne eine Verlegungsbeziehung zu behaupten.

Der abschließende Live-Test ergab zwei Serien, 16 Vorschautermine und einen Ausfall. Sieben HTTP-Anfragen einschließlich Navigation; keine Rohseiten, Quelladressen oder realen Hinweistexte gespeichert. Eine vollständig fiktive Fixture und Grenzfalltests ergänzen den Nachweis. 189 lokale Tests bestehen. Ausfallprüfung und dauerhafte Quellidentität bleiben im Ergebnis ausdrücklich offen.

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

## Ergänzung V0.0.20

Eine begrenzte erneute Detailprüfung lieferte keinen ausreichenden neuen Beleg,
um die offenen Bemerkungen allgemein als reine Zusatzinformationen freizugeben.
Die bisherige Sperre bleibt erhalten; personenbezogene Hinweistexte wurden weder
in Dateien noch in Berichte übernommen. Kein vollständiger Semesterlauf wiederholt.

Der neue lokale Wochentagsabgleich im Semesterbericht zählt Vorschautermine nach
lokalem Datum und macht nicht beobachtete Tage sowie Termine außerhalb sichtbarer
Tagesüberschriften erkennbar. Das ist eine zusätzliche Diagnose, kein Live-Nachweis
vollständiger Wochenenden. Einzelheiten stehen in der Semesterprüfungs-Anleitung.


### V0.0.23 – Offene Importfälle nachvollziehbar ausweisen

Die dokumentierten Einführungsbemerkungen sind weiterhin nicht als unverbindlicher
Zusatztext verifiziert. Statt einer unbelegten Freigabe weist der Semesterbericht
nun die erste konkrete Normalisierungsblockade pro Detail sowie alle fachlichen
Prüfhinweise erfolgreicher Vorschauen aus. Die Diagnose trennt unbekannte Rhythmen,
Durchführungsangaben, Serienbemerkungen, Ausfallformate und Zeitprobleme. Offene
Vollständigkeitsnachweise bleiben separat sichtbar. Kein neuer Quellzugriff;
die noch offenen Live-Fälle können mit dem bestehenden Semesterprüfbefehl gezielt
ausgewertet werden. Siehe [Diagnosebeschreibung](semester-check.md).


## V0.0.24 – Begrenzte Live-Nachprüfung und Raumhinweis

Am 2026-10-21 wurde die bereitgestellte Quelle erneut geprüft. Als ausdrücklich
benannte Arbeitsannahme wurde die WI-Auswahl mit Prüfungsordnung 2020 verwendet;
die sieben sichtbaren WI-Auswahlen wurden nicht insgesamt abgerufen. Dieser
Bestand darf nicht mit dem früheren Lauf mit 66 Details gleichgesetzt werden.

Die Semesteransicht enthält 67 Blöcke mit 21 unterschiedlichen Detailzielen,
die Block-/Einzelterminansicht 48 Blöcke mit zwölf Zielen, alle bereits in der
Semesteransicht vorhanden. 26 Wochen werden angeboten. Die erste Detailprüfung
benötigte 29 HTTP-Anfragen und beobachtete auf allen 21 Detailseiten dieselbe
Semesterbezeichnung für das Wintersemester 2026/27. 20 Vorschauen wurden erzeugt,
eine war durch `unsupported_series_note` blockiert; zwei Vorschauen enthielten
fachlich prüfpflichtige Ausfälle. Der Bestand wurde seriell mit einer Sekunde
Mindestabstand, ohne Wiederholungen und ohne Rohdatenspeicherung abgerufen.

Zwei anschließende gezielte Prüfungen mit jeweils acht HTTP-Anfragen grenzen
die blockierte Bemerkung ein und bestätigen die vollständige Raumhinweisform.
Ein vermeintlicher Datumsbezug war eine durch Punkte gegliederte Raumkennung.
Der Hinweis weicht vom Tabellenraum ab. Die neue Regel erhält beide Angaben
unverändert; der Widerspruch bleibt prüfpflichtig. Aus dem Hinweis wird keine
Terminänderung abgeleitet. Siehe [Sonderfallregel](special-dates.md).

Die Sitzungen verwendeten laufbezogene Linkzuordnung (`identity_mode: run`),
keine konfigurierte dauerhafte Quellkennung. Es wurden keine bisherigen lokalen
Kennungswerte rekonstruiert oder geraten. Die Prüfung lief direkt über die
vorhandenen Adapter und Parser; sie ist kein erfolgreicher Nachweis des gesamten
CLI-Ablaufs mit konfigurierter Kennung. Die Prüfkennungen waren ausschließlich
laufbezogene Platzhalter und keine bestätigte Studiengangs-/Prüfungsordnungszuordnung.

Abschließende Prüfung nach der Erweiterung: 29 HTTP-Anfragen, alle 21 bekannten
Details erfolgreich gegen die erwartete Semesterbezeichnung geprüft, 21 Vorschauen,
309 Termine, keine technisch blockierte Normalisierung. Drei Details bleiben
fachlich prüfpflichtig: zwei wegen Ausfallangaben, eines wegen des Raumhinweises.
Die Wochentagszählung ergibt 79/59/114/33/24/0/0 Termine (Montag bis Sonntag).
Die fehlende dauerhafte Quellidentität wird zusätzlich als
`source_identity_unverified` in der Vollständigkeitsliste ausgewiesen; diese
Ergänzung wurde anschließend lokal getestet.

Montag bis Freitag sind sichtbar; Wochenend- und Semester-Vollständigkeit bleiben
unbewiesen. Kein Archivstand und keine Web-Vorschau wurden geschrieben. Die
früher dokumentierten Einführungsbemerkungen anderer Auswahlen bleiben ungeklärt.
