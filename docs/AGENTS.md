# AGENTS.md – Codex-Arbeitsanweisungen für WI-PlanArchiv

Diese Datei gilt für das gesamte Repository. Ergänzende `AGENTS.md` in Unterordnern dürfen konkrete Bereiche präzisieren, aber die Sicherheitsregeln dieser Datei nicht aufheben.

## 1. Aufgabe und Prioritäten

Entwickle **WI-PlanArchiv** als wartbare, interne Webanwendung zur automatischen Sicherung und modernen Anzeige von Stundenplänen aus QIS-LSF der Hochschule Pforzheim. Arbeite inkrementell und nachvollziehbar.

Prioritäten in dieser Reihenfolge:

1. Korrekte, vollständige und reproduzierbare Sicherung.
2. Keine Zerstörung des letzten gültigen Archivstands.
3. Sicherheit, Datenschutz und schonender Zugriff auf das Quellsystem.
4. Testbarkeit und klare Trennung der Komponenten.
5. Einfache, responsive Benutzeroberfläche.
6. Zusatzfunktionen erst nach einem zuverlässigen Kern.

**Keine Annahmen als verifizierte Fakten ausgeben.** LSF-Endpunkte, Parameter, Zugänglichkeit, Studiengang-IDs, Datenformat und Authentifizierung müssen durch dokumentierte Tests belegt werden. Wenn Zugriff auf die Quelle fehlt, mit lokalen Fixtures arbeiten und offene Fragen dokumentieren.

## 2. Verbindliche technische Leitlinien

- Sprache von Benutzeroberfläche, Nutzertexten und Dokumentation: **Deutsch**; technische Bezeichner im Code vorzugsweise Englisch.
- Backend Python 3 und Flask, HTML/Jinja-Templates, Bootstrap 5, SQLite für den MVP.
- Datenimport, Parser, Archivspeicherung, Scheduler und Web-Routen in getrennten Modulen entwickeln.
- Verwende möglichst wenige Abhängigkeiten; neue Bibliotheken kurz begründen.
- Für Datenmodelle ein nachvollziehbares Migrationskonzept vorsehen; keine stillen destruktiven Schemaänderungen.
- Konfiguration über Umgebungsvariablen; eine `.env.example` ohne echte Secrets bereitstellen.
- Eine Zeitsteuerungsstrategie pro Deployment (systemd-Timer oder APScheduler), keine mehrfach parallel laufenden Jobs durch Gunicorn-Worker.
- Zeitzone `Europe/Berlin`; intern zeitlich eindeutige Timestamps (UTC) speichern und bei Anzeige lokal umrechnen. Sommer-/Winterzeit berücksichtigen.
- ISO-Kalenderwochen und Jahreswechsel korrekt behandeln.
- Für Demo und Tests ausschließlich eindeutig gekennzeichnete fiktive Daten verwenden.

## 3. Quellzugriff: verpflichtende Vorgehensweise

Quelle: die interne QIS-LSF-Vorlesungsplanung. **Die konkrete Quell-URL darf unter keinen Umständen im Repository dokumentiert werden.** Sie wird nur zur Laufzeit durch `LSF_BASE_URL` bzw. eine Git-ignorierte lokale Konfiguration bereitgestellt. Falls die Adresse für die Aufgabe erforderlich ist, muss Codex zuerst den Projektverantwortlichen ausdrücklich danach fragen. Keine Adresse aus früheren Kontexten rekonstruieren, erraten oder veröffentlichen.

Bei der Quellenanalyse:

1. Navigationsfluss, Quellkennungen, Semester- und Wochenparameter erfassen.
2. Prüfen, ob Daten statisch im HTML, über zusätzliche HTTP-Anfragen oder per JavaScript geladen werden.
3. Einfachen HTTP-Abruf bevorzugen; Playwright nur hinzufügen, wenn technisch erforderlich.
4. Repräsentative HTML-/JSON-Test-Fixtures anonymisiert unter `tests/fixtures/` ablegen, soweit zulässig.
5. Wiederkehrende Termine, Feiertage, Blocktermine, Gruppen, Vertiefungen und Änderungen prüfen.
6. Einen vollständigen Semesterumfang nachweisbar testen, nicht nur die angezeigte Woche.
7. Ergebnisse und verbleibende Unsicherheit in `docs/source-analysis.md` dokumentieren.

