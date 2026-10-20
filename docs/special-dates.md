# Einzeltermine und Ausfallhinweise – V0.0.11

Eine erweiterte Live-Stichprobe hat eine Detailseite mit einer wöchentlichen
Serie, einem ausdrücklich als `Einzel` bezeichneten Termin und einer Ausfallangabe
geliefert. Der Einzeltermin besitzt genau ein Datum; sein Wochentag passt dazu.
Die Ausfallspalte verwendet die Form `vollständiges Datum: Hinweistext`.

## Umsetzung

- `Einzel` wird jetzt standardmäßig als einzelner Termin unterstützt. Start- und
  Enddatum müssen identisch sein. Mehrtägige Bereiche werden nicht als
  Einzeltermin oder automatisch als Blockveranstaltung interpretiert.
- Ausfallangaben mit einem vollständigen Datum und nachfolgendem Hinweis werden
  gelesen. Das Datum muss zu einem tatsächlich geplanten Termin der Serie passen.
- Das ausgefallene Datum wird aus den Vorschauterminen entfernt und separat
  unter `CalendarPreview.cancellations` erhalten: Serienindex, lokales Datum
  und optionaler Hinweis.
- Mehrere oder unvollständige Datumsangaben im Hinweis werden nicht als Verlegung
  interpretiert. Unbekannte Angaben bleiben ein Fehler beziehungsweise Prüfpunkt.
- Der Einzeltermin wird unabhängig vom Ausfall behandelt. Ein Zusammenhang als
  Ersatztermin wird nicht automatisch behauptet.

Ausfallhinweise behalten `cancellations_require_review`. Die erfolgreiche
Erzeugung einer Vorschau ist somit keine fachliche Freigabe. Detailstichprobe und
gemeinsamer Importbericht berücksichtigen diese Hinweise jetzt einheitlich.
Die Diagnoseberichte enthalten weiterhin nur Status und Anzahlen, keine
Hinweistexte oder Veranstaltungsdaten.

## Nachweis und Grenzen

Am 2026-10-20 wurden drei weitere Detailseiten der bereits untersuchten Auswahl
gezielt geprüft. Zwei enthielten wöchentliche Serien; die dritte den beschriebenen
Sonderfall. Der korrigierte Detailablauf lieferte dort zwei Serien,
16 Vorschautermine und ein separat erhaltenes Ausfalldatum. Der abschließende
Prüflauf benötigte sieben HTTP-Anfragen einschließlich Studiengangsnavigation.
Rohseiten, Quelladressen und reale Hinweistexte wurden nicht gespeichert.

`tests/fixtures/course_exceptions.html` bildet die relevante Struktur mit
ausschließlich fiktiven Werten nach. 189 lokale Tests bestehen. Ungültige Daten,
nicht zur Serie passende Ausfälle, unklare Verlegungen und mehrtägige
„Einzel“-Angaben sind abgedeckt.

Weiter offen bleiben dauerhafte Veranstaltungsidentität, Block-/Gruppenfälle,
Wochenenden und vollständige Semestererfassung. Speicherung und Webanzeige
echter Stundenpläne sind noch nicht implementiert. Bestehende CLI-Prüfbefehle
verwenden die erweiterte Normalisierung automatisch nach dem Update.

## Ergänzung V0.0.15

Die Normalisierung unterstützt nun mehrere durch Leerraum getrennte Angaben
`Datum: Hinweis` sowie `Datum:` ohne Hinweis. Jedes Datum muss ein tatsächlicher
Termin der Serie sein. Doppelte Daten, ungültige Daten oder ein nicht unterstützter
Eintrag verwerfen die gesamte Vorschau. Vorhandene Hinweise bleiben dem jeweiligen
Ausfall zugeordnet; fehlende Hinweise werden als `null` erhalten.

Numerische Raumkennungen mit drei Zahlenteilen werden nicht mehr pauschal als
Kurzdatum behandelt. Vollständige oder abgekürzte zusätzliche Datumsangaben im
Hinweis bleiben prüfpflichtig und blockieren die Normalisierung. Ersatztermine
werden niemals aus Freitext erzeugt. Auch erfolgreich gelesene Ausfälle behalten
`cancellations_require_review`; ein technischer Parsererfolg ist keine fachliche
Freigabe. Tests verwenden ausschließlich fiktive Termine und Raumkennungen.

