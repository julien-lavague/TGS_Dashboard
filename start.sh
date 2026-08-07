#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

# Activate virtualenv
source "$ROOT/.venv/Scripts/activate"

# Start backend in background (with hot reload)
echo "Starting backend on http://localhost:8000 ..."
cd "$ROOT/backend"
# Force watchfiles into polling mode: on Windows, native filesystem events are
# often missed under OneDrive-synced / Git Bash paths, so --reload silently never
# fires. Polling reliably picks up .py edits at the cost of a small CPU tick.
export WATCHFILES_FORCE_POLLING=true
export WATCHFILES_POLL_DELAY_MS=1000
uvicorn main:app --reload --reload-dir "$ROOT/backend" --port 8000 &
BACKEND_PID=$!

# Start frontend
echo "Starting frontend on http://localhost:3000 ..."
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

# Kill both on Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT INT TERM

echo ""
echo "Both servers are running. Press Ctrl+C to stop."
wait
