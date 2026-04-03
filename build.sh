#!/bin/bash
set -e

echo "Building Docker image: mlops-group8"
docker build -t mlops-group8 .
echo "Build complete."
