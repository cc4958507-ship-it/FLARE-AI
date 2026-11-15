#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if ! docker info >/dev/null 2>&1; then
  echo 'Please install and start Docker Desktop, then run this file again.'
  read -r -p 'Press Enter to close.'
  exit 1
fi
if [[ ! -f .env ]]; then cp .env.example .env; fi
docker compose up --build -d --wait
if command -v open >/dev/null 2>&1; then open http://localhost:8100; fi
echo 'FLARE AI is running at http://localhost:8100'
