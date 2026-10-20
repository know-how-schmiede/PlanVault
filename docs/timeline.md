# Timeline

Alle Änderungen einer Version werden in einem gemeinsamen Eintrag zusammengefasst. Neue Versionen stehen oben.

## V0.0.10 – Gemeinsamer Import-Prüflauf und JSON-Bericht

**Datum:** 2026-10-20

**Änderungen:**

- Version auf Userwunsch zentral auf `0.0.10` gesetzt.
- Navigation, Wochenabgleich und Detailstichprobe zu einem gemeinsamen Prüflauf verbunden.
- Gleiche Detailziele aus mehreren geprüften Wochen zusammengeführt; keine Detailabrufe nach ungeklärten Wochenantworten.
- Bereinigten Bericht mit Lauf-ID, UTC-Zeitstempeln, Versionsangabe, Phasen, Anzahlen und offenen Punkten ergänzt. Keine Quelladressen oder Veranstaltungsdaten im Bericht.
- Befehl `source-import-check` mit optionaler JSON-Ausgabe ergänzt. Vollständigkeit und Veröffentlichung bleiben ausdrücklich unbestätigt.
- README, Roadmap, Quellenanalyse und Anleitung aktualisiert.

**Prüfung:** 178 lokale Tests erfolgreich. Gemeinsamer Live-Prüflauf mit zehn HTTP-Anfragen: KW 43/2026 und KW 44/2026 passend, 51 unterschiedliche Detailziele, zwei Details geprüft; 24 fehlende Wochen und 49 ungeprüfte Ziele korrekt ausgewiesen. Keine Rohseiten oder Quelladressen gespeichert. `git diff --check` ohne Fehler. Kein vollständiger Semesterimport, keine Archivveröffentlichung und kein Deployment im LXC.

**Commit-Kurzbeschreibung:** Version 0.0.10 mit gemeinsamem Import-Prüflauf und bereinigtem JSON-Bericht ergänzen

## V0.0.9 – Detailzuordnung und begrenzte Importstichprobe

**Datum:** 2026-10-20

**Änderungen:**

- Version auf Userwunsch zentral auf `0.0.9` gesetzt.
- Veranstaltungslinks anhand der beobachteten Blockstruktur gesammelt und von Raumlinks getrennt.
- Identische absolute Ziele innerhalb des Prüflaufs zusammengefasst; unterschiedliche Ziele niemals allein anhand des Titels zusammengeführt.
- Begrenzten Detailabruf mit Semesterprüfung, Parser und Kalendervorschau verbunden. Fehler verhindern ein erfolgreiches Teilergebnis; ungeklärte Normalisierung bleibt markiert.
- Befehl `source-details-check` ergänzt: explizite Woche, erwartetes Semester, lokale Zuordnungskennungen und maximal zehn Detailziele.
- README, Roadmap, Quellenanalyse und Anleitung aktualisiert.

**Prüfung:** 166 lokale Tests erfolgreich. Live-Stichprobe mit acht HTTP-Anfragen: 53 Blöcke, 47 unterschiedliche Detailziele; zwei Details mit einer beziehungsweise zwei Serien verarbeitet, 45 Ziele ungeprüft. Keine Rohseiten oder Quelladressen gespeichert. `git diff --check` ohne Fehler. Dauerhafte Quellidentität, vollständiger Semesterimport und Deployment im LXC bleiben offen.

**Commit-Kurzbeschreibung:** Version 0.0.9 mit Detailzuordnung und begrenzter Importstichprobe ergänzen

## V0.0.8 – Wochennavigation und Abdeckungsprüfung

**Datum:** 2026-10-20

**Änderungen:**

- Version auf Userwunsch zentral auf `0.0.8` gesetzt.
- Datierte Wochenauswahl mit Prüfung von Datumsbereich, ISO-Jahr, Wochennummer und Eindeutigkeit ergänzt.
- Wochenwechsel über beobachtete Formularwerte mit Prüfung der ausgewählten Woche und sichtbaren Tagesüberschriften verbunden.
- Wochenantworten gegen einen unabhängig angegebenen Zeitraum abgeglichen. Nicht besuchte Wochen bleiben fehlend; ungeklärte leere Ansichten und Ferienhinweise verhindern eine Vollständigkeitsmeldung.
- Manuellen Befehl `source-weeks-check` für ausdrücklich ausgewählte Wochen ergänzt. Beim ersten ungeklärten Ergebnis stoppt die Prüfung.
- README, Roadmap, Quellenanalyse und Bedienungsanleitung aktualisiert.

