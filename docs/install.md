# Installation im Debian-13-LXC

Diese Anleitung installiert WI-PlanArchiv als systemd-Dienst mit Gunicorn. Aktuell stehen das Flask-Grundgerüst und die Startseite zur Verfügung. Datenimport, Datenbank und Zeitsteuerung folgen gemäß [Roadmap](roadmap.md).

## Voraussetzungen

- Bestehender Debian-13-LXC-Container mit systemd, beispielsweise auf Proxmox. Das Skript wird **im Container** als root ausgeführt, nicht auf dem Proxmox-Host.
- Funktionierendes DNS und ausgehender Zugriff auf Debian-Paketquellen, GitHub, raw.githubusercontent.com und PyPI.
- Der gewünschte Stand einschließlich Installer, Tests und Requirements muss auf GitHub veröffentlicht sein. Ein vorheriger Repository-Checkout im Container ist nicht nötig. Für die spätere Quellenanalyse zusätzlich eine berechtigte Netzwerkverbindung zur Datenquelle.
- Als Startgröße sind 1–2 vCPU, 1 GB RAM und 8 GB Speicher vorgesehen; der spätere Archivbedarf ist zusätzlich einzuplanen.

Das Skript erstellt keinen Container und verändert keine Proxmox-, Firewall- oder Netzwerkeinstellungen. Es benötigt keine aktivierten Nesting-Funktionen. Eine Ausführung im Debian-13-LXC wurde in der aktuellen Windows-Entwicklungsumgebung noch nicht geprüft.

## Wohin wird installiert?

Standardmäßig wird das Repository automatisch von `https://github.com/know-how-schmiede/PlanVault.git` nach `/opt/wi-planarchiv` geklont. Die Skripte liegen anschließend unter `/opt/wi-planarchiv/scripts`. Kein separates Übertragen der Anwendung erforderlich.

## Schnellstart als root im Debian-Container

Ausgangssituation: Ein frisch erstellter Debian-13-LXC-Container mit systemd, geöffnet in der Proxmox-Konsole und als root angemeldet.

```bash
# Download vorbereiten
apt-get update
apt-get install -y --no-install-recommends ca-certificates curl

# Installer herunterladen und vor der Ausführung ansehen
curl --fail --show-error --location \
  https://raw.githubusercontent.com/know-how-schmiede/PlanVault/main/scripts/install-debian13.sh \
  --output /root/install-wi-planarchiv.sh
less /root/install-wi-planarchiv.sh

# Interaktive Installation starten
bash /root/install-wi-planarchiv.sh
```

Falls `less` nicht installiert ist, die Datei mit `cat /root/install-wi-planarchiv.sh` ansehen. Das Skript wird erst nach erfolgreichem Download aus einer Datei ausgeführt. Die lokal entwickelten Änderungen müssen zuvor auf GitHub verfügbar sein; diese Anleitung veröffentlicht sie nicht automatisch.

### Abfragen und Standardwerte

Mit Enter den jeweiligen Standard übernehmen:

| Abfrage | Standard | Bedeutung |
| --- | --- | --- |
| Dienstnutzer | `wi-planarchiv` | Neu anzulegendes Systemkonto ohne Login |
| Installationspfad | `/opt/wi-planarchiv` | Neues direktes Unterverzeichnis von `/opt`, ohne Leer- oder Sonderzeichen |
| Git-Branch oder Tag | `main` | Veröffentlichter Stand, der automatisch geklont wird |
| Bind-Adresse | `127.0.0.1` | Nur lokal; alternativ `0.0.0.0` für internes Netzwerk |
| HTTP-Port | `8000` | Freier Port zwischen 1024 und 65535 |

Repository-Adresse, Dienstname, Konfigurations- und Datenverzeichnis bleiben fest. Das Skript unterstützt öffentlich lesbare Branches und Tags. Für einen festgelegten Release-Stand einen veröffentlichten Tag wählen; beliebige Commit-IDs sind keine Eingabeoption. Zum passenden Installer bei einem Tag auch im Download-Link `main` durch diesen Tag ersetzen.

### Ablauf des Skripts

1. Root-Rechte, Debian 13 und systemd prüfen; Einstellungen abfragen und validieren.
2. Vorhandene Installationsziele oder Dienstkonten erkennen und vor Änderungen abbrechen.
3. Git, Python, venv, Zertifikate und curl über apt installieren; Port prüfen.
4. Gewählten Branch oder Tag automatisch nach dem Installationspfad klonen und benötigte Projektdateien prüfen.
5. Dienstnutzer, Konfiguration und Datenbereich anlegen; virtuelle Python-Umgebung mit Flask, Gunicorn und pytest einrichten.
6. Tests unter dem Dienstkonto ausführen, anschließend systemd-Dienst einrichten und starten.
7. Lokale HTTP-Prüfung durchführen und eine Zusammenfassung mit Git-Commit, Pfaden, Bind-Adresse und Betriebsbefehlen ausgeben.

