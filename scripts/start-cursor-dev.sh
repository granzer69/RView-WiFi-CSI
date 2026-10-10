#!/usr/bin/env bash
# Starts API + Vite for Cursor Cloud Agents (port forwarding / in-app browser).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export RVIEW_CORS_ORIGINS="${RVIEW_CORS_ORIGINS:-http://127.0.0.1:43123,http://localhost:43123}"

if ! curl -sf --max-time 2 http://127.0.0.1:45231/health >/dev/null 2>&1; then
  echo "[start-cursor-dev] starting API on 0.0.0.0:45231"
  nohup python3 scripts/run_api.py >>/tmp/rview-api.log 2>&1 &
  for _ in $(seq 1 30); do
    if curl -sf --max-time 1 http://127.0.0.1:45231/health >/dev/null 2>&1; then
      break
    fi
    sleep 0.5
  done
fi

echo "[start-cursor-dev] starting Vite on 0.0.0.0:43123 (logs: /tmp/rview-vite.log)"
cd "$ROOT/frontend"
exec npm run dev -- --host 0.0.0.0 --port 43123 >>/tmp/rview-vite.log 2>&1
