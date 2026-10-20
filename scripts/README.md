# WI-PlanArchiv Setup-Skript für Debian 13

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

Als root im Container herunterladen, ansehen und nach erfolgreichem Download starten:

```bash
apt-get update && \
apt-get install -y --no-install-recommends ca-certificates wget && \
wget --timeout=30 --tries=3 --output-document=/root/update-wi-planarchiv.sh.download \
  https://raw.githubusercontent.com/know-how-schmiede/PlanVault/main/scripts/update-debian13.sh && \
mv -- /root/update-wi-planarchiv.sh.download /root/update-wi-planarchiv.sh && \
cat /root/update-wi-planarchiv.sh && \
bash /root/update-wi-planarchiv.sh
```

Branch oder Tag und bestehenden HTTP-Port angeben. Das Update-Skript erkennt Benutzer und Pfad aus dem Dienst, testet den neuen Stand vor der Umschaltung und sichert die alte Installation. Konfiguration einschließlich Bind-Adresse bleibt erhalten. Bei Fehlern während Neustart oder HTTP-Prüfung wird zum alten Anwendungsstand zurückgekehrt. Sicherungen und Releases werden aufbewahrt. Details und Grenzen stehen in der [Installationsanleitung](../docs/install.md).

Die Eingabeprüfung der Installations- und Update-Skripte entfernt jetzt Leerzeichen am Rand und Wagenrückläufe. 14 isolierte Eingabetests bestehen; die erneute Prüfung im Zielcontainer steht aus (siehe [Timeline](../docs/timeline.md)).


Ab V0.0.18 benötigen Installations- und Update-Skript kein `curl`. Der Schnellstart verwendet `wget` nur zum Download; die Anwendung selbst kommt weiterhin über Git. Lokale HTTP-Prüfungen nutzen Python 3 ohne Proxy, mit Timeout und Größenlimit; das Update prüft zusätzlich die exakte Versionsnummer. Ein nicht erfolgreicher Download wird nicht gestartet. Die bestehende Update-Sicherung und Rückkehr zum alten Code bleiben erhalten. Die neue Fassung wurde noch nicht im Ziel-LXC ausgeführt.
