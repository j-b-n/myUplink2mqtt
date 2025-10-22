#!/bin/bash

# Setup script for myUplink2mqtt systemd service
# This script automates the installation of the service on Raspberry Pi

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   myUplink2mqtt systemd Service Setup                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
   echo -e "${RED}✗ This script must be run as root (use sudo)${NC}"
   exit 1
fi

# Check if myUplink2mqtt.service exists
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVICE_FILE="$SCRIPT_DIR/myuplink2mqtt.service"

if [ ! -f "$SERVICE_FILE" ]; then
    echo -e "${RED}✗ Service file not found: $SERVICE_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found service file${NC}"
echo ""

# Step 1: Verify prerequisites
echo -e "${YELLOW}Step 1: Checking Prerequisites${NC}"
echo "─────────────────────────────────────────────"

# Check OAuth config
# Note: Get the actual user's home directory (not root's when using sudo)
ACTUAL_USER=${SUDO_USER:-$(whoami)}
ACTUAL_HOME=$(eval echo "~$ACTUAL_USER")
OAUTH_CONFIG_FILE="$ACTUAL_HOME/.myUplink_API_Config.json"

if [ -f "$OAUTH_CONFIG_FILE" ]; then
    echo -e "${GREEN}✓ OAuth config file found: $OAUTH_CONFIG_FILE${NC}"
elif [ -n "$MYUPLINK_CLIENT_ID" ] && [ -n "$MYUPLINK_CLIENT_SECRET" ]; then
    echo -e "${GREEN}✓ OAuth environment variables set${NC}"
else
    echo -e "${YELLOW}⚠ OAuth credentials not found!${NC}"
    echo "  Please ensure one of the following is configured:"
    echo "  1. $OAUTH_CONFIG_FILE with credentials"
    echo "  2. Environment variables: MYUPLINK_CLIENT_ID, MYUPLINK_CLIENT_SECRET"
    read -p "  Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Setup cancelled${NC}"
        exit 1
    fi
fi

# Determine which Python to use (prefer venv if it exists)
PYTHON_CMD="python3"
USING_VENV=false

if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_CMD="$SCRIPT_DIR/.venv/bin/python"
    USING_VENV=true
    echo -e "${GREEN}✓ Virtual environment detected, will use: $PYTHON_CMD${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment not found, creating one...${NC}"
    if python3 -m venv "$SCRIPT_DIR/.venv"; then
        PYTHON_CMD="$SCRIPT_DIR/.venv/bin/python"
        USING_VENV=true
        echo -e "${GREEN}✓ Virtual environment created successfully${NC}"
    else
        echo -e "${RED}✗ Failed to create virtual environment${NC}"
        exit 1
    fi
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python3 not found${NC}"
    exit 1
fi

echo "Checking Python dependencies..."

if [ "$USING_VENV" = true ]; then
    # Check packages in virtual environment
    MISSING_PACKAGES=false
    $PYTHON_CMD -c "import paho.mqtt.client" 2>/dev/null && echo -e "${GREEN}✓ paho-mqtt installed${NC}" || { echo -e "${RED}✗ paho-mqtt not found${NC}"; MISSING_PACKAGES=true; }
    $PYTHON_CMD -c "import requests_oauthlib" 2>/dev/null && echo -e "${GREEN}✓ requests-oauthlib installed${NC}" || { echo -e "${RED}✗ requests-oauthlib not found${NC}"; MISSING_PACKAGES=true; }
    $PYTHON_CMD -c "import myuplink" 2>/dev/null && echo -e "${GREEN}✓ myuplink installed${NC}" || { echo -e "${RED}✗ myuplink not found${NC}"; MISSING_PACKAGES=true; }
    $PYTHON_CMD -c "import aiohttp" 2>/dev/null && echo -e "${GREEN}✓ aiohttp installed${NC}" || { echo -e "${RED}✗ aiohttp not found${NC}"; MISSING_PACKAGES=true; }
    
    # If packages are missing, install them from requirements.txt
    if [ "$MISSING_PACKAGES" = true ]; then
        echo ""
        echo "Installing missing packages from requirements.txt..."
        PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
        if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
            $SCRIPT_DIR/.venv/bin/pip install -r "$PROJECT_ROOT/requirements.txt" --quiet
            echo -e "${GREEN}✓ Packages installed from requirements.txt${NC}"
        else
            echo -e "${RED}✗ requirements.txt not found at $PROJECT_ROOT/requirements.txt${NC}"
            exit 1
        fi
    fi