Ohne ausdrückliche Freigabe keine Lasttests, aggressiven Crawls oder breit angelegten Abrufe. Standardmäßig geringe Parallelität, Rate-Limits, Timeouts, begrenztes Retry mit Backoff sowie aussagekräftiges Logging implementieren. Keine Zugangsbeschränkungen umgehen.

## 4. Archiv und Datenintegrität

- Quellrohdaten (falls zulässig) und normalisierte Veranstaltungsdaten logisch getrennt halten.
- Jeden Import einem `BackupRun` zuordnen; Provenienz und Importstatus speichern.
- Neue Snapshots zunächst in einen **vorläufigen, unveröffentlichten** Zustand schreiben.
- Vollständigkeit und Konsistenz validieren (z. B. Studiengang, Semester, erwartete Seiten/Zeiträume, Parsing-Fehler).
- Snapshot erst danach in einer Transaktion als letzten gültigen Stand veröffentlichen.
- Fehlerhafte, leere oder unvollständige Importe dürfen den letzten erfolgreichen Stand **niemals** ersetzen.
- Zeitstempel und Status einer fehlgeschlagenen Sicherung von denen der letzten erfolgreichen Sicherung klar unterscheiden.
- Wiederholte Importe desselben Inhalts dürfen keine unnötigen neuen Versionen erzeugen.
- Aufbewahrungsbereinigung niemals ohne Schutz des zuletzt gültigen Stands durchführen.
- Restore der Archivdaten dokumentieren und testen.

## 5. Frontend / UX

- Primäre Ansicht ist **nicht** das historische QIS-LSF-Layout, sondern eine eigenständige, moderne Darstellung.
- Wochenansicht als Standard; für Smartphones eine gut bedienbare Listen- oder Tagesansicht.
- Filter: Studiengang, Fachsemester, Hochschulsemester, Kalenderwoche; Vertiefung/Gruppe nach Bedarf aus tatsächlicher Quelle.
- Veranstaltung zeigt vorhandene Angaben wie Titel, Start/Ende, Raum, Lehrperson und Art; fehlende Angaben transparent behandeln.
- Unterschiedliche Veranstaltungstypen visuell differenzieren, aber Bedeutung nicht ausschließlich über Farbe vermitteln.
- Immer deutlich anzeigen: **Letzte erfolgreiche Sicherung**, ausgewählter Archivstand und gegebenenfalls Fehlerzustand.
- Barrierearme Bedienung: semantisches HTML, Tastaturbedienung, Kontraste, Labels und lesbare mobile Darstellung.
- Originaldarstellung nur ergänzend und sicher gerendert bereitstellen.
- Kein UI-Feature vortäuschen, das noch keine Daten oder Implementierung besitzt.

## 6. Backend / Administration

- Die Auswahlschalter `backup_enabled` und `display_enabled` bleiben voneinander unabhängig.
- Standardmäßig nur relevante WI-Studiengänge konfigurieren, Erweiterbarkeit auf andere Studiengänge vorsehen.
- Adminfunktionen durch Authentifizierung und Autorisierung schützen.
- Ändernde HTTP-Endpunkte mit geeigneter CSRF-Prüfung und serverseitiger Validierung versehen.
- Zeitpläne, Aufbewahrungsfristen, manueller Start und Backup-Historie administrierbar machen.
- Gleichzeitige Jobs für denselben Importbereich mit Sperren bzw. eindeutigem Job-Status verhindern.
- Kein automatischer Backup-Job darf allein durch den normalen Aufruf der Website ausgelöst werden.

## 7. Sicherheit und Datenschutz

