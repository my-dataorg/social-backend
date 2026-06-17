#!/usr/bin/env bash
# Start social-backend (port 8020) — scaffold
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PORT="${PORT:-8020}"

if [[ ! -f app/main.py ]]; then
  echo "social-backend is still a scaffold (no app/main.py yet)."
  echo "Planned port: ${PORT} · database: social_db"
  exit 1
fi

if [[ ! -f .env ]]; then
  cp .env.example .env 2>/dev/null || true
fi

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

echo "Starting social-backend on http://localhost:${PORT}"
exec uvicorn app.main:app --reload --host 0.0.0.0 --port "$PORT"
