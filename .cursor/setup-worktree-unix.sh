#!/usr/bin/env bash
# AHOS worktree bootstrap (Unix). Runs inside the NEW worktree after Cursor
# creates it. Do not symlink node_modules or .venv to the root worktree.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT_SRC="${ROOT_WORKTREE_PATH:-}"

echo "==> AHOS worktree setup in $PWD"
python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt

if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi

mkdir -p .cursor-local/data .cursor-local/reports
if [ ! -f .env.example ]; then
  echo "WARN: .env.example missing"
elif [ ! -f .env ]; then
  # Copy the template only. Never copy the parent worktree's live .env.
  cp .env.example .env
  printf '\nAHOS_PAPER_ONLY=1\nAHOS_DATA_DIR=%s/.cursor-local/data\n' "$PWD" >> .env
fi

echo "AHOS_DATA_DIR=$PWD/.cursor-local/data"
echo "==> worktree setup complete (no databases initialized, no servers started)"
