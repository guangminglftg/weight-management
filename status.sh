#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$PROJECT_DIR/runtime/app.pid"

if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "running: $(cat "$PID_FILE")"
  curl -fsS -o /dev/null -w "health: HTTP %{http_code}\n" http://127.0.0.1:7862/ || true
else
  echo "stopped"
fi
