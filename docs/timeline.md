# Timeline

Alle Änderungen einer Version werden in einem gemeinsamen Eintrag zusammengefasst. Neue Versionen stehen oben.

## V0.0.2 – Debian-13-LXC-Installation

**Datum:** 2026-10-20

**Änderungen:**

- Anwendungsversion auf Wunsch des Users in `version.py` auf `0.0.2` gesetzt; der gemeinsame Footer übernimmt diesen Wert automatisch.
- Erstinstallationsskript für Debian-13-LXC mit Prüfung von Betriebssystem, root-Rechten, systemd, Installationszielen und lokalem Port ergänzt.
- Dienstkonto, virtuelle Python-Umgebung, Gunicorn, systemd-Dienst, Konfigurationsdatei und Datenverzeichnis vorgesehen. Vorhandene Installationen werden nicht überschrieben; Testausführung unter dem Dienstkonto und lokale HTTP-Prüfung integriert.
- Standard-Bind-Adresse auf `0.0.0.0` geändert; Abschlussmeldung zeigt die erkannten Container-IPv4-Webadressen mit dem gewählten Port. Anleitung für direkten Netzwerkzugriff und bestehende Installationen angepasst.
- Separates Git-Update-Skript ergänzt: Dienstkonfiguration erkennen, neuen Release und venv vorab testen, Konfiguration und Daten sichern, umschalten und bei Fehlern den bisherigen Anwendungspfad wiederherstellen. Konfiguration und Bind-Adresse bleiben erhalten; Update-Anleitung ergänzt.
- Produktionsabhängigkeiten und LF-Zeilenenden für Shellskripte definiert.
- Installer an den Aufbau der NeoFab-ScanLab-Vorlage angepasst: interaktive Standardwerte, validierte Eingaben für Dienstnutzer, Installationspfad, Branch oder Tag und Bind-Adresse/Port, automatischer Clone des öffentlichen Projekt-Repositories sowie abschließende Übersicht mit installiertem Git-Commit.
- Download-Schnellstart ohne vorhandenen Checkout in docs/install.md und scripts/README.md ergänzt. Projektanweisungen um verbindliche Regeln für Git-basierte Installer und passende Anleitungen erweitert.
- `docs/install.md` mit Installation, Zugriff, Konfiguration, Betrieb und Fehlerbehandlung erstellt; README und Roadmap aktualisiert.

**Prüfung:** Bash-Syntax mit `bash -n` und Abbruch ohne root-Rechte geprüft; `git diff --check` ohne Fehler. Versionswert und Dokumentationsverweise abgeglichen. Die neue Webadressen-Ausgabe mit mehreren IPv4, Duplikaten, IPv6, lokalem Zugriff und fehlender IPv4 isoliert erfolgreich geprüft; der geänderte Netzwerkstandard wurde noch nicht erneut im LXC installiert. Laut vom User bereitgestelltem Installationsprotokoll vom 2026-10-20 ist die Debian-13-LXC-Erstinstallation für Commit `a58ee45b6495d130080b2d29e7330b8c6a4277b5` erfolgreich: Python 3.13.5, drei Tests bestanden, systemd-Dienst eingerichtet und lokale HTTP-Prüfung erfolgreich. Bind-Adresse `127.0.0.1:8000`. Browserdarstellung und externer Zugriff sind noch nicht bestätigt. Update-Skript: Bash-Syntax, Abbruch ohne root und Rollback-Steuerung mit simulierten Systembefehlen geprüft (Vorbereitungsfehler, Umschaltfehler, Fehler vor Verschieben und erfolgreicher Abschluss). Vollständiger Update-Praxistest im LXC bleibt offen. Prüfergebnis in Anleitung und Roadmap nachgeführt.

**Commit-Kurzbeschreibung:** Debian-LXC-Installation und Updates mit Sicherung und Anleitung ergänzen

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
