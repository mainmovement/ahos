#!/usr/bin/env bash
# AHOS Cloud Agent — idempotent dependency bootstrap.
# Runs once after checkout (and again on config changes). Must terminate.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Installing system packages (PostgreSQL 16, python venv)"
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq
sudo apt-get install -y -qq postgresql postgresql-contrib python3-venv

echo "==> Installing Node dependencies (Next.js web command center)"
npm ci

echo "==> Creating Python virtualenv and installing runtime dependencies"
python3 -m venv .venv
./.venv/bin/pip install --quiet --upgrade pip
./.venv/bin/pip install --quiet -r requirements.txt

echo "==> Ensuring .env exists with a local DATABASE_URL"
if [ ! -f .env ]; then
  cp .env.example .env
fi
if ! grep -q '^DATABASE_URL=' .env; then
  printf '\n# ---- Next.js web command center (PostgreSQL) ----\nDATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/app_db\n' >> .env
fi

echo "==> install.sh complete"
