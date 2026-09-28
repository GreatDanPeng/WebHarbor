#!/bin/bash
# Reset the dev instance DB (re-seeds at boot) and restart the dev server.
# Usage: bash reset_dev.sh
set -e
cd "$(dirname "$0")/.."
pkill -f "PORT=43094" 2>/dev/null || true
pkill -f "python3.11 app.py" 2>/dev/null || true
sleep 1
rm -f instance/spothero.db
PORT=43094 nohup python3.11 app.py > /tmp/spothero-dev.log 2>&1 &
for i in $(seq 1 90); do
  sleep 1
  if curl -s -o /dev/null http://127.0.0.1:43094/_health 2>/dev/null; then
    echo "dev server up on 43094"
    exit 0
  fi
done
echo "dev server failed to start"; tail -5 /tmp/spothero-dev.log; exit 1