- **Keine reale Quell-URL** (auch keine Teil-URL, Hostnamen, Pfade, Query-Parameter oder URL-codierte Varianten) in Repository-Dateien, Dokumentation, Konfigurationsbeispielen, Tests, Fixtures, Screenshots, Issues, Pull Requests, Commit-Nachrichten oder Logs hinterlegen.
- Keine Secrets, Cookies, Zugangsdaten, personenbezogenen Testdaten oder Infrastruktur-Adressen in Commits oder Logs.
- Vertrauliche Quelladressen ausschließlich zur Laufzeit über `LSF_BASE_URL` oder eine lokal Git-ignorierte Konfiguration beziehen. `.env.example` enthält `LSF_BASE_URL=` ohne Wert; `.env` wird ignoriert.
- Bei fehlender URL niemals einen Standardwert mit einer echten Hochschuladresse einsetzen. Den Projektverantwortlichen bei Bedarf danach fragen.
- Logs, Exceptions, Traces und Testberichte so bereinigen, dass auch bei HTTP-Fehlern keine vollständige oder teilweise Quelladresse erscheint.
- Vor jedem Commit prüfen, ob versehentlich interne URLs in Dateien oder Änderungen aufgenommen wurden. Bereits versehentlich veröffentlichte URLs müssen auch aus der Git-Historie bereinigt werden.
- `.env`, Datenbankdateien, Backupdateien, Browserprofile und heruntergeladene geschützte Inhalte in `.gitignore` berücksichtigen.
- Daten aus Quellseiten als **untrusted input** behandeln; Parser defensiv entwickeln.
- Archiviertes HTML niemals unkontrolliert mitsamt fremden Skripten im eigenen Weborigin darstellen (XSS-Risiko). Bevorzugt Daten extrahieren und selbst rendern; Originalsnapshot nur sanitisiert oder isoliert.
- Abfrageparameter, Dateipfade und externe URLs validieren, um SQL-Injection, Path-Traversal und SSRF zu vermeiden.
- Datenspeicherung und Datenanzeige gemäß abgestimmten Hochschulregeln beschränken; Lösch- und Aufbewahrungskonzept dokumentieren.
- Keine öffentliche Freigabe von Hochschuldaten allein aus Bequemlichkeit.

## 8. Tests und Qualitätskriterien

Schreibe bzw. aktualisiere Tests für jede relevante Änderung. Mindestens:

- Parser-Tests mit echten, freigegebenen/anonymisierten Fixtures und Grenzfällen.
- Tests für deutsche Datums-/Zeitformate, ISO-Wochen und Zeitzonenwechsel.
- Tests für Vollständigkeit, Fehlversuche und unvollständige Quelldaten.
- Test: Ein fehlgeschlagener Import überschreibt nicht den letzten guten Snapshot.
- Test: Identische Daten erzeugen keine unnötige neue Version.
- Tests für Admin-Berechtigungen und Konfigurationsvalidierung.
- Tests für Filter sowie korrekt gekennzeichnete veraltete Archivstände.

Nutze `pytest`. Halte `README.md`, relevante Dateien unter `docs/` und insbesondere `docs/timeline.md` parallel zum Code aktuell. Änderungen sollen mit nachvollziehbaren, kleinen Commits strukturiert werden, sofern Commit-Erstellung explizit beauftragt ist.

## 9. Arbeitsweise bei Codex-Aufgaben

Vor Änderungen:

1. Projektstruktur, bestehende Tests und Dokumentation lesen.
2. Den konkreten Auftrag zusammenfassen und betroffene Module bestimmen.
3. Offene technische Annahmen kurz benennen; bei Blockern sicheren Minimalansatz wählen.

Während Änderungen:

1. Kleine, testbare Einheiten bauen statt großer Umbauten.
2. Bereits funktionierende Features und Datenmigrationen berücksichtigen.
3. API, DB-Schema und Datenfluss konsistent halten.
4. Bei Architekturentscheidungen unter `docs/decisions/` kurz festhalten, warum eine Variante gewählt wurde.

Nach Änderungen:

1. Passende Tests und Linter ausführen (sofern verfügbar).
2. Ergebnisse, Fehler und nicht ausgeführte Prüfungen offen nennen.
3. In wenigen Punkten dokumentieren: geändert, getestet, verbleibende Risiken, nächster sinnvoller Schritt.
4. Keine Erfolgsmeldung für ungeprüfte Live-LSF-Abrufe oder Deployments abgeben.

## 10. MVP-Umsetzungsreihenfolge

- **Schritt A:** Source-Analyse und `docs/source-analysis.md`; eine kleine, erlaubte Testdatenbasis.
- **Schritt B:** Parser/Normalizer mit JSON-Ergebnis für einen Studiengang und Semester.
- **Schritt C:** DB-Modell und sichere Snapshot-Veröffentlichung.
- **Schritt D:** Wochen-/Listenansicht und Filter mit klaren Backup-Zeitstempeln.
- **Schritt E:** Geschützter Adminbereich, Backup-Auswahl und konfigurierbare Sicherungsjobs.
- **Schritt F:** Versionsvergleich und optionale Exporte.

