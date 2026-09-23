#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$PROJECT_DIR/runtime/app.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "not running"
  exit 0
fi

pid="$(cat "$PID_FILE")"
kill "$pid" 2>/dev/null || true
rm -f "$PID_FILE"
echo "stopped"
