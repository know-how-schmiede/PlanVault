# WI-PlanArchiv Setup-Skript für Debian 13

Die Befehle als **root in der Konsole des Debian-13-Containers** ausführen, nicht auf dem Proxmox-Host. Nur die Codeblöcke kopieren, keine Terminal-Eingabeaufforderung. Die gewünschte Version muss zuvor auf GitHub veröffentlicht sein.

**Bereits installiert?** Direkt zu [Vorhandene Installation aktualisieren](#vorhandene-installation-aktualisieren). Für Anfänger erklärt die [Schritt-für-Schritt-Anleitung](../docs/install.md) jede Eingabe und die Erfolgskontrolle.

## Wohin kopieren?

Ein vorheriger Checkout ist nicht erforderlich. Den Installer als root im Debian-13-LXC herunterladen; er klont die Anwendung selbst aus GitHub. Standardziel ist `/opt/wi-planarchiv`.

## Schnellstart

```bash
apt-get update
apt-get install -y --no-install-recommends ca-certificates wget
wget --timeout=30 --tries=3 --output-document=/root/install-wi-planarchiv.sh.download \
  https://raw.githubusercontent.com/know-how-schmiede/PlanVault/main/scripts/install-debian13.sh && \
mv -- /root/install-wi-planarchiv.sh.download /root/install-wi-planarchiv.sh && \
cat /root/install-wi-planarchiv.sh && \
bash /root/install-wi-planarchiv.sh
```

## Hinweise

- Den aktuellen Stand zuerst auf GitHub veröffentlichen. Der Installer installiert den gewählten Remote-Stand, keine unveröffentlichten lokalen Änderungen.
- Mit Enter die Standardwerte für Dienstnutzer, Installationspfad, Branch oder Tag, Bind-Adresse und Port übernehmen.
- Das Skript installiert Abhängigkeiten, klont Git, führt Tests aus und richtet Gunicorn als systemd-Dienst ein.
- Standardmäßig auf `0.0.0.0:8000` gebunden und über die Container-IP im internen Netz erreichbar. Die Abschlussmeldung zeigt die erkannten IPv4-Webadressen mit dem gewählten Port. Mit `127.0.0.1` bleibt der Zugriff auf den Container beschränkt. Vorhandene Installationen werden nicht überschrieben.
- Für vorhandene Installationen das separate Update-Skript verwenden; Konfiguration und Daten bleiben erhalten.

Die vollständige [Installationsanleitung](../docs/install.md) beschreibt Voraussetzungen, Eingaben, Zugriff, Betriebsbefehle und Fehlerbehandlung.

## Vorhandene Installation aktualisieren

Den gesamten folgenden Block als root im Container kopieren. Er lädt das aktuelle Skript herunter, auch wenn noch keine Update-Datei vorhanden ist, zeigt es an und startet es nur bei erfolgreichem Download:

```bash
apt-get update && \
apt-get install -y --no-install-recommends ca-certificates wget && \
wget --timeout=30 --tries=3 --output-document=/root/update-wi-planarchiv.sh.download \
  https://raw.githubusercontent.com/know-how-schmiede/PlanVault/main/scripts/update-debian13.sh && \
mv -- /root/update-wi-planarchiv.sh.download /root/update-wi-planarchiv.sh && \
cat /root/update-wi-planarchiv.sh && \
bash /root/update-wi-planarchiv.sh
```

Bei Branch/Tag Enter für `main` drücken. Bei Port Enter für den bisherigen Standard `8000` drücken, andernfalls den tatsächlich verwendeten Port angeben. Auf die Erfolgsmeldung warten, dann die bisherige Webseite neu laden und die Version im Footer prüfen (für diesen veröffentlichten Stand: V0.0.20). Das Update-Skript erkennt Benutzer und Pfad aus dem Dienst, testet den neuen Stand vor der Umschaltung und sichert die alte Installation. Konfiguration einschließlich Bind-Adresse bleibt erhalten. Bei Fehlern während Neustart oder HTTP-Prüfung wird zum alten Anwendungsstand zurückgekehrt. Sicherungen und Releases werden aufbewahrt. Details und Grenzen stehen in der [Installationsanleitung](../docs/install.md).

Die Eingabeprüfung der Installations- und Update-Skripte entfernt jetzt Leerzeichen am Rand und Wagenrückläufe. 14 isolierte Eingabetests bestehen; der erfolgreiche Serverbetrieb wurde inzwischen vom User bestätigt (siehe [Timeline](../docs/timeline.md)).


Ab V0.0.18 benötigen Installations- und Update-Skript kein `curl`. Der Schnellstart verwendet `wget` nur zum Download; die Anwendung selbst kommt weiterhin über Git. Lokale HTTP-Prüfungen nutzen Python 3 ohne Proxy, mit Timeout und Größenlimit; das Update prüft zusätzlich die exakte Versionsnummer. Ein nicht erfolgreicher Download wird nicht gestartet. Die bestehende Update-Sicherung und Rückkehr zum alten Code bleiben erhalten. Der User hat das erfolgreiche Update auf dem Server nach V0.0.18 bestätigt. Eine erneute Erstinstallation der curl-freien Fassung wurde nicht separat bestätigt.