**Definition of Done pro Schritt:** Funktion dokumentiert, Fehlerfälle berücksichtigt, relevante Tests vorhanden und erfolgreich, keine echten Zugangsdaten im Repository, kein Datenverlust beim fehlgeschlagenen Import.

## 11. Explizit nicht im initialen MVP

- Hochschulweiter Massencrawl ohne vorherige Freigabe.
- Komplexes Nutzer-/Rollenmanagement jenseits sicherem Adminzugriff.
- Vollautomatische Erkennung aller Planänderungen vor belastbarer Event-Normalisierung.
- Mobile Native-App, Push-Nachrichten, umfangreiche API oder Cloud-Abhängigkeiten.
- Behauptungen über Echtzeitdaten: PlanVault/WI-PlanArchiv ist ein **Archiv**, kein Ersatz für eine garantierte Livequelle.
## 12. Versionierung, Footer und Timeline

- Die aktuelle Anwendungsversion wird zentral in `version.py` im Repository-Hauptverzeichnis als `__version__` festgehalten. Andere Stellen beziehen die Version daraus; keine unabhängig gepflegten Versionsangaben im Anwendungscode oder in Templates.
- Die Webseite zeigt die aktuelle Version aus `version.py` im gemeinsamen Footer aller Seiten an, mit vorangestelltem `V` (z. B. `V0.1.3`).
- Versionsschema: `V<Major>.<Minor>.<Patch>`. Codex schlägt anhand des tatsächlich erreichten Roadmap-/Meilensteinstands die ersten beiden Stellen vor, z. B. `V0.1.x`, und begründet den Vorschlag kurz. Geplante, noch nicht umgesetzte Funktionen rechtfertigen keine höhere Version.
- Die dritte Stelle (`x`, Patch) wählt der User. Codex darf sie weder selbst festlegen noch automatisch erhöhen. Eine vom User angegebene vollständige Version wird in `version.py` übernommen; ohne neue Angabe bleibt eine bestehende Version unverändert. Bei der erstmaligen Versionsfestlegung bleibt der Vorschlag bis zur Auswahl durch den User in der Timeline offen; `x` ist ein Platzhalter und keine veröffentlichte Anwendungsversion.
- Orientierung für Versionsvorschläge entlang der Roadmap: `V0.0.x` für Konzept und Entwicklungsstart; `V0.1.x` für Quellenanalyse und Import-Prototyp (M0/M1); `V0.2.x` für Persistenz (M2); `V0.3.x` für Web-MVP (M3); `V0.4.x` für Administration (M4); `V0.5.x` für Erweiterungen (M5). `V1.0.x` erst bei vollständig umgesetztem und geprüftem MVP. Diese Zuordnung dient als Vorschlag, die endgültige Version bestimmt der User.
- Bei jeder Änderung, auch an Dokumentation oder Konfiguration, `docs/timeline.md` aktualisieren. Pro vollständiger Version gibt es genau einen gemeinsamen Eintrag. Alle Änderungen derselben Version werden dort zusammengefasst, auch über mehrere Aufgaben, Commits oder Tage hinweg; keinen weiteren Eintrag für dieselbe Version anlegen. Erst bei einer neuen Version einen neuen Eintrag oberhalb der bisherigen Versionen erstellen. Jeder Eintrag enthält Version, Datum bzw. Datumszeitraum, eine zusammengefasste Änderungsliste und den aktuellen Prüfstatus. Einen offenen Versionsvorschlag bei Festlegung der vollständigen Version im bestehenden Eintrag ersetzen.
- Jeder Versionseintrag enthält außerdem unter **Commit-Kurzbeschreibung** einen knappen deutschen Text, der die gesamten Änderungen dieser Version zusammenfasst und als Commit-Betreff bei GitHub verwendet werden kann. Diesen Text bei weiteren Änderungen derselben Version entsprechend aktualisieren. Dies dokumentiert den Vorschlag und bedeutet nicht, dass bereits ein Commit erstellt wurde. Commits weiterhin nur auf ausdrücklichen Auftrag erstellen.
- Vor Abschluss prüfen, dass `version.py`, die Footer-Anzeige und der zugehörige Timeline-Eintrag bei Versionsänderungen übereinstimmen. Solange noch keine Webanwendung existiert, die Footer-Anforderung bei deren Implementierung umsetzen und nicht als bereits erledigt darstellen.