**Live-Ergebnis V0.0.15:** 54 bekannte Details geprüft, 50 Vorschauen erzeugt; davon 17 mit fachlichen Prüfhinweisen. Die Zahl technisch blockierter Details sinkt von 19 auf vier. Abschließender Prüflauf: 62 HTTP-Anfragen. Nächster Schritt: die verbleibenden Bemerkungs-/Verlegungsfälle gezielt klären und den Vollständigkeitsnachweis der Quelle weiterführen. Prüfhinweise werden nicht allein wegen erfolgreicher Normalisierung entfernt.

## Ergänzung V0.0.16 – Verlegungstext ist keine Terminregel

Die bisherige Sperre für zusätzliche Datumsangaben im Ausfallhinweis wird durch
eine ausdrücklich prüfpflichtige Vorschau ersetzt. Nur das führende, vollständige
Ausfalldatum wird angewendet; es muss weiterhin zur Terminserie gehören.
Weitere Datums- und Zeitangaben sind unverändert erhaltener Freitext, kein
Ersatztermin. Auch ein Datum ohne Jahr erhält kein automatisch ergänztes Jahr.
Ein unabhängig vorhandener Einzeltermin wird weder verändert noch automatisch
als Ersatz verknüpft. `replacement_reference_requires_review` kennzeichnet diese
Fälle zusätzlich zu `cancellations_require_review`; `complete` bleibt false.

Ungültige oder doppelte führende Ausfalldaten und zu lange Hinweise brechen
weiterhin ab. Ein ungültiges Datum innerhalb des opaken Hinweises wird als Text
bewahrt, niemals als Kalenderdatum interpretiert. Allgemeine Serienbemerkungen
oder Durchführungshinweise bleiben zunächst blockierend: Hier könnten Regeln
stehen, welche die ganze Serie beeinflussen.

Bei blockierter Normalisierung enthält das interne Detailergebnis jetzt
`unresolved_course` mit allen bereits geparsten Serien. Es wird keine Teilvorschau
ausgegeben. Diese Daten erscheinen weder in `repr` noch im bereinigten CLI-Bericht
und werden noch nicht auf Datenträger gespeichert. Für eine spätere geschützte
Prüfansicht muss die Darstellung separat umgesetzt und gegen XSS abgesichert
werden. Der Semesterbericht behält Schema 3 und die bisherigen Zähler.
### Serienhinweise innerhalb V0.0.16

Drei live belegte Formate dürfen als Hinweis erhalten bleiben:

- Exakt `Vorlesung`: Kennzeichnung des Lehrformats.
- Exakt `Nachholtermin`: nur beim bereits strukturiert erfassten Rhythmus `Einzel`
  mit genau einem Datum. Keine Zuordnung zu einem bestimmten Ausfall.
- `Labor` gefolgt von einer Raumkennung aus Großbuchstabe und drei durch Punkte
  getrennten Zahlengruppen: zusätzlicher Raumhinweis. Das separate Raumfeld wird
  nicht überschrieben. Der Hinweis bleibt stets mit `room_note_requires_review`
  prüfpflichtig, auch wenn die Räume übereinstimmen sollten.

Die Vorschau ergänzt `series_annotations` mit `series_index`, `kind` und `text`.
Mögliche Arten sind `teaching_format`, `makeup_label` und `room_hint`. Der
Originaltext bleibt erhalten; jede dieser Annotationen behält
`notes_require_review`, ein Nachholtermin zusätzlich
`replacement_reference_requires_review`. Datum, Uhrzeit, Raum und bestehende
Termine werden durch die Annotation nicht verändert.

Die Erkennung erfolgt über vollständige Übereinstimmung. Zusätze wie
„nur jede zweite Woche“, unbekannte Formate und Durchführungshinweise führen
weiterhin zum Abbruch der gesamten Veranstaltungsvorschau. Bei einem späteren
Fehler wird keine Teilvorschau mit bereits erkannten Annotationen zurückgegeben.
Das neue Feld gehört zur internen Kalendervorschau; der bereinigte CLI-Bericht
bleibt unverändert bei Schema 3 und enthält keine Hinweistexte.