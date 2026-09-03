#!/usr/bin/env bash
# AHOS Cloud Agent start — do not launch product runtimes or mutate evidence.
# Install already created venvs; this script only self-heals missing deps.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -x ./.venv/bin/python ]; then
  echo "==> recreating Python venv"
  python3 -m venv .venv
  ./.venv/bin/pip install --upgrade pip
  ./.venv/bin/pip install -r requirements.txt
fi

if [ ! -d node_modules/next ]; then
  echo "==> node_modules incomplete; npm ci/install"
  if [ -f package-lock.json ]; then npm ci; else npm install; fi
fi

export AHOS_PAPER_ONLY="${AHOS_PAPER_ONLY:-1}"
echo "AHOS engineering environment ready."
echo "PAPER_ONLY=${AHOS_PAPER_ONLY}"
echo "Not started: Next.js, Postgres, SQLite init, Telegram, n8n, observation daemon."
echo "Start services explicitly in an isolated data dir when a task needs them."
