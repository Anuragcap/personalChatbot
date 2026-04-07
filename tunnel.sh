#!/bin/bash
set -e

DEVTUNNEL="$HOME/bin/devtunnel"
TUNNEL_NAME="mlops-group8"

if [ ! -f "$DEVTUNNEL" ]; then
  echo "Error: devtunnel not found at $DEVTUNNEL"
  exit 1
fi

# # Ensure services are up
# if ! docker compose ps --services --filter "status=running" 2>/dev/null | grep -q frontend; then
#   echo "Services are not running. Starting them first..."
#   docker compose up -d --build
# fi

# Use devtunnel show to check existence — avoids fragile list parsing
if "$DEVTUNNEL" show "$TUNNEL_NAME" > /dev/null 2>&1; then
  echo "Tunnel already exists: $TUNNEL_NAME"
else
  echo "Creating tunnel: $TUNNEL_NAME"
  "$DEVTUNNEL" create --name "$TUNNEL_NAME"
  "$DEVTUNNEL" port create "$TUNNEL_NAME" -p 22111
  "$DEVTUNNEL" port create "$TUNNEL_NAME" -p 22112
  "$DEVTUNNEL" port create "$TUNNEL_NAME" -p 22113
fi

echo ""
echo "Starting tunnel host for: $TUNNEL_NAME"
echo "devtunnel will print the public URLs below once connected."
echo ""
"$DEVTUNNEL" host "$TUNNEL_NAME"