**Prüfung:** 146 lokale Tests erfolgreich. Live-Stichprobe mit acht HTTP-Anfragen: 26 angebotene Wochen, KW 44/2026 strukturell passend, KW 53/2026 wegen Ferienhinweisen prüfpflichtig; 24 fehlende Wochen korrekt gemeldet. Keine Quelladressen oder Rohseiten gespeichert. `git diff --check` ohne Fehler. Vollständiger Semesterimport, Wochenend-/Sonderterminerfassung und Deployment im Zielcontainer bleiben offen.

**Commit-Kurzbeschreibung:** Version 0.0.8 mit Wochennavigation und strenger Abdeckungsprüfung ergänzen

## V0.0.7 – Live-geprüfte Studiengangsnavigation

**Datum:** 2026-10-20

**Änderungen:**

- Version auf Userwunsch zentral auf `0.0.7` gesetzt.
- Studiengangssuche über sichtbare Feldbeschriftungen, eindeutige Trefferlinks und ausdrücklich benannte Suchschaltflächen implementiert. Keine realen Quellparameter im Code hinterlegt.
- Normale Fieldsets und gleichwertige doppelte Submit-Schaltflächen unterstützt; schreibgeschützte Studiengangsanzeige mit versteckter Auswahl korrekt erhalten.
- Manuellen Befehl `source-plan-check` ergänzt; Ergebnisse bleiben reine Navigationsprüfung ohne Archivveröffentlichung.
- README, Roadmap, Quellenanalyse und Bedienungsanleitung aktualisiert.

**Prüfung:** 122 lokale Tests erfolgreich, einschließlich Versionsfooter und Navigation. Ablauf Einstieg → Suche → Treffer → Auswahlbestätigung → Planantwort für den bereits untersuchten Studiengang live erfolgreich: sechs HTTP-Anfragen einschließlich Weiterleitungen, 53 bekannte Veranstaltungsblöcke. Keine Rohseiten, Quelladressen oder Formularparameter gespeichert. Vorheriger Versuch mit fünf Anfragen wurde erwartungsgemäß vom Budget gestoppt. Kein vollständiger Semesterimport und kein Deployment im LXC; `git diff --check` ohne Fehler.

**Commit-Kurzbeschreibung:** Version 0.0.7 mit live geprüfter Studiengangsnavigation ergänzen

## V0.0.6 – Geprüfte Formularnavigation

**Datum:** 2026-10-20

**Änderungen:**

- Version auf Userwunsch zentral auf `0.0.6` gesetzt.
- Formularauswahl anhand expliziter Feldnamen sowie GET-/POST-Übermittlung über die bestehende HTTP-Sitzung ergänzt.
- Versteckte und wiederholte Felder, Textbereiche, Auswahlen und explizite Suchschaltflächen unterstützt; unerlaubte Überschreibungen und mehrdeutige Strukturen abgelehnt.
- Ausschließlich fiktive Formulartests ergänzt; keine realen Navigationsparameter hinterlegt.
- README, Roadmap und Quellenanalyse um Funktionsumfang und offene Live-Zuordnung ergänzt.

**Prüfung:** 106 lokale Tests erfolgreich, einschließlich Formularnavigation, HTTP-Adapter, Parser und Versionsfooter; `git diff --check` ohne Fehler. Keine Live-Navigation und keine Bereitstellung im LXC durchgeführt; automatischer Semesterimport bleibt offen.

**Commit-Kurzbeschreibung:** Version 0.0.6 mit validierter Formularnavigation ergänzen

## V0.0.5 – HTTP-Abrufadapter und manueller Quelltest

**Datum:** 2026-10-20

**Änderungen:**

