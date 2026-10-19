#!/usr/bin/env bash
# Start SPORTOMATYKA AI Dziennik (odpowiednik run_ai_dziennik.bat, venv projektu: .venv).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/.venv"
REQ="$ROOT/requirements.txt"
MARKER="$VENV/.requirements.sha256"

if [[ -x "$VENV/Scripts/python.exe" ]]; then
  PY="$VENV/Scripts/python.exe"
elif [[ -x "$VENV/bin/python" ]]; then
  PY="$VENV/bin/python"
else
  echo "[1/3] Tworzenie .venv ..."
  BASE_PY="$(command -v python3 || command -v python || true)"
  if [[ -z "$BASE_PY" ]]; then
    echo "[BLAD] Brak Python w PATH." >&2
    exit 1
  fi
  "$BASE_PY" -m venv "$VENV"
  if [[ -x "$VENV/Scripts/python.exe" ]]; then
    PY="$VENV/Scripts/python.exe"
  else
    PY="$VENV/bin/python"
  fi
fi

REQ_HASH="$("$PY" -c 'import hashlib, pathlib, sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "$REQ")"
OLD_HASH="$(cat "$MARKER" 2>/dev/null || true)"

if [[ "$REQ_HASH" != "$OLD_HASH" ]]; then
  echo "[2/3] Instalacja requirements ..."
  "$PY" -m pip install --upgrade pip
  "$PY" -m pip install -r "$REQ"
  echo "$REQ_HASH" > "$MARKER"
else
  echo "[2/3] Zaleznosci aktualne."
fi

echo "[3/3] Start ..."
cd "$ROOT"
exec "$PY" "$ROOT/run.py"
