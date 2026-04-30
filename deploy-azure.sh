#!/usr/bin/env bash
# Azure Container Apps deployment script for Group 8 Personal Chatbot
# Prerequisites: Azure CLI installed, logged in (az login), HF_TOKEN set in environment
# Usage: HF_TOKEN=hf_xxx bash deploy-azure.sh

set -euo pipefail

# ─── CONFIGURATION ─────────────────────────────────────────────────────────────
RESOURCE_GROUP="mlops-group8-rg"
LOCATION="eastus"
ACR_NAME="mlopsgroup8acr"          # must be globally unique, lowercase, no hyphens
ENVIRONMENT="mlops-group8-env"
BACKEND_APP="group8-backend"
FRONTEND_APP="group8-frontend"

BACKEND_IMAGE="${ACR_NAME}.azurecr.io/chatbot-backend:latest"
FRONTEND_IMAGE="${ACR_NAME}.azurecr.io/chatbot-frontend:latest"

HF_TOKEN="${HF_TOKEN:?HF_TOKEN env var is required}"
# ───────────────────────────────────────────────────────────────────────────────

echo "=== Step 1: Create Resource Group ==="
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

echo "=== Step 2: Create Azure Container Registry ==="
az acr create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$ACR_NAME" \
  --sku Basic \
  --admin-enabled true

echo "=== Step 3: Build & push images via ACR Tasks (no local Docker needed) ==="
# Build backend
az acr build \
  --registry "$ACR_NAME" \
  --image "chatbot-backend:latest" \
  --file Dockerfile.backend \
  .

# Build frontend
az acr build \
  --registry "$ACR_NAME" \
  --image "chatbot-frontend:latest" \
  --file Dockerfile.frontend \
  .

echo "=== Step 4: Get ACR credentials ==="
ACR_USERNAME=$(az acr credential show --name "$ACR_NAME" --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)

echo "=== Step 5: Create Container Apps Environment ==="
az containerapp env create \
  --name "$ENVIRONMENT" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION"

echo "=== Step 6: Deploy backend Container App ==="
az containerapp create \
  --name "$BACKEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$ENVIRONMENT" \
  --image "$BACKEND_IMAGE" \
  --registry-server "${ACR_NAME}.azurecr.io" \
  --registry-username "$ACR_USERNAME" \
  --registry-password "$ACR_PASSWORD" \
  --target-port 9008 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --secrets "hf-token=${HF_TOKEN}" \
  --env-vars "HF_TOKEN=secretref:hf-token"

BACKEND_URL=$(az containerapp show \
  --name "$BACKEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.configuration.ingress.fqdn" -o tsv)

echo "Backend deployed at: https://${BACKEND_URL}"

echo "=== Step 7: Deploy frontend Container App ==="
az containerapp create \
  --name "$FRONTEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$ENVIRONMENT" \
  --image "$FRONTEND_IMAGE" \
  --registry-server "${ACR_NAME}.azurecr.io" \
  --registry-username "$ACR_USERNAME" \
  --registry-password "$ACR_PASSWORD" \
  --target-port 7008 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --env-vars "BACKEND_URL=https://${BACKEND_URL}"

FRONTEND_URL=$(az containerapp show \
  --name "$FRONTEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.configuration.ingress.fqdn" -o tsv)

echo ""
echo "========================================="
echo "  DEPLOYMENT COMPLETE"
echo "========================================="
echo "  Frontend (Gradio UI): https://${FRONTEND_URL}"
echo "  Backend (FastAPI):    https://${BACKEND_URL}"
echo "  Backend metrics:      https://${BACKEND_URL}/metrics"
echo "  Backend health:       https://${BACKEND_URL}/health"
echo "  Backend API docs:     https://${BACKEND_URL}/docs"
echo "========================================="
echo "  Submit this URL to the class sheet:"
echo "  https://${FRONTEND_URL}"
echo "========================================="