- Version auf Userwunsch zentral auf `0.0.5` gesetzt; Website-Betrieb nach vorherigem Update vom User bestätigt.
- HTTPS-Abrufadapter mit temporären Cookies, gleichem Quell-Origin für Navigation, Größen- und Anfragelimits, Socket-Timeout und Mindestabstand ergänzt.
- Begrenzte GET-Wiederholungen bei vorübergehenden Fehlern; keine automatischen Wiederholungen oder Weiterleitungen für Formular-POSTs. Fehlerausgaben enthalten keine Quelladressen oder Antworttexte.
- Abruf beobachteter Detailseiten mit Parser und Kalendervorschau verbunden; Ergebnisse bleiben unvollständige Vorschauen.
- Manuellen Flask-Befehl `source-check` und Anleitung für die Prüfung unter dem Dienstkonto ergänzt. Normale Webseitenaufrufe lösen keine Quellabrufe aus.
- README, Roadmap und Quellenanalyse nachgeführt. Automatische Studiengangs-/Wochennavigation und vollständige Semesterimporte bleiben offen.

**Prüfung:** 83 lokale Tests erfolgreich, einschließlich simulierter HTTP-Fehler, Weiterleitungen, Größenlimits, Abrufbudget, Parser-Anbindung, CLI und Versionsfooter; `git diff --check` ohne Fehler. Keine neuen Live-Abrufe oder Bereitstellung im LXC; Zielcontainer-Test des neuen Clients steht aus.

**Commit-Kurzbeschreibung:** Version 0.0.5 mit begrenztem Quellabruf und manuellem Verbindungstest ergänzen

## V0.0.4 – Kalendervorschau und Wochenabgleich

**Datum:** 2026-10-20

**Änderungen:**

- Version auf Userwunsch zentral auf `0.0.4` gesetzt; der gemeinsame Footer übernimmt sie.
- Erfolgreichen Website-Aufruf nach dem vorherigen Update durch den User bestätigt.
- Separate JSON-fähige Kalendervorschau ergänzt: wöchentliche Serien, vollständige Ausfalldaten, UTC-Zeitpunkte und lokale ISO-Wochen. Mehrdeutige Zeiten und ungeklärte Angaben führen zum Fehler statt zu Teilresultaten.
- Synthetisch geprüfte Einzel- und Blockregeln nur über explizite Rhythmuszuordnung zugelassen; Parser erhält einzelne Datumsangaben. Echte LSF-Sonderfälle bleiben zu verifizieren.
- Veranstaltungszuordnung über explizite Quell-, Studiengangs-, Prüfungsordnungs- und Semesterkennungen vorbereitet; keine Identität aus Titeln ableiten.
- Wochenabgleich erkennt fehlende, fehlerhafte, doppelte und unerwartete Wochen. Bestätigte leere Wochen von ungeprüften Leerantworten getrennt.
- Architekturentscheidung, README, Quellenanalyse und Roadmap aktualisiert. Zeitzonendaten für Windows als bedingte Abhängigkeit ergänzt.

**Prüfung:** 46 lokale Tests erfolgreich, einschließlich Versionsfooter, Zeitumstellung, Jahreswechsel, Ausfällen, Sonderregeln und fehlerhafter Wochenabdeckung; `git diff --check` ohne Fehler. Neue Fälle ausschließlich fiktiv; keine neuen Live-Abrufe oder Bereitstellung im LXC. Vollständiger Semesterimport, Navigation und echte Sonderfälle bleiben offen.

**Commit-Kurzbeschreibung:** Version 0.0.4 mit Kalendervorschau und sicherem Wochenabgleich ergänzen

## V0.0.3 – Quellenanalyse und erster Detailparser

**Datum:** 2026-10-20

**Änderungen:**

