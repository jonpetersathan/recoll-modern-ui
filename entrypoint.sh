#!/bin/bash
set -e

# Ensure HOME is writable (important when running as arbitrary UID like 2002:2002)
if [ -z "$HOME" ] || [ ! -w "$HOME" ]; then
    export HOME=/tmp
fi

export RECOLL_CONFDIR="${RECOLL_CONFDIR:-/root/.recoll}"
CONFDIR="$RECOLL_CONFDIR"
mkdir -p "$CONFDIR" 2>/dev/null || true

# If recoll.conf does not exist in config directory, copy default template
if [ ! -f "$CONFDIR/recoll.conf" ]; then
    echo "[Recoll Init] No recoll.conf found in $CONFDIR. Copying default configuration from /app/recoll.conf..."
    if [ -f /app/recoll.conf ]; then
        cp /app/recoll.conf "$CONFDIR/recoll.conf"
    fi
fi

# Ensure topdirs is set to /data if missing
if [ -f "$CONFDIR/recoll.conf" ] && [ -w "$CONFDIR/recoll.conf" ]; then
    if ! grep -q "^[[:space:]]*topdirs" "$CONFDIR/recoll.conf"; then
        echo "[Recoll Init] Setting topdirs = /data in $CONFDIR/recoll.conf..."
        echo "topdirs = /data" >> "$CONFDIR/recoll.conf"
    fi
fi

# Ensure recoll-metadata-extractor is accessible
if [ ! -f /usr/local/bin/recoll-metadata-extractor ] && [ -f /app/src/recollweb/extractor_cli.py ]; then
    ln -sf /app/src/recollweb/extractor_cli.py /usr/local/bin/recoll-metadata-extractor
    chmod +x /usr/local/bin/recoll-metadata-extractor 2>/dev/null || true
fi

# If index doesn't exist yet, run initial indexing
if [ ! -d "$CONFDIR/xapiandb" ]; then
    echo "[Recoll Init] Search index not found at $CONFDIR/xapiandb. Building initial index for /data..."
    recollindex -z -c "$CONFDIR"
fi

echo "[Recoll Init] Starting Web UI..."
exec "$@"
