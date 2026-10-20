# Fiktive Parser-Testdaten

`course_detail.html` übernimmt ausschließlich die am 20.10.2026 beobachtete Tabellenstruktur einer Veranstaltungsdetailseite. Sämtliche Werte wurden durch fiktive Angaben ersetzt oder geleert: Titel, Kennungen, Semester, Termine, Räume und Lehrpersonen. Adressen, Linkziele, Formulardaten, Bilder, Skripte und Kommentare wurden entfernt. Es handelt sich nicht um einen archivierten Originalplan.

Beobachtet wurden eine Titelüberschrift, eine Metadatentabelle mit paarweisen Überschrift-/Wertzellen sowie eine Termintabelle mit zwei Zeilen. Leere Langtexte und fehlende Veranstaltungsnummern wurden ebenfalls live beobachtet und in der Testdatei nachgebildet. Diese Struktur bildet die Grundlage des Parsers. Die Testvarianten für unbekannte Rhythmen, Ausfälle und Fehlerseiten sind ausdrücklich synthetische Grenzfälle; sie belegen keine erfolgreiche Untersuchung dieser Sonderfälle in der Live-Quelle.

Der Parser liefert Terminserien. Er erzeugt noch keine einzelnen Kalendertermine und bestätigt keine Vollständigkeit eines Semesters. Leere oder strukturell unbekannte Tabellen werden derzeit abgelehnt.

`course_exceptions.html` ergänzt ab V0.0.11 einen tatsächlich beobachteten
Strukturfall: wöchentliche Serie, `Einzel` mit gleichem Start-/Enddatum und
Ausfallangabe in der Form `Datum: Hinweis`. Die Datei wurde ausschließlich mit
fiktiven Titeln, Kennungen, Terminen, Räumen, Lehrpersonen und Hinweisen erstellt.
Sie enthält keine Originalinhalte und behauptet keine Verlegungsbeziehung.
Die separate Normalisierung erhält den Ausfall samt Hinweis und erzeugt
Kalendervorschauen; die Semester-Vollständigkeit bleibt ungeprüft.

`course_exceptions.html` ergänzt ab V0.0.11 einen tatsächlich beobachteten
Strukturfall: wöchentliche Serie, `Einzel` mit gleichem Start-/Enddatum und
Ausfallangabe in der Form `Datum: Hinweis`. Die Datei wurde ausschließlich mit
fiktiven Titeln, Kennungen, Terminen, Räumen, Lehrpersonen und Hinweisen erstellt.
Sie enthält keine Originalinhalte und behauptet keine Verlegungsbeziehung.
Die separate Normalisierung erhält den Ausfall samt Hinweis und erzeugt
Kalendervorschauen; die Semester-Vollständigkeit bleibt ungeprüft.
