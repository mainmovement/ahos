#!/usr/bin/env bash
# AHOS Cloud Agent — per-boot service reconciliation.
# Starts PostgreSQL, ensures the database + schema exist, and initializes the
# Python SQLite stores. Idempotent and safe to re-run on every boot.
set -euo pipefail

cd "$(dirname "$0")/.."

# Self-heal: when booting from a prebuilt snapshot the `install` phase is skipped,
# so make sure the web stack's Node dependencies are actually present before we
# rely on drizzle-kit. Cheap no-op when node_modules is already complete.
if [ ! -d node_modules/drizzle-orm ] || [ ! -d node_modules/drizzle-kit ]; then
  echo "==> node_modules incomplete; running npm ci"
  npm ci
fi

# Self-heal the Python virtualenv the same way.
if [ ! -x ./.venv/bin/python ]; then
  echo "==> Python virtualenv missing; recreating"
  python3 -m venv .venv
  ./.venv/bin/pip install --quiet --upgrade pip
  ./.venv/bin/pip install --quiet -r requirements.txt
fi

echo "==> Starting PostgreSQL 16 cluster"
sudo pg_ctlcluster 16 main start 2>/dev/null || true

echo "==> Waiting for PostgreSQL to accept connections"
for _ in $(seq 1 30); do
  if sudo -u postgres psql -tAc 'SELECT 1' >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "==> Ensuring role password and app_db database"
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';" >/dev/null 2>&1 || true
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='app_db'" | grep -q 1; then
  sudo -u postgres createdb app_db
fi

echo "==> Applying Drizzle schema (idempotent push)"
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/app_db \
  npx drizzle-kit push --config=drizzle.config.json

echo "==> Initializing Python SQLite stores"
if [ -x ./.venv/bin/python ]; then
  ./.venv/bin/python scripts/init_databases.py --with-guards || true
fi

echo "==> start.sh complete"
