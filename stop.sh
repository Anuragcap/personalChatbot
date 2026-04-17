#!/bin/bash

echo "Stopping mlops-group8 services..."
docker compose down

echo "Killing any active devtunnel processes..."
pkill -f "$HOME/bin/devtunnel" 2>/dev/null && echo "  devtunnel stopped" || echo "  devtunnel not running"

echo "Done."
