#!/bin/bash
set -e

DEVTUNNEL="$HOME/bin/devtunnel"
TUNNEL_NAME="mlops-group8"

if [ ! -f "$DEVTUNNEL" ]; then
  echo "Error: devtunnel not found at $DEVTUNNEL"
  exit 1
fi

# Ensure services are up
if ! docker compose ps --services --filter "status=running" 2>/dev/null | grep -q app; then
  echo "Services are not running. Starting them first..."
  docker compose up -d --build
fi

# Check if a tunnel with this name already exists
echo "Checking for existing tunnel: $TUNNEL_NAME"
TUNNEL_ID=$("$DEVTUNNEL" list 2>/dev/null | grep "$TUNNEL_NAME" | awk '{print $1}')

if [ -z "$TUNNEL_ID" ]; then
  echo "No existing tunnel found. Creating tunnel: $TUNNEL_NAME"
  TUNNEL_ID=$("$DEVTUNNEL" create --name "$TUNNEL_NAME" 2>&1 | grep -oE '[a-z0-9]+-[a-z0-9]+-[a-z0-9]+' | head -1)

  echo "Assigning ports to tunnel: $TUNNEL_ID"
  "$DEVTUNNEL" port create "$TUNNEL_ID" -p 22111
  "$DEVTUNNEL" port create "$TUNNEL_ID" -p 22112
  "$DEVTUNNEL" port create "$TUNNEL_ID" -p 22113
else
  echo "Existing tunnel found: $TUNNEL_ID"
fi

echo ""
echo "Tunnel name : $TUNNEL_NAME"
echo "Tunnel ID   : $TUNNEL_ID"
echo ""
echo "Ports:"
echo "  Frontend  -> https://$TUNNEL_ID-22111.devtunnels.ms"
echo "  Backend   -> https://$TUNNEL_ID-22112.devtunnels.ms"
echo "  Grafana   -> https://$TUNNEL_ID-22113.devtunnels.ms"
echo ""
echo "Starting tunnel host..."
"$DEVTUNNEL" host "$TUNNEL_ID"
