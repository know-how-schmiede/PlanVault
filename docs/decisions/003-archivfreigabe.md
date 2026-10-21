# 003 – Explizite Regeln und gebundene Archivfreigabe

Datum: 2026-10-21 · umgesetzt in V0.0.30

Die Quelle liefert wiederkehrende Detailserien und eine fünftägige Wochenansicht. Ferienhinweise sind teilweise unbenannt; Gruppen, Zusatztexte und Wochenendfreiheit sind daraus nicht vollständig maschinell nachweisbar. Eine bloß gleiche Menge von Veranstaltungstiteln reicht für einen vollständigen Kalenderimport nicht.

Der neue Import erhält deshalb eine unabhängig vorgegebene Semesterregeldatei. Tageskolumnen, Zeiten, Räume und Veranstaltungsart werden als Multimenge abgeglichen. Explizite Ferienausnahmen betreffen ausschließlich dort unsichtbare regelmäßige Termine; sichtbare Ausnahmen und Einzeltermine bleiben erhalten. Harte Fehler erlauben keine Freigabe. Verbleibende fachliche Befunde werden einzeln mit einem Beleg bestätigt. Die Bestätigungen binden per SHA-256 den gesamten Importinhalt einschließlich ursprünglicher Serien und Beobachtungen; ein veränderter oder unvollständiger Prüfbeleg wird abgewiesen.

SQLite speichert zuerst einen vorläufigen `BackupRun` in `runs`. Eine kurze Schreibtransaktion prüft den unveränderten Inhalt und alle Bestätigungen, legt bei verändertem Inhalt einen Snapshot an und aktualisiert erst dann den letzten gültigen Stand. Fehlversuche stehen separat in der Historie. Netzwerkabrufe laufen außerhalb einer SQLite-Schreibtransaktion; eine Betriebssystem-Dateisperre schützt den gesamten Import. Es gibt keine Freigabe durch HTTP-Seitenaufrufe und keine automatische Sicherungsbereinigung.

Schemaversion 1 verwendet ausschließlich die Python-Standardbibliothek. Fremde Datenbanken oder unbekannte Schemaversionen werden ohne Migration abgewiesen. Sicherung und Restore nutzen die SQLite-Backup-API; Restore schreibt ausschließlich eine neue Datei. Die Auswahl für den produktiven Betrieb erfolgt nach Prüfung über die externe Konfiguration. Der lokale Test ersetzt keine Wiederherstellungsprobe im Zielcontainer.
