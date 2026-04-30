#!/bin/bash

echo "Stopping containers..."

for NAME in mlops-group8-app group08otel-lgtem; do
  if docker ps -q --filter "name=^${NAME}$" | grep -q .; then
    docker stop "$NAME" && echo "  Stopped: $NAME"
  else
    echo "  Not running: $NAME"
  fi
done

echo "Killing any active devtunnel processes..."
pkill -f "$HOME/bin/devtunnel" 2>/dev/null && echo "  devtunnel stopped" || echo "  devtunnel not running"

echo "Done."
