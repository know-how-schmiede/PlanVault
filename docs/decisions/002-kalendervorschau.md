# 002 – Kalendervorschau und getrennte Vollständigkeitsprüfung

**Stand:** 2026-10-20, Version 0.0.4.

**Fortschreibung V0.0.11:** Nach Live-Nachweis wird `Einzel` mit genau einem
Datum standardmäßig unterstützt. Das beobachtete Format `Datum: Ausfallhinweis`
wird gelesen; Ausfälle bleiben separat samt Hinweis in der Vorschau erhalten.
Die folgenden ursprünglichen Einschränkungen zu Einzelterminen und reinem
Datumsformat werden damit erweitert. Blockregeln und fachliche Freigabe bleiben
offen. Siehe [Sondertermine](../special-dates.md).

**Fortschreibung V0.0.11:** Nach Live-Nachweis wird `Einzel` mit genau einem
Datum standardmäßig unterstützt. Das beobachtete Format `Datum: Ausfallhinweis`
wird gelesen; Ausfälle bleiben separat samt Hinweis in der Vorschau erhalten.
Die folgenden ursprünglichen Einschränkungen zu Einzelterminen und reinem
Datumsformat werden damit erweitert. Blockregeln und fachliche Freigabe bleiben
offen. Siehe [Sondertermine](../special-dates.md).

## Entscheidung

Der HTML-Parser erhält Terminserien weiterhin unverändert. Zusätzlich akzeptiert
er syntaktisch eindeutige Einzeldaten; deren Quellrhythmus bleibt prüfpflichtig.
`backend.parser.normalize_course` erzeugt daraus eine JSON-fähige Vorschau.
Standardmäßig wird nur der bisher beobachtete Rhythmus `woch` als wöchentlich
interpretiert. Einzel- und tägliche Blocktermine benötigen eine ausdrücklich
übergebene Zuordnung `recurrence_rules` zu `single` beziehungsweise `daily`.
Die Tests dieser beiden Regeln sind synthetisch. Sie belegen keine echten
LSF-Codes oder Gruppierungsregeln.

Ausfälle werden nur als vollständige deutsche Datumsangaben mit Komma oder
Semikolon akzeptiert. Jedes Ausfalldatum muss ein Termin der Serie sein.
Freitext, unvollständige Daten, unbekannte Rhythmen und Bemerkungen führen zum
Abbruch der gesamten Normalisierung. Feiertage und Ferien werden nicht
automatisch abgezogen. Auch bei erkannten Ausfällen bleibt ein Prüfhinweis.

Lokale Termine werden mit `Europe/Berlin` nach UTC umgerechnet. Nicht existierende
oder doppeldeutige Uhrzeiten während der Zeitumstellung werden abgelehnt.
ISO-Jahr und ISO-Woche beziehen sich auf das lokale Datum. Unter Windows liefert
die zusätzliche Abhängigkeit `tzdata` die Zeitzonendaten; Debian nutzt die
Systemdaten.

## Identität

`CourseContext` verlangt opake Quell-, Studiengangs- und Prüfungsordnungskennungen
sowie das passende Semester. Daraus entsteht ein deterministischer SHA-256-Schlüssel.
Titel, Räume und Lehrpersonen sind keine Identitätsmerkmale. Quelladressen werden
nicht als Kennungen akzeptiert. Eine fehlende Veranstaltungsnummer wird niemals
durch den Titel ersetzt. Die Kennungen muss der spätere Abrufadapter aus einer
verifizierten Zuordnung liefern; die Vorschau markiert diese Voraussetzung
weiterhin ausdrücklich als zu prüfen. Das Hashing beweist keine Quellidentität.

## Vollständigkeit

`backend.importer.coverage.check_week_coverage` vergleicht die erwarteten
ISO-Wochen eines angegebenen Semesterzeitraums mit den Ergebnissen des Abrufadapters.
Fehlende, unerwartete, doppelte oder fehlgeschlagene Wochen verhindern
`weeks_complete`. Eine leere Woche zählt nur mit `empty_confirmed`, das der
Adapter erst nach Prüfung der korrekten Quellstruktur melden darf.

Ein erfolgreicher Wochenabgleich bestätigt weder vollständige Veranstaltungslisten
noch Sondertermine außerhalb der Wochenansicht. Jede Kalendervorschau behält
`complete=false`. Es gibt weiterhin keine Archivveröffentlichung, keine
automatischen Abrufe und keine neuen Web-Endpunkte. Nächste Voraussetzung ist der
Live-Nachweis für Sonderfälle und die Anbindung eines verifizierten Abrufadapters.
