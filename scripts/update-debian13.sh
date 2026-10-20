#!/usr/bin/env bash
# Update mit vorbereiteter Release-Umgebung und Rückkehr zum vorherigen Code.
set -Eeuo pipefail
umask 027

if [[ $EUID -ne 0 ]]; then
    echo 'Bitte als root im Debian-13-Container ausführen.' >&2
    exit 1
fi
source /etc/os-release
[[ ${ID:-} == debian && ${VERSION_ID:-} == 13 && -d /run/systemd/system ]] || {
    echo 'Debian 13 mit systemd erforderlich.' >&2; exit 1;
}
for command in git python3 runuser flock realpath; do
    command -v "$command" >/dev/null || { echo "Befehl fehlt: $command" >&2; exit 1; }
done
exec 9>/run/lock/wi-planarchiv-update.lock
flock -n 9 || { echo 'Ein Update läuft bereits.' >&2; exit 1; }

SERVICE=wi-planarchiv.service
CONFIG=/etc/wi-planarchiv/app.env
STATE=/var/lib/wi-planarchiv
APP_DIR=$(systemctl show "$SERVICE" --property=WorkingDirectory --value)
APP_USER=$(systemctl show "$SERVICE" --property=User --value)
APP_GROUP=$(systemctl show "$SERVICE" --property=Group --value)
[[ $APP_DIR =~ ^/opt/[a-zA-Z0-9_-]+$ && $APP_USER =~ ^[a-z_][a-z0-9_-]{0,30}$ && $APP_USER != root ]] || {
    echo 'Keine unterstützte WI-PlanArchiv-Dienstkonfiguration gefunden.' >&2; exit 1;
}
[[ $APP_GROUP == "$APP_USER" && -d $APP_DIR/.git && -f $CONFIG && -d $STATE ]] || {
    echo 'Installation, Dienstgruppe, Konfiguration oder Datenverzeichnis unvollständig.' >&2; exit 1;
}
EXEC_START=$(systemctl show "$SERVICE" --property=ExecStart --value)
[[ $EXEC_START == *"$APP_DIR/.venv/bin/gunicorn"* && $EXEC_START == *'backend:create_app()'* ]] || {
    echo 'Abweichender Startbefehl; Update abgebrochen.' >&2; exit 1;
}
systemctl is-active --quiet "$SERVICE" || { echo 'Dienst muss vor dem Update laufen.' >&2; exit 1; }
OLD_DIR=$(realpath -e "$APP_DIR")
[[ $(stat -c %u "$OLD_DIR") == 0 ]] || { echo 'Anwendung muss root gehören.' >&2; exit 1; }
[[ -z $(git -C "$OLD_DIR" status --porcelain) ]] || {
    echo 'Lokale Git-Änderungen gefunden; vor dem Update sichern und klären.' >&2; exit 1;
}
if [[ -e $APP_DIR/instance || -e $APP_DIR/.env ]]; then
    echo 'Lokale Laufzeitdaten im Anwendungspfad gefunden; zuerst außerhalb des Checkouts ablegen.' >&2
    exit 1
fi

# ASCII-Prüfung unabhängig von der Container-Locale; Terminal-Randzeichen entfernen.
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
GIT_BRANCH=${GIT_BRANCH:-main}
read -r -p "Git-Branch oder Tag [$GIT_BRANCH]: " answer || answer=''
answer=$(normalize_answer "$answer")
GIT_BRANCH=${answer:-$GIT_BRANCH}
[[ $GIT_BRANCH =~ ^[a-zA-Z0-9][a-zA-Z0-9._/-]*$ ]] || { printf 'Ungültiger Git-Stand: %q (z. B. main).\n' "$GIT_BRANCH" >&2; exit 1; }
HEALTH_PORT=8000
read -r -p "Aktueller HTTP-Port für die Prüfung [$HEALTH_PORT]: " answer || answer=''
answer=$(normalize_answer "$answer")
HEALTH_PORT=${answer:-$HEALTH_PORT}
[[ $HEALTH_PORT =~ ^[1-9][0-9]{0,4}$ ]] && (( HEALTH_PORT >= 1024 && HEALTH_PORT <= 65535 )) || {
    echo 'Ungültiger Port.' >&2; exit 1;
}
# Keine Konfigurationsdatei als Shellcode laden oder vertrauliche Werte ausgeben.
health_check "$HEALTH_PORT" 5 || { echo 'Lokale HTTP-Prüfung vor dem Update fehlgeschlagen.' >&2; exit 1; }
STAMP=$(date -u +%Y%m%dT%H%M%SZ)-$$
RELEASE_ROOT=${APP_DIR}-releases
RELEASE=$RELEASE_ROOT/$STAMP
BACKUP=/var/backups/wi-planarchiv/$STAMP
[[ ! -L $RELEASE_ROOT && ! -L /var/backups/wi-planarchiv ]] || {
    echo 'Release- oder Sicherungsverzeichnis darf kein Symlink sein.' >&2; exit 1;
}
if [[ -e $RELEASE_ROOT ]]; then
    [[ $(stat -c %u "$RELEASE_ROOT") == 0 ]] || { echo 'Release-Verzeichnis muss root gehören.' >&2; exit 1; }
