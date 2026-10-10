#!/usr/bin/env bash
# Cursor environment.json `start` hook — delegates to dev-stack (no external browser).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec bash "$ROOT/scripts/dev-stack.sh" start
