#!/bin/bash
set -e

echo "Starting mlops-group8 container (backend: 22112, frontend: 22111)..."
docker run -d \
  --name mlops-group8-app \
  -p 22111:7008 \
  -p 22112:9008 \
  -e HF_TOKEN=$HF_TOKEN \
  -e BACKEND_URL=http://localhost:9008 \
  mlops-group8

echo "Starting Grafana OTEL LGTM container..."
docker run --name group09otel-lgtem \
  -p 22113:3000 \
  -p 22114:4317 \
  -p 22115:4318 \
  --rm -d \
  grafana/otel-lgtm

echo ""
echo "Services running:"
echo "  Frontend  -> http://localhost:22111"
echo "  Backend   -> http://localhost:22112"
echo "  Grafana   -> http://localhost:22113"
echo "  OTLP gRPC -> localhost:22114"
echo "  OTLP HTTP -> localhost:22115"
