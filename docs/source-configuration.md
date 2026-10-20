# Datenquelle und vertrauliche Konfiguration

Die Datenquelle ist die interne QIS-LSF-Vorlesungsplanung. **Die konkrete Quell-URL ist vertrauliche Betriebskonfiguration und gehört nicht in dieses Repository.** Sie darf weder in Dokumentation, Quellcode, Beispieldateien, Screenshots, Tests, Fehlermeldungen noch in Commit-Nachrichten veröffentlicht werden.

Die Adresse wird ausschließlich zur Laufzeit über die Umgebungsvariable `LSF_BASE_URL` oder eine lokal gespeicherte, von Git ausgeschlossene Konfigurationsdatei bereitgestellt. Eine `.env.example` darf nur den Variablennamen und einen leeren Wert enthalten. Die tatsächliche URL darf nicht in `.env.example` stehen.

**Wenn für Entwicklung, Tests oder Fehleranalyse die Quell-URL benötigt wird, muss ausdrücklich beim Projektverantwortlichen nachgefragt werden.** Keine Adresse erraten, aus früheren Gesprächen übernehmen oder in Dateien niederschreiben.

Die Quelle kann nur aus einer berechtigten Netzwerkumgebung erreichbar sein. Ob Anmeldung, Sitzungen, dynamische Inhalte oder spezielle Parameter erforderlich sind, ist noch nicht verifiziert. Keine nicht dokumentierten Schnittstellen voraussetzen.

[Zurück zum Projektüberblick](../README.md)
