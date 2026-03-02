#!/usr/bin/env bash

BACKEND_URL="http://paffenroth-23.dyn.wpi.edu:9008/health"
DEPLOY_SCRIPT="$(dirname "$0")/deploy.sh"
CHECK_INTERVAL=60   # seconds between health checks
MAX_FAILURES=3      # how many consecutive failures before triggering recovery

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"; }

consecutive_failures=0

log "${GREEN}Starting health monitor for Group 8 backend...${NC}"
log "Checking: $BACKEND_URL every ${CHECK_INTERVAL}s"
log "Recovery triggers after ${MAX_FAILURES} consecutive failures."

while true; do
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$BACKEND_URL" 2>/dev/null)

    if [ "$HTTP_STATUS" = "200" ]; then
        if [ "$consecutive_failures" -gt 0 ]; then
            log "${GREEN}Backend recovered! (was down for ${consecutive_failures} check(s))${NC}"
        fi
        consecutive_failures=0
        log "${GREEN}[OK] Backend healthy (HTTP $HTTP_STATUS)${NC}"
    else
        consecutive_failures=$((consecutive_failures + 1))
        log "${RED}[FAIL] Backend unreachable (HTTP ${HTTP_STATUS:-timeout}). Failure ${consecutive_failures}/${MAX_FAILURES}${NC}"

        if [ "$consecutive_failures" -ge "$MAX_FAILURES" ]; then
            log "${YELLOW}[RECOVERY] Threshold reached! Triggering automated deployment...${NC}"
            consecutive_failures=0

            if [ -f "$DEPLOY_SCRIPT" ]; then
                bash "$DEPLOY_SCRIPT" 2>&1 | tee -a monitor_recovery.log
                log "${GREEN}[RECOVERY] Deployment script completed.${NC}"
            else
                log "${RED}[RECOVERY] deploy.sh not found at $DEPLOY_SCRIPT!${NC}"
            fi
        fi
    fi

    sleep "$CHECK_INTERVAL"
done