- Anwendungsversion auf Wunsch des Users zentral in `version.py` auf `0.0.3` gesetzt. Der Footer übernimmt die Version nach dem Deployment automatisch.
- Aktuelle Versionsangaben in Roadmap und Quellenanalyse aktualisiert. M0 bleibt in Bearbeitung.
- Feldstruktur zweier Veranstaltungsdetailseiten geprüft und eine ausschließlich fiktiv befüllte HTML-Testdatei aus der beobachteten Struktur erstellt.
- Detailparser mit Beautiful Soup ergänzt: Titel, optionale Metadaten und mehrere Terminserien lesen; unvollständige Seiten ablehnen; ungeprüfte Rhythmen, Ausfälle und fehlende Quellkennungen markieren. Keine ungeprüfte Erzeugung einzelner Kalendertermine.
- Parserentscheidung, Abhängigkeit und verbleibende Schritte für Sonderfälle und vollständigen Import dokumentiert.
- Eingabeprüfung von Installation und Update gegen führende/abschließende Leerzeichen und Wagenrückläufe gehärtet; ASCII-Locale festgelegt und ungültigen Git-Stand eindeutig ausgegeben. Der gemeldete Abbruch bei `main` ist mit unveränderter Eingabe lokal nicht reproduzierbar. 14 isolierte Bash-Eingabeprüfungen und beide Syntaxprüfungen erfolgreich; erneuter Zielcontainer-Test offen.

**Prüfung:** Versionswert, zentrale Einbindung im Footer und Dokumentationsangaben abgeglichen; `git diff --check` ohne Fehler. 22 lokale Tests erfolgreich. Detailparser zusätzlich an zwei Live-Seiten erfolgreich geprüft (eine bzw. zwei Terminserien), ohne Quelladressen oder Rohdaten zu speichern. Vollständiger Semesterimport und echte Sonderfälle bleiben offen; Änderungen noch nicht auf dem Server ausgerollt.

**Commit-Kurzbeschreibung:** Version 0.0.3 mit Detailparser ergänzen und Skripteingaben härten

## V0.0.2 – Debian-13-LXC-Installation

**Datum:** 2026-10-20

**Änderungen:**

- Anwendungsversion auf Wunsch des Users in `version.py` auf `0.0.2` gesetzt; der gemeinsame Footer übernimmt diesen Wert automatisch.
- Erstinstallationsskript für Debian-13-LXC mit Prüfung von Betriebssystem, root-Rechten, systemd, Installationszielen und lokalem Port ergänzt.
- Dienstkonto, virtuelle Python-Umgebung, Gunicorn, systemd-Dienst, Konfigurationsdatei und Datenverzeichnis vorgesehen. Vorhandene Installationen werden nicht überschrieben; Testausführung unter dem Dienstkonto und lokale HTTP-Prüfung integriert.
- Standard-Bind-Adresse auf `0.0.0.0` geändert; Abschlussmeldung zeigt die erkannten Container-IPv4-Webadressen mit dem gewählten Port. Anleitung für direkten Netzwerkzugriff und bestehende Installationen angepasst.
- Separates Git-Update-Skript ergänzt: Dienstkonfiguration erkennen, neuen Release und venv vorab testen, Konfiguration und Daten sichern, umschalten und bei Fehlern den bisherigen Anwendungspfad wiederherstellen. Konfiguration und Bind-Adresse bleiben erhalten; Update-Anleitung ergänzt.
- Erfolgreichen erneuten Betriebs- und Update-Test laut Nutzerbestätigung dokumentiert. M0 mit docs/source-analysis.md begonnen: Studiengangsuche und Planabruf ohne Login sowie Wochenwechsel einschließlich Jahreswechsel per HTTP geprüft. Semesterfilter können nicht zugeordnete Veranstaltungen ausblenden; verbleibende Prüfungen für Vollständigkeit und Sondertermine dokumentiert.
- Produktionsabhängigkeiten und LF-Zeilenenden für Shellskripte definiert.
- Installer an den Aufbau der NeoFab-ScanLab-Vorlage angepasst: interaktive Standardwerte, validierte Eingaben für Dienstnutzer, Installationspfad, Branch oder Tag und Bind-Adresse/Port, automatischer Clone des öffentlichen Projekt-Repositories sowie abschließende Übersicht mit installiertem Git-Commit.
- Download-Schnellstart ohne vorhandenen Checkout in docs/install.md und scripts/README.md ergänzt. Projektanweisungen um verbindliche Regeln für Git-basierte Installer und passende Anleitungen erweitert.
- `docs/install.md` mit Installation, Zugriff, Konfiguration, Betrieb und Fehlerbehandlung erstellt; README und Roadmap aktualisiert.

