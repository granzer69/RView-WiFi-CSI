#!/usr/bin/env bash
# Single entrypoint for Cursor Cloud: API + Vite without duplicate processes or auto-open browser.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export BROWSER=none
export RVIEW_CURSOR_PREVIEW=1
export RVIEW_CORS_ORIGINS="${RVIEW_CORS_ORIGINS:-http://127.0.0.1:43123,http://localhost:43123}"

cmd="${1:-start}"

vite_pid() {
  pgrep -f 'node.*vite.*--port 43123' 2>/dev/null | head -1 || true
}

api_up() {
  curl -sf --max-time 2 http://127.0.0.1:45231/health >/dev/null 2>&1
}

ui_up() {
  curl -sf --max-time 2 http://127.0.0.1:43123/ >/dev/null 2>&1
}

start_api() {
  if api_up; then
    echo "[dev-stack] API already up on 0.0.0.0:45231"
    return 0
  fi
  echo "[dev-stack] starting API on 0.0.0.0:45231"
  nohup python3 scripts/run_api.py >>/tmp/rview-api.log 2>&1 &
  for _ in $(seq 1 40); do
    if api_up; then
      return 0
    fi
    sleep 0.25
  done
  echo "[dev-stack] ERROR: API did not become healthy (see /tmp/rview-api.log)" >&2
  return 1
}

start_ui() {
  if ui_up; then
    echo "[dev-stack] UI already responding on 0.0.0.0:43123 (not starting duplicate Vite)"
    return 0
  fi
  if [[ -n "$(vite_pid)" ]]; then
    echo "[dev-stack] Vite process exists but not responding; stop stack and retry: bash scripts/dev-stack.sh stop" >&2
    return 1
  fi
  echo "[dev-stack] starting Vite dev on 0.0.0.0:43123 (HMR off for Cursor; logs: /tmp/rview-vite.log)"
  cd "$ROOT/frontend"
  exec npm run dev >>/tmp/rview-vite.log 2>&1
}

start_ui_preview() {
  if ui_up && [[ -n "$(vite_pid)" ]]; then
    echo "[dev-stack] UI already on 43123; stop first if switching modes: bash scripts/dev-stack.sh stop"
    return 0
  fi
  echo "[dev-stack] building frontend (production bundle for stable Cursor preview)…"
  cd "$ROOT/frontend"
  npm run build
  echo "[dev-stack] starting Vite preview on 0.0.0.0:43123 (logs: /tmp/rview-vite.log)"
  exec npm run preview >>/tmp/rview-vite.log 2>&1
}

case "$cmd" in
  start)
    start_api
    start_ui
    ;;
  start-preview)
    start_api
    start_ui_preview
    ;;
  stop)
    echo "[dev-stack] stopping Vite + API"
    pkill -f 'node.*vite.*--port 43123' 2>/dev/null || true
    pkill -f 'scripts/run_api.py' 2>/dev/null || true
    sleep 1
    ;;
  status)
    echo -n "API 45231: "
    if api_up; then echo "ok ($(curl -sf http://127.0.0.1:45231/health | head -c 80)…)"; else echo "down"; fi
    echo -n "UI  43123: "
    if ui_up; then echo "ok (HTTP $(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:43123/))"; else echo "down"; fi
    vp="$(vite_pid)"
    echo "Vite PID: ${vp:-none}"
    ;;
  *)
    echo "Usage: bash scripts/dev-stack.sh {start|start-preview|stop|status}" >&2
    exit 1
    ;;
esac
