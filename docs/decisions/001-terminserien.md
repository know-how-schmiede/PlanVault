# 001 – Veranstaltungsdetails zunächst als Terminserien erfassen

**Stand:** 2026-10-20, Version 0.0.3.

## Beobachtung

Die geprüften Detailseiten enthalten je Terminzeile Wochentag, Uhrzeiten, Rhythmus und einen Datumsbereich. Daneben gibt es eigene Spalten für Bemerkungen, Durchführung und Ausfälle. Der Titel steht in einer Überschrift; Langtext und Veranstaltungsnummer können leer sein.

## Entscheidung

Der Parser liest ausschließlich bereits geladenes HTML und liefert eine Veranstaltung mit unveränderten Terminserien. Er führt keine HTTP-Aufrufe aus und schreibt keine Archivdaten. Beautiful Soup wird für die Auswertung der HTML-Tabellen verwendet; zusätzliche Netzwerk- oder Browserbibliotheken sind dafür nicht erforderlich.

Tageszeiten bleiben lokale Uhrzeiten mit der Zuordnung `Europe/Berlin`. Eine Umrechnung nach UTC erfolgt erst, wenn einzelne tatsächliche Termine samt Datum feststehen. Wiederholungen werden nicht ungeprüft über den gesamten Datumsbereich expandiert.

Der Parser ordnet Felder über Tabellenüberschriften zu. Unbekannte oder unvollständige Zeilen führen zum Fehler statt zum stillen Weglassen. Nicht verifizierte Rhythmen, Ausfalltexte, Bemerkungen und mehrere Termintabellen bleiben erhalten und werden zur weiteren Prüfung markiert. Eine fehlende Veranstaltungsnummer wird nicht durch den Titel ersetzt.

## Folgen

Die Daten reichen für den ersten Parser-Test und die weitere Quellenanalyse, noch nicht für einen vollständigen Stundenplan. Der spätere Abrufadapter muss eine belastbare Quellzuordnung aus der Navigation herstellen. Gruppenbezug, Wochenend-/Blocktermine, Ausnahmen und Semester-Vollständigkeit benötigen zusätzliche Live-Nachweise und Tests. Eine leere Detailtabelle gilt vorerst nicht als verifizierter leerer Plan.
