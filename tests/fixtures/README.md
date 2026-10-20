# Fiktive Parser-Testdaten

`course_detail.html` übernimmt ausschließlich die am 20.10.2026 beobachtete Tabellenstruktur einer Veranstaltungsdetailseite. Sämtliche Werte wurden durch fiktive Angaben ersetzt oder geleert: Titel, Kennungen, Semester, Termine, Räume und Lehrpersonen. Adressen, Linkziele, Formulardaten, Bilder, Skripte und Kommentare wurden entfernt. Es handelt sich nicht um einen archivierten Originalplan.

Beobachtet wurden eine Titelüberschrift, eine Metadatentabelle mit paarweisen Überschrift-/Wertzellen sowie eine Termintabelle mit zwei Zeilen. Leere Langtexte und fehlende Veranstaltungsnummern wurden ebenfalls live beobachtet und in der Testdatei nachgebildet. Diese Struktur bildet die Grundlage des Parsers. Die Testvarianten für unbekannte Rhythmen, Ausfälle und Fehlerseiten sind ausdrücklich synthetische Grenzfälle; sie belegen keine erfolgreiche Untersuchung dieser Sonderfälle in der Live-Quelle.

Der Parser liefert Terminserien. Er erzeugt noch keine einzelnen Kalendertermine und bestätigt keine Vollständigkeit eines Semesters. Leere oder strukturell unbekannte Tabellen werden derzeit abgelehnt.
