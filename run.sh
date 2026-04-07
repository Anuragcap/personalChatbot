#!/bin/bash
set -e

echo "Starting mlops-group8 services with docker-compose..."
docker compose up -d --build

echo ""
echo "Services running:"
echo "  Frontend (mlops-group8-frontend)      -> http://localhost:22111"
echo "  Backend  (mlops-group8-backend)       -> http://localhost:22112"
echo "  Backend metrics                       -> http://localhost:22112/metrics"
echo "  Grafana  (group08otel-lgtm)           -> http://localhost:22113"
echo "  Node Exporter (host network)          -> http://localhost:22116/metrics"
echo ""
echo "Network: mlopsgroup8 (frontend <-> backend <-> grafana)"
