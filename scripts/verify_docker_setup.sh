#!/bin/bash

# Docker Compose setup validation script
# Checks prerequisites and validates docker-compose configuration
# Usage: ./verify_docker_setup.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

CHECKS_PASSED=0
CHECKS_FAILED=0

# Helper functions
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((CHECKS_PASSED++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((CHECKS_FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

check_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Docker Compose Setup Validation                              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Docker installation
echo -e "${YELLOW}Checking Docker Installation${NC}"
echo "─────────────────────────────────────────────"

if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    check_pass "Docker is installed: $DOCKER_VERSION"
else
    check_fail "Docker is not installed"
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_VERSION=$(docker-compose --version)
    check_pass "Docker Compose is installed: $DOCKER_COMPOSE_VERSION"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_VERSION=$(docker compose version)
    check_pass "Docker Compose is installed: $DOCKER_COMPOSE_VERSION"
else
    check_fail "Docker Compose is not installed"
fi

# Check Docker daemon
echo ""
echo -e "${YELLOW}Checking Docker Daemon${NC}"
echo "─────────────────────────────────────────────"

if docker ps &> /dev/null; then
    check_pass "Docker daemon is running"
else
    check_fail "Cannot connect to Docker daemon"
    check_warn "Try: sudo systemctl start docker"
fi

# Check Docker files exist
echo ""
echo -e "${YELLOW}Checking Docker Files${NC}"
echo "─────────────────────────────────────────────"

if [ -f "Dockerfile" ]; then
    check_pass "Dockerfile found"
else
    check_fail "Dockerfile not found in current directory"
fi

if [ -f "docker-compose.yml" ]; then
    check_pass "docker-compose.yml found"
else
    check_fail "docker-compose.yml not found in current directory"
fi

if [ -f ".env.example" ]; then
    check_pass ".env.example found"
else
    check_fail ".env.example not found"
fi

if [ ! -f ".env" ]; then
    check_warn ".env file not found - Docker Compose will use .env.example"
    check_info "Run: cp .env.example .env"
else
    check_pass ".env configuration file found"
fi

# Check configuration
echo ""
echo -e "${YELLOW}Checking Configuration${NC}"
echo "─────────────────────────────────────────────"

if [ -f ".env" ]; then
    if grep -q "MYUPLINK_CLIENT_ID" .env; then
        CLIENT_ID=$(grep "MYUPLINK_CLIENT_ID" .env | cut -d'=' -f2 | head -1)
        if [ -z "$CLIENT_ID" ] || [ "$CLIENT_ID" = "" ]; then
            check_warn "MYUPLINK_CLIENT_ID is empty"
        else
            check_pass "MYUPLINK_CLIENT_ID is configured"
        fi
    else
        check_warn "MYUPLINK_CLIENT_ID not found in .env"
    fi

    if grep -q "MYUPLINK_CLIENT_SECRET" .env; then
        CLIENT_SECRET=$(grep "MYUPLINK_CLIENT_SECRET" .env | cut -d'=' -f2 | head -1)
        if [ -z "$CLIENT_SECRET" ] || [ "$CLIENT_SECRET" = "" ]; then
            check_warn "MYUPLINK_CLIENT_SECRET is empty"
        else
            check_pass "MYUPLINK_CLIENT_SECRET is configured"
        fi
    else
        check_warn "MYUPLINK_CLIENT_SECRET not found in .env"
    fi

    if grep -q "MQTT_BROKER_HOST" .env; then
        check_pass "MQTT_BROKER_HOST is configured"
    else
        check_warn "MQTT_BROKER_HOST not found"
    fi
fi

# Validate docker-compose.yml
echo ""
echo -e "${YELLOW}Validating docker-compose.yml${NC}"
echo "─────────────────────────────────────────────"

if docker-compose config > /dev/null 2>&1 || docker compose config > /dev/null 2>&1; then
    check_pass "docker-compose.yml is valid"
else
    check_fail "docker-compose.yml validation failed"
fi

# Check required directories
echo ""
echo -e "${YELLOW}Checking Required Directories${NC}"
echo "─────────────────────────────────────────────"

for dir in utils demo tests docs; do
    if [ -d "$dir" ]; then
        check_pass "$dir directory found"
    else
        check_fail "$dir directory not found"
    fi
done

# Check myUplink2mqtt.py
if [ -f "myUplink2mqtt.py" ]; then
    check_pass "myUplink2mqtt.py found"
else
    check_fail "myUplink2mqtt.py not found"
fi

if [ -f "requirements.txt" ]; then
    check_pass "requirements.txt found"
else
    check_fail "requirements.txt not found"
fi

# Check disk space (warning if less than 2GB)
echo ""
echo -e "${YELLOW}Checking System Resources${NC}"
echo "─────────────────────────────────────────────"

AVAILABLE_SPACE=$(df /var/lib/docker -B1 2>/dev/null | tail -1 | awk '{print $4}')
if [ -n "$AVAILABLE_SPACE" ]; then
    AVAILABLE_GB=$((AVAILABLE_SPACE / 1024 / 1024 / 1024))
    if [ "$AVAILABLE_GB" -lt 2 ]; then
        check_warn "Low disk space: ${AVAILABLE_GB}GB available (recommend 2GB+)"
    else
        check_pass "Sufficient disk space: ${AVAILABLE_GB}GB available"
    fi
else
    check_info "Could not determine disk space"
fi

# Summary
echo ""
echo "─────────────────────────────────────────────"
echo -e "${BLUE}Validation Summary${NC}"
echo "─────────────────────────────────────────────"
echo -e "${GREEN}Passed:${NC} $CHECKS_PASSED"
echo -e "${RED}Failed:${NC} $CHECKS_FAILED"

if [ $CHECKS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Ensure MYUPLINK_CLIENT_ID and MYUPLINK_CLIENT_SECRET are set in .env"
    echo "2. Review MQTT configuration"
    echo "3. Start services: docker-compose up -d"
    echo "4. View logs: docker-compose logs -f"
    exit 0
else
    echo ""
    echo -e "${RED}✗ Some checks failed. See above for details.${NC}"
    echo ""
    echo "Common issues:"
    echo "- Docker not running: sudo systemctl start docker"
    echo "- Missing .env file: cp .env.example .env"
    echo "- Docker Compose not installed: see https://docs.docker.com/compose/install/"
    exit 1
fi