**Prüfung:** Bash-Syntax mit `bash -n` und Abbruch ohne root-Rechte geprüft; `git diff --check` ohne Fehler. Versionswert und Dokumentationsverweise abgeglichen. Die neue Webadressen-Ausgabe mit mehreren IPv4, Duplikaten, IPv6, lokalem Zugriff und fehlender IPv4 isoliert erfolgreich geprüft; der geänderte Netzwerkstandard wurde noch nicht erneut im LXC installiert. Laut vom User bereitgestelltem Installationsprotokoll vom 2026-10-20 ist die Debian-13-LXC-Erstinstallation für Commit `a58ee45b6495d130080b2d29e7330b8c6a4277b5` erfolgreich: Python 3.13.5, drei Tests bestanden, systemd-Dienst eingerichtet und lokale HTTP-Prüfung erfolgreich. Bind-Adresse `127.0.0.1:8000`. Der User bestätigt anschließend den laufenden Server und Zugriff im internen Netz. Update-Skript: Bash-Syntax, Abbruch ohne root und Rollback-Steuerung mit simulierten Systembefehlen geprüft (Vorbereitungsfehler, Umschaltfehler, Fehler vor Verschieben und erfolgreicher Abschluss). Erfolgreicher Update-Praxistest im LXC anschließend vom User bestätigt; tatsächlicher Fehlerfall mit Rollback im LXC noch offen. Prüfergebnis in Anleitung und Roadmap nachgeführt. Quellenanalyse: HTTP-200-Antworten für Einstieg, Suche, Plan und zwei Wochenwechsel beobachtet; keine vertraulichen Quelladressen oder Rohseiten im Repository abgelegt.

**Commit-Kurzbeschreibung:** Debian-LXC-Installation und Updates ergänzen sowie Quellenanalyse beginnen

## V0.0.1 – Konzept und Entwicklungsstart

**Datum:** 2026-10-20

**Änderungen:**

- Vorhandenes Projektbanner in die README eingebunden.
- Hinweise zur vertraulichen Quell-URL nach `docs/source-configuration.md` ausgelagert und in der README verlinkt.
- Aktuelle Anwendungsversion zentral als `__version__ = "0.0.1"` in `version.py` hinterlegt; dritte Versionsstelle vom User festgelegt.
- Projektanweisungen um zentrale Versionspflege, Versionsanzeige im Webseiten-Footer und Versionsvorschläge anhand der Roadmap ergänzt. Die dritte Versionsstelle bleibt dem User vorbehalten.
- Timeline einschließlich Commit-Kurzbeschreibung eingeführt und in der README verlinkt.
- Roadmap mit Projektgrundlagen, Meilensteinen M0 bis M5, Versionszielen und Abschlusskriterien erstellt und in der README verlinkt. Betrieb und Wiederherstellung als Voraussetzungen der MVP-Freigabe beschrieben.
- Projektanweisungen zur Timeline angepasst: sämtliche Änderungen derselben Version in einem Eintrag zusammenfassen und dessen Prüfstatus sowie Commit-Kurzbeschreibung fortschreiben. Bisherige Einträge für V0.0.1 zusammengeführt.

- Flask-App-Factory, Startseite mit Leerzustand und gemeinsames Layout mit Version aus version.py im Footer implementiert.
- Umgebungsbasierte Konfiguration, .env.example und Git-Ausschlüsse sowie getrennte Pakete für späteren Import, Parser, Speicherung und Scheduler angelegt. Keine Quellabrufe beim Start oder Seitenaufruf.
- Flask als Web-Abhängigkeit und pytest als Testwerkzeug aufgenommen; Tests für Start ohne Quelle, Versionsanzeige, vertrauliche Konfiguration und Stylesheet ergänzt. Installation und Testbefehle in der README dokumentiert.

**Prüfung:** Dokumentation mit README und Projektanweisungen abgeglichen; lokale Verweisziele sowie Versionswert geprüft; `git diff --check` ohne Fehler. Laufzeittests und Browserprüfung sind noch offen: Der vorhandene Windows-Python-Alias startet nicht (Fehler zur Anmeldesitzung); keine weitere Python-Installation gefunden. Die Abschlusskriterien des Projektgerüsts sind damit noch nicht vollständig verifiziert.

**Commit-Kurzbeschreibung:** Flask-Grundgerüst mit Versionsfooter, Konfiguration und Projektdokumentation anlegen
