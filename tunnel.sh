#!/bin/bash
set -e

DEVTUNNEL="$HOME/bin/devtunnel"

if [ ! -f "$DEVTUNNEL" ]; then
  echo "Error: devtunnel not found at $DEVTUNNEL"
  exit 1
fi

echo "Starting devtunnel for:"
echo "  Frontend  -> port 22111"
echo "  Backend   -> port 22112"
echo "  Grafana   -> port 22113"
echo ""

"$DEVTUNNEL" host \
  -p 22111 \
  -p 22112 \
  -p 22113
