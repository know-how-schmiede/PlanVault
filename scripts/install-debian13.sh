#!/usr/bin/env bash
# Interaktive Erstinstallation direkt aus GitHub für Debian 13 (LXC).
set -Eeuo pipefail
umask 027
trap 'printf "Installation fehlgeschlagen (Zeile %s). Vor erneutem Versuch Zustand prüfen.\n" "$LINENO" >&2' ERR

if [[ ${EUID} -ne 0 ]]; then
    echo 'Bitte als root im Debian-13-Container ausführen.' >&2
    exit 1
fi
source /etc/os-release
if [[ ${ID:-} != debian || ${VERSION_ID:-} != 13 ]]; then
    echo 'Dieses Skript unterstützt ausschließlich Debian 13.' >&2
    exit 1
fi
if [[ ! -d /run/systemd/system ]]; then
    echo 'Der Container muss mit systemd gestartet sein.' >&2
    exit 1
fi

# Lokale HTTP-Prüfung ohne Proxy, curl oder zusätzliche Python-Pakete.
health_check() {
    python3 - "$1" "${2:-2}" "${3:-}" <<'PY_HEALTH'
import http.client
import re
import sys

connection = None
try:
    port, timeout, expected = int(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
    if not 1 <= port <= 65535 or not 0 < timeout <= 10:
        raise ValueError
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    connection.request("GET", "/")
    response = connection.getresponse()
    body = response.read(1_000_001)
    valid = response.status == 200 and len(body) <= 1_000_000
    if expected:
        valid = valid and re.search(rb"Version V" + re.escape(expected.encode("utf-8")) + rb"(?![0-9.])", body) is not None
    sys.exit(0 if valid else 1)
except (OSError, ValueError, http.client.HTTPException):
    sys.exit(1)
finally:
    if connection is not None:
        connection.close()
PY_HEALTH
}

export LC_ALL=C
normalize_answer() {
    local value=$1
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    printf '%s' "$value"
}
prompt() {
    local variable=$1 label=$2 default=$3 value
    read -r -p "$label [$default]: " value || value=''
    value=$(normalize_answer "$value")
    printf -v "$variable" '%s' "${value:-$default}"
}

REPO_URL=https://github.com/know-how-schmiede/PlanVault.git
APP_USER=wi-planarchiv
APP_DIR=/opt/wi-planarchiv
GIT_BRANCH=${GIT_BRANCH:-main}
LISTEN_HOST=0.0.0.0
LISTEN_PORT=8000
echo '==> WI-PlanArchiv: GitHub-Installation für Debian 13'
prompt APP_USER 'Dienstnutzer' "$APP_USER"
prompt APP_DIR 'Installationspfad unter /opt' "$APP_DIR"
prompt GIT_BRANCH 'Git-Branch oder Tag' "$GIT_BRANCH"
prompt LISTEN_HOST 'Bind-Adresse (127.0.0.1 oder 0.0.0.0)' "$LISTEN_HOST"
prompt LISTEN_PORT 'HTTP-Port' "$LISTEN_PORT"
if [[ ! $APP_USER =~ ^[a-z_][a-z0-9_-]{0,30}$ || $APP_USER == root ]]; then
    echo 'Ungültiger Dienstnutzer.' >&2
    exit 1
fi
if [[ ! $APP_DIR =~ ^/opt/[a-zA-Z0-9_-]+$ ]]; then
    echo 'Installationspfad muss ein direktes Unterverzeichnis von /opt ohne Sonderzeichen sein.' >&2
    exit 1
fi
if [[ ! $GIT_BRANCH =~ ^[a-zA-Z0-9][a-zA-Z0-9._/-]*$ ]]; then
    echo 'Ungültiger Git-Branch oder Tag.' >&2
    exit 1
fi
if [[ $LISTEN_HOST != 127.0.0.1 && $LISTEN_HOST != 0.0.0.0 ]] ||
   [[ ! $LISTEN_PORT =~ ^[1-9][0-9]{0,4}$ ]] ||
   (( LISTEN_PORT < 1024 || LISTEN_PORT > 65535 )); then
    echo 'Bind-Adresse oder Port ungültig; erlaubt sind Ports 1024 bis 65535.' >&2
    exit 1
fi
CONFIG_DIR=/etc/wi-planarchiv
STATE_DIR=/var/lib/wi-planarchiv
UNIT=/etc/systemd/system/wi-planarchiv.service
for target in "$APP_DIR" "$CONFIG_DIR" "$STATE_DIR" "$UNIT"; do
    if [[ -e $target || -L $target ]]; then
        echo 'Installationsziel existiert bereits. Keine Änderungen vorgenommen; siehe docs/install.md.' >&2
        exit 1
    fi
done
if getent passwd "$APP_USER" >/dev/null || getent group "$APP_USER" >/dev/null; then
    echo 'Dienstkonto existiert bereits. Vor Installation manuell prüfen.' >&2
    exit 1
fi

export DEBIAN_FRONTEND=noninteractive
echo '==> Systempakete installieren'
apt-get update
apt-get install -y --no-install-recommends git python3 python3-venv ca-certificates
python3 -c 'import socket, sys; s = socket.socket(); s.bind((sys.argv[1], int(sys.argv[2]))); s.close()' "$LISTEN_HOST" "$LISTEN_PORT"
echo '==> Gewählten Git-Stand herunterladen'
GIT_TERMINAL_PROMPT=0 git clone --depth 1 --single-branch --branch "$GIT_BRANCH" -- "$REPO_URL" "$APP_DIR"
for required in backend/__init__.py version.py requirements.txt requirements-prod.txt tests/test_app.py; do
    if [[ ! -f "$APP_DIR/$required" ]]; then
        echo 'Git-Stand unvollständig. Benötigte Projektdateien müssen zuerst auf GitHub veröffentlicht sein.' >&2
        exit 1
    fi
done
INSTALLED_COMMIT=$(git -C "$APP_DIR" rev-parse HEAD)
useradd --system --user-group --home-dir "$STATE_DIR" --no-create-home --shell /usr/sbin/nologin "$APP_USER"
install -d -m 0750 -o root -g "$APP_USER" "$CONFIG_DIR"
install -d -m 0750 -o "$APP_USER" -g "$APP_USER" "$STATE_DIR"

# Der Dienst darf den durch root verwalteten Git-Checkout nur lesen.
chown -R root:"$APP_USER" "$APP_DIR"
chmod -R u=rwX,g=rX,o= "$APP_DIR"
chmod 0755 "$APP_DIR"
python3 -m venv "$APP_DIR/.venv"
echo '==> Python-Abhängigkeiten installieren'
"$APP_DIR/.venv/bin/python" -m pip install -r "$APP_DIR/requirements-prod.txt" 'pytest>=8,<10'
chown -R root:"$APP_USER" "$APP_DIR/.venv"
chmod -R g+rX,o-rwx "$APP_DIR/.venv"

# Tests unter dem späteren Dienstkonto, ohne Schreibzugriff auf den Code.
cd "$APP_DIR"
echo '==> Anwendung unter dem Dienstkonto testen'
runuser -u "$APP_USER" -- env PYTHONDONTWRITEBYTECODE=1 "$APP_DIR/.venv/bin/python" -m pytest -p no:cacheprovider

cat > "$CONFIG_DIR/app.env" <<ENV
LSF_BASE_URL=
GUNICORN_CMD_ARGS="--bind ${LISTEN_HOST}:${LISTEN_PORT} --workers 2 --timeout 30"
ENV
chown root:"$APP_USER" "$CONFIG_DIR/app.env"
chmod 0640 "$CONFIG_DIR/app.env"

echo '==> Gunicorn als systemd-Dienst einrichten'
cat > "$UNIT" <<SERVICE
[Unit]
Description=WI-PlanArchiv Webanwendung
After=network.target

[Service]
Type=simple
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}
EnvironmentFile=/etc/wi-planarchiv/app.env
Environment=PYTHONDONTWRITEBYTECODE=1
ExecStart=${APP_DIR}/.venv/bin/gunicorn backend:create_app()
Restart=on-failure
RestartSec=5
UMask=0027
NoNewPrivileges=true
StateDirectory=wi-planarchiv
StateDirectoryMode=0750

