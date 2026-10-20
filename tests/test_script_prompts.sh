#!/usr/bin/env bash
# Nur Eingabeabschnitte ausführen, keine Installation oder Dienständerungen.
set -euo pipefail
cd "$(dirname "$0")/.."
update_prompt=$(sed -n '/^export LC_ALL=C$/,/^HEALTH_PORT=8000$/p' scripts/update-debian13.sh)
for input in '' 'main' ' main ' $'\r' $'main\r' 'feature/parser' 'v0.0.3'; do
    result=$(printf '%s\n' "$input" | bash -c "$update_prompt; printf '%s' \"\$GIT_BRANCH\"")
    case "$input" in
        feature/parser|v0.0.3) expected=$input ;;
        *) expected=main ;;
    esac
    [[ $result == "$expected" ]]
done
for input in '-main' 'main branch' 'main;echo'; do
    if printf '%s\n' "$input" | bash -c "$update_prompt" 2>/dev/null; then
        echo 'Ungültige Eingabe wurde akzeptiert.' >&2
        exit 1
    fi
done
installer_prompt=$(sed -n '/^export LC_ALL=C$/,/^REPO_URL=/p' scripts/install-debian13.sh)
for input in '' ' main ' $'\r' $'main\r'; do
    result=$(printf '%s\n' "$input" | bash -c "$installer_prompt; prompt chosen Branch main; printf '%s' \"\$chosen\"")
    [[ $result == main ]]
done
echo '14 Eingabeprüfungen erfolgreich.'
