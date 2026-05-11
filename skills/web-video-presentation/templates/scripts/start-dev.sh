#!/usr/bin/env bash
# start-dev.sh — kill any existing process on port 5174, then launch vite.
#
# Usage: bash scripts/start-dev.sh
#   (called automatically via `npm run dev`)
#
# Why: multiple vite instances accumulate when sessions are not cleanly stopped.
# This script ensures only one dev server runs at a time on the fixed port.
set -euo pipefail

PORT=5174

kill_port() {
  local pids
  pids=$(lsof -ti tcp:"$PORT" 2>/dev/null || true)
  if [[ -n "$pids" ]]; then
    echo "▸ Stopping existing process on port $PORT (pid: $pids)"
    echo "$pids" | xargs kill -9 2>/dev/null || true
    sleep 0.3
  fi
}

kill_port
exec npx vite
