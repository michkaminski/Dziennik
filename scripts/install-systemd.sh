#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$ROOT/scripts/install-systemd.sh"
MODE="${1:-user}"
UNIT_NAME="ai-dziennik.service"
TEMPLATE="$ROOT/scripts/ai-dziennik.service"

if [[ ! -f "$TEMPLATE" ]]; then
  echo "[BLAD] Brak $TEMPLATE" >&2
  exit 1
fi

if [[ "$MODE" != "user" && "$MODE" != "system" ]]; then
  echo "Uzycie: $0 [user|system]" >&2
  exit 1
fi

if ! command -v systemctl >/dev/null; then
  echo "[BLAD] Brak systemctl. Ten skrypt jest na Linuxa ze systemd." >&2
  exit 1
fi

render_unit() {
  local wanted_by="$1"
  local service_user="$2"
  local body
  body="$(<"$TEMPLATE")"
  body="${body//@ROOT@/$ROOT}"
  body="${body//@PATH@/$PATH}"
  body="${body//@WANTED_BY@/$wanted_by}"
  body="${body//@SERVICE_USER@/$service_user}"
  printf '%s\n' "$body"
}

enable_and_start() {
  local -a ctl=("$@")
  "${ctl[@]}" daemon-reload
  "${ctl[@]}" enable "$UNIT_NAME"
  if "${ctl[@]}" is-active --quiet "$UNIT_NAME"; then
    "${ctl[@]}" restart "$UNIT_NAME"
  else
    "${ctl[@]}" start "$UNIT_NAME"
  fi
}

install_user() {
  if [[ -z "${XDG_RUNTIME_DIR:-}" && -d "/run/user/$(id -u)" ]]; then
    export XDG_RUNTIME_DIR="/run/user/$(id -u)"
  fi
  if ! systemctl --user show-environment >/dev/null 2>&1; then
    echo "[BLAD] Brak sesji systemd --user. Zaloguj sie na to konto albo: bash $SCRIPT system" >&2
    exit 1
  fi
  if systemctl is-active --quiet "$UNIT_NAME" 2>/dev/null; then
    echo "[BLAD] Dziala juz usluga systemowa $UNIT_NAME. Zatrzymaj: sudo systemctl disable --now $UNIT_NAME" >&2
    exit 1
  fi
  local dest="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
  mkdir -p "$dest"
  chmod +x "$ROOT/run_ai_dziennik.sh"
  render_unit "default.target" "" >"$dest/$UNIT_NAME"
  enable_and_start systemctl --user
  if ! loginctl show-user "$USER" -p Linger --value 2>/dev/null | grep -qx yes; then
    if loginctl enable-linger "$USER"; then
      echo "Linger wlaczone: usluga wstanie przy starcie systemu bez logowania."
    else
      echo "Nie udalo sie wlaczyc linger. Recznie: loginctl enable-linger $USER"
    fi
  fi
  echo "Status: systemctl --user status $UNIT_NAME"
  echo "Logi:   journalctl --user -u ai-dziennik -f"
}

as_target_user() {
  local target_user="$1"
  shift
  if [[ "$(id -un)" == "$target_user" ]]; then
    if [[ -z "${XDG_RUNTIME_DIR:-}" && -d "/run/user/$(id -u)" ]]; then
      export XDG_RUNTIME_DIR="/run/user/$(id -u)"
    fi
    "$@"
    return
  fi
  local uid runtime
  uid="$(id -u "$target_user")"
  runtime="/run/user/$uid"
  if [[ ! -S "$runtime/bus" ]]; then
    return 1
  fi
  sudo -u "$target_user" env XDG_RUNTIME_DIR="$runtime" \
    DBUS_SESSION_BUS_ADDRESS="unix:path=$runtime/bus" \
    "$@"
}

retire_user_service() {
  local target_user="$1"
  local home_dir unit_path
  home_dir="$(getent passwd "$target_user" | cut -d: -f6)"
  if [[ -z "$home_dir" ]]; then
    echo "[BLAD] Nieznany uzytkownik $target_user" >&2
    exit 1
  fi
  if [[ "$(id -un)" == "$target_user" && -n "${XDG_CONFIG_HOME:-}" ]]; then
    unit_path="$XDG_CONFIG_HOME/systemd/user/$UNIT_NAME"
  else
    unit_path="$home_dir/.config/systemd/user/$UNIT_NAME"
  fi
  as_target_user "$target_user" systemctl --user disable --now "$UNIT_NAME" || true
  if [[ -f "$unit_path" ]]; then
    rm -f "$unit_path"
    as_target_user "$target_user" systemctl --user daemon-reload || true
  fi
}

install_system() {
  if [[ "$(id -u)" -ne 0 ]]; then
    if ! command -v sudo >/dev/null; then
      echo "[BLAD] Uruchom jako root: bash $SCRIPT system" >&2
      exit 1
    fi
    exec sudo -E bash "$SCRIPT" system
  fi
  local target_user="${SUDO_USER:-$USER}"
  if [[ "$target_user" == "root" ]]; then
    echo "[BLAD] Uruchom ze swojego konta: bash $SCRIPT system" >&2
    exit 1
  fi
  retire_user_service "$target_user"
  local target_group
  target_group="$(id -gn "$target_user")"
  chmod +x "$ROOT/run_ai_dziennik.sh"
  render_unit "multi-user.target" $'User='"$target_user"$'\nGroup='"$target_group"$'\n' >"/etc/systemd/system/$UNIT_NAME"
  enable_and_start systemctl
  echo "Usluga systemowa $UNIT_NAME, proces jako $target_user."
  echo "Cockpit: Uslugi -> ai-dziennik"
  echo "Status: systemctl status $UNIT_NAME"
  echo "Logi:   journalctl -u ai-dziennik -f"
}

if [[ "$MODE" == "user" ]]; then
  install_user
else
  install_system
fi
