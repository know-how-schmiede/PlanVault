# WI-PlanArchiv Setup-Skript für Debian 13

## Wohin kopieren?

Ein vorheriger Checkout ist nicht erforderlich. Den Installer als root im Debian-13-LXC herunterladen; er klont die Anwendung selbst aus GitHub. Standardziel ist `/opt/wi-planarchiv`.

## Schnellstart

```bash
apt-get update
apt-get install -y --no-install-recommends ca-certificates curl
curl --fail --show-error --location \
  https://raw.githubusercontent.com/know-how-schmiede/PlanVault/main/scripts/install-debian13.sh \
  --output /root/install-wi-planarchiv.sh
cat /root/install-wi-planarchiv.sh
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
curl --fail --show-error --location \
  https://raw.githubusercontent.com/know-how-schmiede/PlanVault/main/scripts/update-debian13.sh \
  --output /root/update-wi-planarchiv.sh
cat /root/update-wi-planarchiv.sh
bash /root/update-wi-planarchiv.sh
```

Branch oder Tag und bestehenden HTTP-Port angeben. Das Update-Skript erkennt Benutzer und Pfad aus dem Dienst, testet den neuen Stand vor der Umschaltung und sichert die alte Installation. Konfiguration einschließlich Bind-Adresse bleibt erhalten. Bei Fehlern während Neustart oder HTTP-Prüfung wird zum alten Anwendungsstand zurückgekehrt. Sicherungen und Releases werden aufbewahrt. Details und Grenzen stehen in der [Installationsanleitung](../docs/install.md).
