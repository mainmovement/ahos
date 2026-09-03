#!/usr/bin/env bash
# AHOS Cloud Agent install — dependencies only.
# Must terminate. Must not start servers, migrate databases, or copy secrets.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Python venv + requirements.txt"
python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt

echo "==> Node dependencies"
if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi

mkdir -p .cursor-local/data .cursor-local/reports
echo "==> install.sh complete (no .env secrets, no DB init, no drizzle push)"
