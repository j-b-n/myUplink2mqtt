#!/bin/bash

# Uninstall script for myUplink2mqtt systemd service
# This script removes the service and optionally the virtual environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   myUplink2mqtt systemd Service Uninstall                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
   echo -e "${RED}✗ This script must be run as root (use sudo)${NC}"
   exit 1
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/.venv"
SERVICE_FILE="/etc/systemd/system/myuplink2mqtt.service"

echo -e "${YELLOW}Step 1: Stopping Service${NC}"
echo "─────────────────────────────────────────────"

if systemctl is-active --quiet myuplink2mqtt.service 2>/dev/null; then
    echo "Stopping myuplink2mqtt.service..."
    systemctl stop myuplink2mqtt.service
    sleep 1
    echo -e "${GREEN}✓ Service stopped${NC}"
else
    echo -e "${YELLOW}⚠ Service is not running${NC}"
fi

echo ""

echo -e "${YELLOW}Step 2: Disabling Service${NC}"
echo "─────────────────────────────────────────────"

if systemctl is-enabled --quiet myuplink2mqtt.service 2>/dev/null; then
    systemctl disable myuplink2mqtt.service
    echo -e "${GREEN}✓ Service disabled${NC}"
else
    echo -e "${YELLOW}⚠ Service was not enabled${NC}"
fi

echo ""

echo -e "${YELLOW}Step 3: Removing Service File${NC}"
echo "─────────────────────────────────────────────"

if [ -f "$SERVICE_FILE" ]; then
    rm -f "$SERVICE_FILE"
    echo -e "${GREEN}✓ Service file removed: $SERVICE_FILE${NC}"
else
    echo -e "${YELLOW}⚠ Service file not found: $SERVICE_FILE${NC}"
fi

echo ""

echo -e "${YELLOW}Step 4: Reloading systemd Configuration${NC}"
echo "─────────────────────────────────────────────"
systemctl daemon-reload
echo -e "${GREEN}✓ systemd daemon reloaded${NC}"

echo ""

echo -e "${YELLOW}Step 5: Virtual Environment${NC}"
echo "─────────────────────────────────────────────"

if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment found at: $VENV_DIR"
    read -p "Remove virtual environment? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_DIR"
        echo -e "${GREEN}✓ Virtual environment removed${NC}"
    else
        echo -e "${YELLOW}⚠ Virtual environment kept${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Virtual environment not found at: $VENV_DIR${NC}"
fi

echo ""

echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  UNINSTALL COMPLETE!                          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo "Summary:"
echo -e "  ${GREEN}✓${NC} Service stopped and disabled"
echo -e "  ${GREEN}✓${NC} Service file removed from /etc/systemd/system/"
echo -e "  ${GREEN}✓${NC} systemd daemon reloaded"

if [ -d "$VENV_DIR" ]; then
    echo -e "  ${YELLOW}ℹ${NC} Virtual environment was kept"
    echo ""
    echo "To remove virtual environment manually:"
    echo -e "  ${BLUE}rm -rf $VENV_DIR${NC}"
else
    echo -e "  ${GREEN}✓${NC} Virtual environment removed"
fi

echo ""
echo "The service has been successfully uninstalled."
echo ""
echo "Project files remain at: $SCRIPT_DIR"
echo -e "To reinstall later, run: ${BLUE}sudo ./install_service.sh${NC}"
echo ""