[Install]
WantedBy=multi-user.target
SERVICE
chmod 0644 "$UNIT"
systemd-analyze verify "$UNIT"
systemctl daemon-reload
systemctl enable --now wi-planarchiv.service

healthy=false
for attempt in {1..15}; do
    if health_check "$LISTEN_PORT" 2; then
        healthy=true
        break
    fi
    sleep 1
done
if [[ $healthy != true ]]; then
    echo 'HTTP-Prüfung fehlgeschlagen. Dienststatus und Journal lokal prüfen.' >&2
    exit 1
fi
WEB_URLS=''
if [[ $LISTEN_HOST == 0.0.0.0 ]]; then
    WEB_URLS=$(hostname -I | awk -v port="$LISTEN_PORT" '
        { for (i = 1; i <= NF; i++) {
            address = $i
            if (address ~ /^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$/ &&
                address !~ /^(127\.|169\.254\.|0\.)/ && !seen[address]++)
                printf "http://%s:%s/\n", address, port
        } }')
    if [[ -z $WEB_URLS ]]; then
        WEB_URLS="Keine Container-IPv4 erkannt; IP mit hostname -I prüfen (Port ${LISTEN_PORT})."
    fi
else
    WEB_URLS="http://127.0.0.1:${LISTEN_PORT}/ (nur im Container; für Fernzugriff SSH-Tunnel verwenden)"
fi
cat <<SUMMARY

============================================================
WI-PlanArchiv: Installation abgeschlossen
------------------------------------------------------------
Git-Stand:       ${GIT_BRANCH}
Commit:          ${INSTALLED_COMMIT}
Dienstnutzer:    ${APP_USER}
Installation:    ${APP_DIR}
Bind-Adresse:    ${LISTEN_HOST}:${LISTEN_PORT}
Webadresse:
${WEB_URLS}
Konfiguration:   ${CONFIG_DIR}/app.env
Dienst:          wi-planarchiv.service
------------------------------------------------------------
systemctl status wi-planarchiv --no-pager
journalctl -u wi-planarchiv -n 50 --no-pager
systemctl restart wi-planarchiv
============================================================
SUMMARY