Das System-Python bleibt von pip-Installationen unberührt; dies entspricht dem [Debian-Hinweis zu virtuellen Umgebungen](https://sources.debian.org/src/python3.13/3.13.5-2%2Bdeb13u4/debian/EXTERNALLY-MANAGED.in). Die private Quelladresse wird nicht abgefragt; `LSF_BASE_URL` bleibt leer. Der Git-Checkout ist durch root verwaltet und für das Dienstkonto nur lesbar.

| Pfad | Zweck |
| --- | --- |
| `/opt/wi-planarchiv` | Git-Checkout und `.venv`, durch root verwaltet; Installationspfad wählbar |
| `/etc/wi-planarchiv/app.env` | Laufzeitkonfiguration, für root und Dienstgruppe lesbar |
| `/var/lib/wi-planarchiv` | Reservierter Datenbereich für spätere Archivfunktionen |
| `/etc/systemd/system/wi-planarchiv.service` | Dienstdefinition |

Der Dienst läuft als `wi-planarchiv`, ohne Schreibrechte am Anwendungscode. `NoNewPrivileges` und `StateDirectory` werden gemäß [systemd-Dokumentation](https://www.freedesktop.org/software/systemd/man/256/systemd.exec.html) verwendet. Auf zusätzliche Mount-Namespace-Einschränkungen wird im Grundgerüst für LXC-Kompatibilität verzichtet.

## Zugriff und Konfiguration

Die folgenden Beispiele verwenden die Standardwerte. Bei abweichendem Dienstnutzer, Installationspfad oder Port die Befehle entsprechend anpassen. Dienstname und Konfigurationspfad bleiben gleich.

Standardmäßig lauscht die Anwendung nur auf `127.0.0.1:8000` im Container. Für einen ersten Zugriff vom Arbeitsplatz mit eingerichtetem SSH-Zugang einen Tunnel starten; `CONTAINER_HOST` durch den eigenen Container ersetzen:

```bash
ssh -L 8000:127.0.0.1:8000 root@CONTAINER_HOST
```

Danach im lokalen Browser `http://127.0.0.1:8000` öffnen. Im Footer steht die Version aus `version.py`.

Alternativ als root `/etc/wi-planarchiv/app.env` bearbeiten und in `GUNICORN_CMD_ARGS` die Bind-Adresse auf `0.0.0.0:8000` setzen, wenn direkter Zugriff im berechtigten internen Netz gewünscht ist. Danach den Dienst neu starten. Die gegenwärtige Startseite hat keine Anmeldung. Vor externem Zugriff Netzberechtigungen, Reverse Proxy und TLS einrichten; das Installationsskript veröffentlicht die Anwendung nicht automatisch.

`LSF_BASE_URL` bleibt zunächst leer. Eine später benötigte vertrauliche Quelladresse nur lokal in der Konfigurationsdatei eintragen; siehe [Datenquellenkonfiguration](source-configuration.md). Konfigurationsinhalte nicht in Tickets, Screenshots oder Logs veröffentlichen. Die App lädt `.env` nicht automatisch, der Dienst verwendet die genannte Datei über `EnvironmentFile`.

## Betrieb und Prüfung

```bash
systemctl status wi-planarchiv --no-pager
systemctl restart wi-planarchiv
journalctl -u wi-planarchiv -n 50 --no-pager
curl --fail http://127.0.0.1:8000/
```

Die HTTP-Ausgabe soll die Startseite und den Versionsfooter enthalten. Tests erneut ausführen:

```bash
cd /opt/wi-planarchiv
runuser -u wi-planarchiv -- env PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m pytest -p no:cacheprovider
```

Ein erfolgreicher Start bestätigt nur das Grundgerüst; die Erreichbarkeit der LSF-Quelle und spätere Archivfunktionen sind separat zu verifizieren.

## Wiederholung, Updates und Fehler

Das Skript ist für eine Erstinstallation bestimmt. Existieren Dienstkonto oder Installationsziele bereits, bricht es vor Paketinstallationen ab. Es überschreibt keine bestehende Konfiguration oder Archivdaten. Bei einem späteren Fehler können bereits Pakete, Konto oder Dateien angelegt sein; es gibt keinen automatischen Rollback. Vor erneutem Versuch den lokalen Zustand prüfen und eine unvollständige Installation gezielt bereinigen. Keine Datenverzeichnisse ungeprüft löschen.

Ein automatisches Update ist noch nicht implementiert. Vor einem manuellen Update Konfiguration, Anwendung und gegebenenfalls Archivdaten sichern, den Dienst stoppen, den geprüften Code und die Requirements aktualisieren, Tests ausführen und den Dienst wieder starten. Das Erstinstallationsskript dafür nicht erneut verwenden. Die dokumentierten Versionen in der [Timeline](timeline.md) helfen bei der Zuordnung des installierten Stands.

Bei Startfehlern zunächst Dienststatus und Journal lokal prüfen. Bei Paket- oder Clone-Fehlern DNS, Netzwerk, Paketquellen sowie GitHub-Erreichbarkeit und den gewählten Branch oder Tag prüfen. Ein fehlgeschlagener Clone kann ein Installationsverzeichnis hinterlassen; vor erneutem Versuch gezielt prüfen. Bei fehlgeschlagenen Tests wird der Dienst nicht neu eingerichtet oder gestartet. Das Skript installiert keine Scheduler-Jobs und verändert keine bestehende Datenbank.

## Aufbau und Referenz

Der Aufbau mit Voraussetzungen, Schnellstart, Eingaben mit Standardwerten, Installationsphasen und abschließenden Betriebsbefehlen orientiert sich an den [NeoFab-ScanLab-Setup-Skripten](https://github.com/know-how-schmiede/NeoFab-ScanLab/tree/main/scripts). WI-PlanArchiv bündelt Basis- und Diensteinrichtung in einer Erstinstallation; ein Update-Skript ist noch nicht enthalten.
