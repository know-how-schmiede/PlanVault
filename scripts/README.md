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
- Standardmäßig nur unter `127.0.0.1:8000` im Container erreichbar. Vorhandene Installationen werden nicht überschrieben.
- Dies ist ein Erstinstallationsskript; automatisierte Updates sind noch nicht umgesetzt.

Die vollständige [Installationsanleitung](../docs/install.md) beschreibt Voraussetzungen, Eingaben, Zugriff, Betriebsbefehle und Fehlerbehandlung.
