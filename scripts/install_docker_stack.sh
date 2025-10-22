#!/bin/bash

# Installation script for myUplink2mqtt Docker Compose stack
# Installs the Docker Compose configuration to /opt/stacks/myuplink2mqtt
# Usage: sudo ./scripts/install_docker_stack.sh [target_directory]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEFAULT_STACK_DIR="/opt/stacks/myuplink2mqtt"
STACK_DIR="${1:-$DEFAULT_STACK_DIR}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   myUplink2mqtt Docker Compose Stack Installation              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
   echo -e "${RED}✗ This script must be run as root (use sudo)${NC}"
   echo "  Usage: sudo ./scripts/install_docker_stack.sh"
   exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "  Please install Docker from https://docs.docker.com/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker is installed${NC}"

# Check if Docker Compose is available
if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not installed${NC}"
    echo "  Please install Docker Compose:"
    echo "  https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker Compose is available${NC}"
echo ""

# Step 1: Create directories
echo -e "${YELLOW}Step 1: Creating directory structure${NC}"
echo "─────────────────────────────────────────────"

if [ ! -d "$STACK_DIR" ]; then
    mkdir -p "$STACK_DIR"
    echo -e "${GREEN}✓ Created $STACK_DIR${NC}"
else
    echo -e "${YELLOW}⚠ Directory already exists: $STACK_DIR${NC}"
fi

# Step 2: Copy files
echo ""
echo -e "${YELLOW}Step 2: Copying files${NC}"
echo "─────────────────────────────────────────────"

# Check source files exist
if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    echo -e "${RED}✗ docker-compose.yml not found in $PROJECT_ROOT${NC}"
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/Dockerfile" ]; then
    echo -e "${RED}✗ Dockerfile not found in $PROJECT_ROOT${NC}"
    exit 1
fi

# Copy main files
cp "$PROJECT_ROOT/docker-compose.yml" "$STACK_DIR/"
echo -e "${GREEN}✓ Copied docker-compose.yml${NC}"

cp "$PROJECT_ROOT/Dockerfile" "$STACK_DIR/"
echo -e "${GREEN}✓ Copied Dockerfile${NC}"

cp "$PROJECT_ROOT/.env.example" "$STACK_DIR/"
echo -e "${GREEN}✓ Copied .env.example${NC}"

cp "$PROJECT_ROOT/myUplink2mqtt.py" "$STACK_DIR/"
echo -e "${GREEN}✓ Copied myUplink2mqtt.py${NC}"

cp "$PROJECT_ROOT/requirements.txt" "$STACK_DIR/"
echo -e "${GREEN}✓ Copied requirements.txt${NC}"

cp "$PROJECT_ROOT/README.md" "$STACK_DIR/"
echo -e "${GREEN}✓ Copied README.md${NC}"

cp "$PROJECT_ROOT/LICENSE" "$STACK_DIR/"
echo -e "${GREEN}✓ Copied LICENSE${NC}"

# Copy directories
for dir in utils demo tests docs; do
    if [ -d "$PROJECT_ROOT/$dir" ]; then
        rm -rf "$STACK_DIR/$dir"
        cp -r "$PROJECT_ROOT/$dir" "$STACK_DIR/"
        echo -e "${GREEN}✓ Copied $dir directory${NC}"
    fi
done

# Step 3: Setup permissions
echo ""
echo -e "${YELLOW}Step 3: Setting up permissions${NC}"
echo "─────────────────────────────────────────────"

# Get the actual user (in case script is run with sudo)
ACTUAL_USER=${SUDO_USER:-$(whoami)}

# Create .env from template if it doesn't exist
if [ ! -f "$STACK_DIR/.env" ]; then
    cp "$STACK_DIR/.env.example" "$STACK_DIR/.env"
    echo -e "${GREEN}✓ Created .env file (from .env.example)${NC}"
else
    echo -e "${YELLOW}⚠ .env already exists (keeping existing configuration)${NC}"
fi

# Make .env readable but not executable
chmod 640 "$STACK_DIR/.env"

# Make stack directory readable by the user
chmod 755 "$STACK_DIR"

echo ""
echo -e "${GREEN}✓ Stack installed successfully!${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "─────────────────────────────────────────────"
echo ""
echo "1. Configure environment variables:"
echo -e "   ${YELLOW}sudo nano $STACK_DIR/.env${NC}"
echo ""
echo "   Required settings:"
echo "   - MYUPLINK_CLIENT_ID"
echo "   - MYUPLINK_CLIENT_SECRET"
echo ""
echo "2. Start the services:"
echo -e "   ${YELLOW}cd $STACK_DIR && docker-compose up -d${NC}"
echo ""
echo "3. View logs:"
echo -e "   ${YELLOW}cd $STACK_DIR && docker-compose logs -f${NC}"
echo ""
echo "4. Stop services:"
echo -e "   ${YELLOW}cd $STACK_DIR && docker-compose down${NC}"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "  See $STACK_DIR/docs/DOCKER_COMPOSE_GUIDE.md for detailed information"
echo ""
