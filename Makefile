.PHONY: help install install-dev lint format test clean check docker-build docker-up docker-down docker-logs install-docker-stack

# Docker configuration
DOCKER_STACK_DIR ?= /opt/stacks/myuplink2mqtt
DOCKER_COMPOSE_FILE := docker/docker-compose.yml

# Detect virtual environment
VENV_DIR := .venv
VENV_ACTIVATE := $(VENV_DIR)/bin/activate
HAS_VENV := $(shell [ -f $(VENV_ACTIVATE) ] && echo 1 || echo 0)

# Set up shell to use virtual environment if it exists
ifeq ($(HAS_VENV),1)
	SHELL := /bin/bash
	.SHELLFLAGS := -ec
	ACTIVATE_VENV := source $(VENV_ACTIVATE) &&
	PYTHON := $(VENV_DIR)/bin/python
	PIP := $(VENV_DIR)/bin/pip
	RUFF := $(VENV_DIR)/bin/ruff
	PYTEST := $(VENV_DIR)/bin/pytest
else
	ACTIVATE_VENV :=
	PYTHON := python
	PIP := pip
	RUFF := ruff
	PYTEST := pytest
endif

help:
	@echo "Available commands:"
	@echo ""
	@echo "  Installation:"
	@echo "  make install       - Install runtime dependencies"
	@echo "  make install-dev   - Install development dependencies"
	@echo ""
	@echo "  Code Quality:"
	@echo "  make lint          - Run ruff linter"
	@echo "  make format        - Format code with ruff formatter"
	@echo "  make format-check  - Check code formatting without applying changes"
	@echo ""
	@echo "  Testing:"
	@echo "  make test          - Run pytest tests"
	@echo "  make test-cov      - Run tests with coverage report"
	@echo "  make check         - Run all checks (lint, format-check, test)"
	@echo ""
	@echo "  Docker Compose:"
	@echo "  make docker-build  - Build Docker image for myuplink2mqtt"
	@echo "  make docker-up     - Start Docker containers (docker-compose up -d)"
	@echo "  make docker-down   - Stop Docker containers (docker-compose down)"
	@echo "  make docker-logs   - View Docker container logs"
	@echo "  make install-docker-stack - Install docker-compose stack to $(DOCKER_STACK_DIR)"
	@echo ""
	@echo "  Maintenance:"
	@echo "  make clean         - Remove build artifacts and cache files"
ifeq ($(HAS_VENV),1)
	@echo ""
	@echo "🐍 Virtual environment detected at $(VENV_DIR)/"
	@echo "   All commands will automatically use the venv"
else
	@echo ""
	@echo "⚠️  No virtual environment detected at $(VENV_DIR)/"
	@echo "   To create one, run: python -m venv $(VENV_DIR)"
endif

install:
	$(ACTIVATE_VENV) $(PIP) install -r requirements.txt

install-dev:
	$(ACTIVATE_VENV) $(PIP) install -r requirements-dev.txt

lint:
	$(ACTIVATE_VENV) $(RUFF) check .

format:
	$(ACTIVATE_VENV) $(RUFF) format .
	$(ACTIVATE_VENV) $(RUFF) check . --fix

format-check:
	$(ACTIVATE_VENV) $(RUFF) format . --check
	$(ACTIVATE_VENV) $(RUFF) check . --select=I

test:
	$(ACTIVATE_VENV) $(PYTEST)

test-cov:
	$(ACTIVATE_VENV) $(PYTEST) --cov=utils --cov-report=html --cov-report=term

check: lint test
	@echo "All checks passed!"

clean:
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov build dist *.egg-info .ruff_cache

# Docker Compose commands
docker-build:
	@echo "Building Docker image..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) build

docker-up:
	@echo "Starting Docker containers..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) up -d
	@echo "Containers started. Use 'make docker-logs' to view logs"

docker-down:
	@echo "Stopping Docker containers..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) down

docker-logs:
	@echo "Following Docker container logs (Ctrl+C to exit)..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) logs -f myuplink2mqtt

install-docker-stack:
	@if [ "$$EUID" -ne 0 ]; then \
		echo "Error: This command requires root privileges. Please run with: sudo make install-docker-stack"; \
		exit 1; \
	fi
	@echo "Installing Docker Compose stack to $(DOCKER_STACK_DIR)..."
	mkdir -p $(DOCKER_STACK_DIR)
	cp $(DOCKER_COMPOSE_FILE) $(DOCKER_STACK_DIR)/
	cp Dockerfile $(DOCKER_STACK_DIR)/
	cp .env.example $(DOCKER_STACK_DIR)/.env.example
	cp -r utils $(DOCKER_STACK_DIR)/
	cp -r demo $(DOCKER_STACK_DIR)/
	cp -r tests $(DOCKER_STACK_DIR)/
	cp -r docs $(DOCKER_STACK_DIR)/
	cp requirements.txt $(DOCKER_STACK_DIR)/
	cp myUplink2mqtt.py $(DOCKER_STACK_DIR)/
	cp README.md $(DOCKER_STACK_DIR)/
	cp LICENSE $(DOCKER_STACK_DIR)/
	@echo ""
	@echo "✓ Stack installed to $(DOCKER_STACK_DIR)"
	@echo ""
	@echo "Next steps:"
	@echo "1. Configure environment: cp $(DOCKER_STACK_DIR)/.env.example $(DOCKER_STACK_DIR)/.env"
	@echo "2. Edit $(DOCKER_STACK_DIR)/.env with your settings"
	@echo "3. Start services: cd $(DOCKER_STACK_DIR) && docker-compose up -d"
	@echo "4. View logs: cd $(DOCKER_STACK_DIR) && docker-compose logs -f"