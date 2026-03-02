#!/usr/bin/env bash

set -e  


HOST="paffenroth-23.dyn.wpi.edu"
BACKEND_PORT=22008
FRONTEND_PORT=22000
BACKEND_USER="group08"
FRONTEND_USER="group08"

GITHUB_REPO="https://github.com/Anuragcap/personalChatbot.git"
APP_DIR="~/personalChatbot"


MY_KEY="./my_key"

# Path to the original group key (from Canvas) – used for first-time login
GROUP_KEY="./group_key"

# Your HF token (set as env var or paste here)
HF_TOKEN="${HF_TOKEN:-PASTE_YOUR_HF_TOKEN_HERE}"

# ─── COLORS ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'
info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# =============================================================================
# STEP 1: Generate your personal SSH key (if it doesn't exist)
# =============================================================================
info "Step 1: Checking for personal SSH key..."
if [ ! -f "$MY_KEY" ]; then
    info "Generating new ed25519 SSH key pair: my_key / my_key.pub"
    ssh-keygen -t ed25519 -f "$MY_KEY" -C "group08@paffenroth-23" -N ""
    chmod 600 "$MY_KEY"
    chmod 644 "${MY_KEY}.pub"
    info "Key generated."
else
    info "Personal key already exists at $MY_KEY"
fi

MY_PUB_KEY=$(cat "${MY_KEY}.pub")
info "Your public key: $MY_PUB_KEY"

# =============================================================================
# STEP 2: Push your public key to the backend VM and remove the default key
# =============================================================================
info "Step 2: Installing your key on the backend VM and removing default key..."

# Fix permissions on the group key for SSH
chmod 600 "$GROUP_KEY"

ssh -o StrictHostKeyChecking=no \
    -i "$MY_KEY" \
    -p "$BACKEND_PORT" \
    "${BACKEND_USER}@${HOST}" bash <<REMOTE_SETUP
set -e
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add the new key
echo "${MY_PUB_KEY}" > ~/.ssh/authorized_keys

# Remove the default professor's key (rcpaffenroth@paffenroth-23)
sed -i '/rcpaffenroth@paffenroth-23/d' ~/.ssh/authorized_keys

chmod 600 ~/.ssh/authorized_keys
echo "Keys updated. Authorized keys now:"
cat ~/.ssh/authorized_keys
REMOTE_SETUP

info "Key swap complete. Verifying new key works..."
ssh -o StrictHostKeyChecking=no \
    -i "$MY_KEY" \
    -p "$BACKEND_PORT" \
    "${BACKEND_USER}@${HOST}" "echo 'New key login successful!'"

# =============================================================================
# STEP 3: Install environment and deploy backend on the backend VM
# =============================================================================
info "Step 3: Installing dependencies and deploying backend..."

ssh -o StrictHostKeyChecking=no \
    -i "$MY_KEY" \
    -p "$BACKEND_PORT" \
    "${BACKEND_USER}@${HOST}" bash <<DEPLOY_BACKEND
set -e
echo ">>> Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y python3 python3-pip python3-venv git curl

echo ">>> Cloning/updating repo..."
if [ -d ~/personalChatbot ]; then
    cd ~/personalChatbot && git fetch origin && git reset --hard origin/main
else
    git clone ${GITHUB_REPO} ~/personalChatbot
fi

cd ~/personalChatbot

echo ">>> Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo ">>> Installing Python dependencies..."
pip install --upgrade pip
pip install gradio[oauth] transformers torch huggingface_hub itsdangerous fastapi uvicorn

echo ">>> Writing environment variables..."
cat > ~/.env << 'ENVFILE'
HF_TOKEN=${HF_TOKEN}
ENVFILE

echo ">>> Setting up systemd service for backend API..."
sudo bash -c 'cat > /etc/systemd/system/chatbot-backend.service << SERVICE
[Unit]
Description=Group 8 Chatbot Backend API
After=network.target

[Service]
User=${BACKEND_USER}
WorkingDirectory=/home/${BACKEND_USER}/personalChatbot
Environment="PATH=/home/${BACKEND_USER}/personalChatbot/venv/bin"
Environment="HF_TOKEN=${HF_TOKEN}"
ExecStart=/home/${BACKEND_USER}/personalChatbot/venv/bin/uvicorn api_backend:app --host 0.0.0.0 --port 9008
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE'

sudo systemctl daemon-reload
sudo systemctl enable chatbot-backend
sudo systemctl restart chatbot-backend
echo ">>> Backend service started!"
sudo systemctl status chatbot-backend --no-pager

DEPLOY_BACKEND

info "Backend deployment complete!"

# =============================================================================
# STEP 4: Deploy frontend on the shared frontend VM
# =============================================================================
info "Step 4: Deploying frontend on shared frontend VM..."

# Also update frontend key if needed
chmod 600 "$GROUP_KEY"
ssh -o StrictHostKeyChecking=no \
    -i "$GROUP_KEY" \
    -p "$FRONTEND_PORT" \
    "${FRONTEND_USER}@${HOST}" bash <<FRONTEND_KEY
set -e
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "${MY_PUB_KEY}" >> ~/.ssh/authorized_keys
sed -i '/rcpaffenroth@paffenroth-23/d' ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
echo "Frontend key updated."
FRONTEND_KEY

ssh -o StrictHostKeyChecking=no \
    -i "$MY_KEY" \
    -p "$FRONTEND_PORT" \
    "${FRONTEND_USER}@${HOST}" bash <<DEPLOY_FRONTEND
set -e
sudo apt-get install -y python3 python3-pip python3-venv git -qq

if [ -d ~/personalChatbot ]; then
    cd ~/personalChatbot && git fetch origin && git reset --hard origin/main
else
    git clone ${GITHUB_REPO} ~/personalChatbot
fi

cd ~/personalChatbot
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install gradio requests -q

sudo bash -c 'cat > /etc/systemd/system/chatbot-frontend.service << SERVICE
[Unit]
Description=Group 8 Chatbot Frontend
After=network.target

[Service]
User=${FRONTEND_USER}
WorkingDirectory=/home/${FRONTEND_USER}/personalChatbot
Environment="PATH=/home/${FRONTEND_USER}/personalChatbot/venv/bin"
Environment="BACKEND_URL=http://paffenroth-23.dyn.wpi.edu:9008"
ExecStart=/home/${FRONTEND_USER}/personalChatbot/venv/bin/python frontend.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE'

sudo systemctl daemon-reload
sudo systemctl enable chatbot-frontend
sudo systemctl restart chatbot-frontend
echo "Frontend service started!"

DEPLOY_FRONTEND

info "========================================================"
info "  Deployment Complete!"
info "  Backend API:  http://${HOST}:9008"
info "  Frontend:     http://${HOST}:7008"
info "  Backend SSH:  ssh -i my_key -p ${BACKEND_PORT} ${BACKEND_USER}@${HOST}"
info "========================================================"