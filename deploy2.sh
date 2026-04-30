#!/usr/bin/env bash
# =============================================================================
#  deploy.sh — Run this ON the VM after SSH keys are already set up
#  Usage: bash deploy.sh
# =============================================================================

set -e  # exit on any error

# ─── CONFIG ───────────────────────────────────────────────────────────────────
GITHUB_REPO="https://github.com/Anuragcap/personalChatbot.git"
APP_DIR="$HOME/personalChatbot"
VENV_DIR="$APP_DIR/venv"
BACKEND_USER=$(whoami)
BACKEND_PORT="9008"
FRONTEND_PORT="7008"
HF_TOKEN="${HF_TOKEN:-PASTE_YOUR_HF_TOKEN_HERE}"

# ─── COLORS ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'
info()    { echo -e "${GREEN}[INFO]${NC}  $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
step()    { echo -e "\n${GREEN}━━━ $1 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

# =============================================================================
# STEP 1: Pull or clone the repo
# =============================================================================
step "Step 1: Syncing GitHub repo"

if [ -d "$APP_DIR/.git" ]; then
    info "Repo already exists — pulling latest changes..."
    cd "$APP_DIR"
    git fetch origin
    git reset --hard origin/main   # force sync, discard any local changes
    info "Repo updated."
else
    info "Cloning repo for the first time..."
    git clone "$GITHUB_REPO" "$APP_DIR"
    info "Repo cloned to $APP_DIR"
fi

cd "$APP_DIR"

# =============================================================================
# STEP 2: Install system dependencies
# =============================================================================
step "Step 2: Installing system dependencies"

sudo apt-get update -qq
sudo apt-get install -y python3 python3-pip python3-venv git curl
info "System dependencies installed."

# =============================================================================
# STEP 3: Set up Python virtual environment
# =============================================================================
step "Step 3: Setting up virtual environment"

if [ ! -d "$VENV_DIR" ]; then
    info "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    info "Virtual environment already exists, skipping creation."
fi

source "$VENV_DIR/bin/activate"

info "Installing Python dependencies..."
pip install --upgrade pip -q
pip install gradio transformers torch huggingface_hub fastapi uvicorn requests -q

info "Python environment ready."

# =============================================================================
# STEP 4: Write environment variables
# =============================================================================
step "Step 4: Writing environment variables"

cat > "$HOME/.env" << ENVFILE
HF_TOKEN=${HF_TOKEN}
BACKEND_URL=http://localhost:${BACKEND_PORT}
ENVFILE

info ".env file written to $HOME/.env"

# =============================================================================
# STEP 5: Deploy backend as a systemd service
# =============================================================================
step "Step 5: Setting up backend service"

sudo tee /etc/systemd/system/chatbot-backend.service > /dev/null << SERVICE
[Unit]
Description=Group 8 Chatbot Backend API
After=network.target

[Service]
User=${BACKEND_USER}
WorkingDirectory=${APP_DIR}
Environment="PATH=${VENV_DIR}/bin"
Environment="HF_TOKEN=${HF_TOKEN}"
ExecStart=${VENV_DIR}/bin/uvicorn api_backend:app --host 0.0.0.0 --port ${BACKEND_PORT}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable chatbot-backend
sudo systemctl restart chatbot-backend
info "Backend service started on port $BACKEND_PORT"

# =============================================================================
# STEP 6: Deploy frontend as a systemd service
# =============================================================================
step "Step 6: Setting up frontend service"

sudo tee /etc/systemd/system/chatbot-frontend.service > /dev/null << SERVICE
[Unit]
Description=Group 8 Chatbot Frontend
After=network.target chatbot-backend.service

[Service]
User=${BACKEND_USER}
WorkingDirectory=${APP_DIR}
Environment="PATH=${VENV_DIR}/bin"
Environment="BACKEND_URL=http://localhost:${BACKEND_PORT}"
ExecStart=${VENV_DIR}/bin/python frontend.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable chatbot-frontend
sudo systemctl restart chatbot-frontend
info "Frontend service started on port $FRONTEND_PORT"

# =============================================================================
# STEP 7: Verify services are running
# =============================================================================
step "Step 7: Verifying deployment"

sleep 3  # give services a moment to start

check_service() {
    local name=$1
    if sudo systemctl is-active --quiet "$name"; then
        info "$name is running ✓"
    else
        warn "$name failed to start — check logs with: sudo journalctl -u $name -n 50"
    fi
}

check_service chatbot-backend
check_service chatbot-frontend

# =============================================================================
# DONE
# =============================================================================
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
info "Backend API : http://$(hostname -I | awk '{print $1}'):${BACKEND_PORT}"
info "Frontend    : http://$(hostname -I | awk '{print $1}'):${FRONTEND_PORT}"
echo ""
info "Useful commands:"
echo "  sudo systemctl status chatbot-backend"
echo "  sudo systemctl status chatbot-frontend"
echo "  sudo journalctl -u chatbot-backend -f      # live backend logs"
echo "  sudo journalctl -u chatbot-frontend -f     # live frontend logs"
echo ""