fi
install -d -m 0750 -o root -g "$APP_GROUP" "$RELEASE_ROOT"
install -d -m 0700 /var/backups/wi-planarchiv "$BACKUP"
STOPPED=false
MOVED=false
LINKED=false
COMMITTED=false
recover() {
    local status=$?
    trap - EXIT INT TERM
    if [[ $COMMITTED != true && $STOPPED == true ]]; then
        echo 'Update fehlgeschlagen; vorherigen Anwendungsstand wiederherstellen.' >&2
        systemctl stop "$SERVICE" || true
        if [[ $LINKED == true ]]; then
            mv -T -- "$APP_DIR" "$BACKUP/failed-release-link" || { echo 'Rollback fehlgeschlagen; Dienst bleibt gestoppt.' >&2; exit 1; }
        fi
        if [[ $MOVED == true ]]; then
            mv -T -- "$BACKUP/application" "$APP_DIR" || { echo 'Rollback fehlgeschlagen; Dienst bleibt gestoppt.' >&2; exit 1; }
        fi
        systemctl start "$SERVICE" || echo 'Vorheriger Dienst konnte nicht gestartet werden; Journal prüfen.' >&2
    fi
    if (( status != 0 )); then
        echo "Update abgebrochen. Sicherung: $BACKUP; vorbereiteter Stand: $RELEASE" >&2
    fi
    exit "$status"
}
trap recover EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo '==> Neuen Git-Stand und isolierte Python-Umgebung vorbereiten'
GIT_TERMINAL_PROMPT=0 git clone --depth 1 --single-branch --branch "$GIT_BRANCH" -- \
    https://github.com/know-how-schmiede/PlanVault.git "$RELEASE"
for required in backend/__init__.py version.py requirements-prod.txt tests/test_app.py; do
    [[ -f $RELEASE/$required ]] || { echo 'Git-Stand unvollständig.' >&2; exit 1; }
done
NEW_COMMIT=$(git -C "$RELEASE" rev-parse HEAD)
OLD_COMMIT=$(git -C "$OLD_DIR" rev-parse HEAD)
python3 -m venv "$RELEASE/.venv"
"$RELEASE/.venv/bin/python" -m pip install -r "$RELEASE/requirements-prod.txt" 'pytest>=8,<10'
chown -R root:"$APP_GROUP" "$RELEASE"
chmod -R u=rwX,g=rX,o= "$RELEASE"
echo '==> Neuen Stand unter dem Dienstkonto testen'
cd "$RELEASE"
runuser -u "$APP_USER" -- env PYTHONDONTWRITEBYTECODE=1 "$RELEASE/.venv/bin/python" -m pytest -p no:cacheprovider
EXPECTED_VERSION=$(runuser -u "$APP_USER" -- env PYTHONDONTWRITEBYTECODE=1 \
    "$RELEASE/.venv/bin/python" -c 'from version import __version__; print(__version__)')
[[ $EXPECTED_VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo 'Ungültige Anwendungsversion.' >&2; exit 1; }

echo '==> Dienst stoppen und bisherigen Stand sichern'
STOPPED=true
systemctl stop "$SERVICE"
cp -a -- /etc/wi-planarchiv "$BACKUP/configuration"
cp -a -- "$STATE" "$BACKUP/state"
systemctl cat "$SERVICE" > "$BACKUP/service.txt"
printf '%s\n' "$OLD_COMMIT" > "$BACKUP/previous-commit"
mv -T -- "$APP_DIR" "$BACKUP/application"
MOVED=true
# Der Release-Pfad bleibt unverändert, damit venv-Shebangs gültig bleiben.
ln -s -- "$RELEASE" "$APP_DIR"
LINKED=true
echo '==> Dienst mit unveränderter Konfiguration starten'
systemctl start "$SERVICE"
healthy=false
for attempt in {1..15}; do
    if systemctl is-active --quiet "$SERVICE" &&
       health_check "$HEALTH_PORT" 2 "$EXPECTED_VERSION"; then
        healthy=true
        break
    fi
    sleep 1
done
[[ $healthy == true ]] || { echo 'HTTP-Prüfung fehlgeschlagen.' >&2; exit 1; }
COMMITTED=true
cat <<SUMMARY

============================================================
WI-PlanArchiv: Update abgeschlossen
Alter Commit:    $OLD_COMMIT
Neuer Commit:    $NEW_COMMIT
Version:         V$EXPECTED_VERSION
Git-Stand:       $GIT_BRANCH
Anwendung:       $APP_DIR
Release:         $RELEASE
Sicherung:       $BACKUP
Konfiguration:   $CONFIG (unverändert, einschließlich Bind-Adresse)
Prüfadresse:     http://127.0.0.1:$HEALTH_PORT/
------------------------------------------------------------
systemctl status wi-planarchiv --no-pager
journalctl -u wi-planarchiv -n 50 --no-pager
============================================================
SUMMARY