else
    # Check packages in system Python
    python3 -c "import paho.mqtt.client" 2>/dev/null && echo -e "${GREEN}✓ paho-mqtt installed${NC}" || echo -e "${YELLOW}⚠ paho-mqtt not found${NC}"
    python3 -c "import requests_oauthlib" 2>/dev/null && echo -e "${GREEN}✓ requests-oauthlib installed${NC}" || echo -e "${YELLOW}⚠ requests-oauthlib not found${NC}"
    python3 -c "import myuplink" 2>/dev/null && echo -e "${GREEN}✓ myuplink installed${NC}" || echo -e "${YELLOW}⚠ myuplink not found${NC}"
    python3 -c "import aiohttp" 2>/dev/null && echo -e "${GREEN}✓ aiohttp installed${NC}" || echo -e "${YELLOW}⚠ aiohttp not found${NC}"
fi

echo -e "${GREEN}✓ Python3 found: $($PYTHON_CMD --version)${NC}"

echo ""

# Step 2: Test manual execution
echo -e "${YELLOW}Step 2: Testing Manual Execution${NC}"
echo "─────────────────────────────────────────────"
echo "Running: $PYTHON_CMD $SCRIPT_DIR/myUplink2mqtt.py --show-config"
echo ""

if $PYTHON_CMD "$SCRIPT_DIR/myUplink2mqtt.py" --show-config 2>&1 | head -20; then
    echo ""
    echo -e "${GREEN}✓ Script executed successfully${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠ Script execution had issues (see output above)${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Setup cancelled${NC}"
        exit 1
    fi
fi

echo ""

# Step 3: Copy service file
echo -e "${YELLOW}Step 3: Installing Service File${NC}"
echo "─────────────────────────────────────────────"
cp "$SERVICE_FILE" /etc/systemd/system/myuplink2mqtt.service
echo -e "${GREEN}✓ Service file copied to /etc/systemd/system/${NC}"

# Set proper permissions
chmod 644 /etc/systemd/system/myuplink2mqtt.service
echo -e "${GREEN}✓ Permissions set correctly${NC}"

echo ""

# Step 4: Reload systemd
echo -e "${YELLOW}Step 4: Reloading systemd Configuration${NC}"
echo "─────────────────────────────────────────────"
systemctl daemon-reload
echo -e "${GREEN}✓ systemd daemon reloaded${NC}"

echo ""

# Step 5: Enable service
echo -e "${YELLOW}Step 5: Enabling Service for Auto-Start${NC}"
echo "─────────────────────────────────────────────"
systemctl enable myuplink2mqtt.service
echo -e "${GREEN}✓ Service enabled for auto-start on boot${NC}"

echo ""

# Step 6: Start service
echo -e "${YELLOW}Step 6: Starting Service${NC}"
echo "─────────────────────────────────────────────"
systemctl start myuplink2mqtt.service
sleep 2

if systemctl is-active --quiet myuplink2mqtt.service; then
    echo -e "${GREEN}✓ Service started successfully${NC}"
else
    echo -e "${RED}✗ Service failed to start${NC}"
    echo ""
    echo "Check logs with:"
    echo "  sudo journalctl -u myuplink2mqtt.service -n 20"
    exit 1
fi

echo ""

# Step 7: Show status
echo -e "${YELLOW}Step 7: Service Status${NC}"
echo "─────────────────────────────────────────────"
systemctl status myuplink2mqtt.service --no-pager | head -20

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    SETUP COMPLETE!                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo "Next steps:"
echo ""
echo "1. View live logs:"
echo -e "   ${BLUE}sudo journalctl -u myuplink2mqtt.service -f${NC}"
echo ""
echo "2. Check service status:"
echo -e "   ${BLUE}sudo systemctl status myuplink2mqtt.service${NC}"
echo ""
echo "3. Stop the service:"
echo -e "   ${BLUE}sudo systemctl stop myuplink2mqtt.service${NC}"
echo ""
echo "4. For more information, see:"
echo -e "   ${BLUE}$SCRIPT_DIR/SYSTEMD_SERVICE_SETUP.md${NC}"
echo ""
