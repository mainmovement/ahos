#!/bin/sh
# AHOS container entrypoint.
#
# The data directory is a mounted volume, so it can legitimately be empty on
# first run. Bootstrapping here (rather than at image build time) means the
# schema lands in the volume the user actually keeps, and it stays correct
# across image rebuilds. init_databases.py is idempotent.
set -e

if [ ! -f /app/data/e01_discovery.sqlite ]; then
    echo "[entrypoint] initialising databases..."
    python3 /app/scripts/init_databases.py --with-guards
fi

exec "$@"
