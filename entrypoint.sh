#!/bin/sh
set -eu

PORT_FILE="/tmp/gluetun/forwarded_port"

while [ ! -s "$PORT_FILE" ]; do
    echo "Waiting for forwarded port..."
    sleep 2
done

FORWARDED_PORT=$(cat "$PORT_FILE" | tr -d '[:space:]')
echo "Forwarded port is $FORWARDED_PORT"

python3 ./nicotine --headless --port $FORWARDED_PORT
