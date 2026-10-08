#!/usr/bin/env bash
set -eu

APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV="$APP_DIR/.venv"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
DELETE_MARKER="$DATA_HOME/chincheta/.delete-venv-on-exit"

cleanup() {
    if [[ -f "$DELETE_MARKER" ]]; then
        rm -f -- "$DELETE_MARKER"
        rm -rf -- "$VENV"
    fi
}
trap cleanup EXIT
rm -f -- "$DELETE_MARKER"

if [[ ! -x "$VENV/bin/python" ]] \
    || ! "$VENV/bin/python" -c "import PySide6" >/dev/null 2>&1; then
    rm -rf -- "$VENV"
    python3 -m venv "$VENV"
    "$VENV/bin/python" -m pip install --disable-pip-version-check \
        -r "$APP_DIR/requirements.txt"
fi

"$VENV/bin/python" "$APP_DIR/chincheta.py" "$@"
