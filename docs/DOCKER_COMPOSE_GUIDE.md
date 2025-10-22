# Docker Compose Deployment Guide

This guide explains how to deploy myUplink2mqtt using Docker Compose, either locally or in a centralized `/opt/stacks` directory.

## Overview

Docker Compose deployment provides:

- 🐳 **Containerized Application**: Consistent environment across different systems
- 🔄 **Auto-restart**: Containers automatically restart on failure
- 📦 **Included MQTT Broker**: Optional Mosquitto MQTT broker in the same stack
- 💾 **Persistent Data**: OAuth tokens and MQTT data persist across restarts
- 📊 **Health Checks**: Built-in health monitoring
- 🔒 **Security**: Non-root user execution inside container
- 📝 **Logging**: Structured logging with size limits

## Prerequisites

- **Docker**: 20.10+ (install from [docker.com](https://docs.docker.com/install/))
- **Docker Compose**: 1.29+ (usually included with Docker Desktop; on Linux, install separately if needed)
- **myUplink API Credentials**: Client ID and Secret from [myUplink Portal](https://dev.myuplink.com/)
- **MQTT Broker**: Either use the included Mosquitto service or provide external MQTT broker details

## Quick Start - Local Deployment

### 1. Prepare Configuration

```bash
# Clone the repository
git clone https://github.com/j-b-n/myUplink2mqtt.git
cd myUplink2mqtt

# Create .env file from template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### 2. Configure `.env` File

```bash
# myUplink API - Required
MYUPLINK_CLIENT_ID=your_client_id_here
MYUPLINK_CLIENT_SECRET=your_client_secret_here

# MQTT Configuration
MQTT_BROKER_HOST=mosquitto    # Use 'mosquitto' if using included service
MQTT_BROKER_PORT=1883
# MQTT_USERNAME=optional_user
# MQTT_PASSWORD=optional_pass
MQTT_BASE_TOPIC=myuplink

# Other settings
HA_DISCOVERY_PREFIX=homeassistant
POLL_INTERVAL=300
LOG_LEVEL=INFO
```

### 3. Start Services

```bash
# Build the Docker image
docker-compose build

# Start services in background
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f myuplink2mqtt
```

### 4. Verify Operation

```bash
# Check container is running
docker-compose ps

# View application logs
docker-compose logs myuplink2mqtt

# If using Mosquitto, check MQTT broker
docker-compose logs mosquitto
```

### 5. Stop Services

```bash
# Stop all services (containers remain)
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove everything including volumes
docker-compose down -v
```

## Production Deployment - `/opt/stacks` Installation

For production systems, install the stack to `/opt/stacks/myuplink2mqtt` where it can be managed centrally.

### Installation Steps

1. **Install Stack** (requires sudo):

```bash
cd /path/to/myUplink2mqtt
sudo make install-docker-stack
```

This copies:

- `docker-compose.yml` - Service configuration
- `Dockerfile` - Container build specification
- Application code and documentation

2. **Configure Environment**:

```bash
sudo cp /opt/stacks/myuplink2mqtt/.env.example /opt/stacks/myuplink2mqtt/.env
sudo nano /opt/stacks/myuplink2mqtt/.env
sudo chown $(whoami) /opt/stacks/myuplink2mqtt/.env
```

3. **Start Services**:

```bash
cd /opt/stacks/myuplink2mqtt
docker-compose up -d
```

4. **Verify Operation**:

```bash
cd /opt/stacks/myuplink2mqtt
docker-compose ps
docker-compose logs -f
```

### Managing `/opt/stacks` Installation

```bash
# Start services
cd /opt/stacks/myuplink2mqtt && docker-compose up -d

# Stop services
cd /opt/stacks/myuplink2mqtt && docker-compose down

# View logs
cd /opt/stacks/myuplink2mqtt && docker-compose logs -f

# Restart services
cd /opt/stacks/myuplink2mqtt && docker-compose restart

# Update to new version
cd /opt/stacks/myuplink2mqtt
git pull origin main
docker-compose build
docker-compose up -d
```

## Configuration Reference

### Environment Variables

#### myUplink API (Required)

- `MYUPLINK_CLIENT_ID` - OAuth client ID from [dev.myuplink.com](https://dev.myuplink.com/)
- `MYUPLINK_CLIENT_SECRET` - OAuth client secret

#### MQTT Configuration

- `MQTT_BROKER_HOST` - MQTT broker hostname/IP (default: `mosquitto`)
- `MQTT_BROKER_PORT` - MQTT broker port (default: `1883`)
- `MQTT_USERNAME` - MQTT authentication username (optional)
- `MQTT_PASSWORD` - MQTT authentication password (optional)
- `MQTT_BASE_TOPIC` - Base MQTT topic (default: `myuplink`)

#### Home Assistant Configuration

- `HA_DISCOVERY_PREFIX` - Home Assistant discovery prefix (default: `homeassistant`)

#### Polling Configuration

- `POLL_INTERVAL` - Seconds between API polls (default: `300` = 5 minutes)

#### Logging Configuration

- `LOG_LEVEL` - Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: `INFO`)

## Services

### myuplink2mqtt

Main application service that:

- Polls myUplink API every `POLL_INTERVAL` seconds
- Publishes data to MQTT broker
- Publishes Home Assistant auto-discovery messages
- Automatically restarts on failure

**Resource Limits:**

- CPU: 0.5 cores max
- Memory: 256 MB max

**Restart Policy:** Always restart unless manually stopped

### mosquitto (Optional)

Eclipse Mosquitto MQTT broker service.

**Ports:**

- `1883` - MQTT protocol
- `9001` - WebSocket protocol

**Volumes:**

- `mosquitto_config` - Configuration files
- `mosquitto_data` - Persistent data
- `mosquitto_logs` - Log files

**Health Check:** Automated health monitoring every 30 seconds

## Volumes

### Named Volumes

```yaml
myuplink_tokens: # OAuth token storage (persists across restarts)
mosquitto_config: # Mosquitto configuration
mosquitto_data: # Mosquitto persistent data
mosquitto_logs: # Mosquitto logs
```

### Bind Mounts (Optional)

Mount existing config files:

```yaml
volumes:
  - /home/pi/.myUplink_API_Config.json:/home/appuser/.myUplink_API_Config.json:ro
```

## Using External MQTT Broker

If you don't want to use the included Mosquitto service:

1. **Edit docker-compose.yml**: Comment out the `mosquitto` service and remove `depends_on`

2. **Update .env**:

```bash
MQTT_BROKER_HOST=192.168.1.100    # Your broker's IP
MQTT_BROKER_PORT=1883
```

3. **Restart**:

```bash
docker-compose up -d
```

## Troubleshooting

### Containers Won't Start

```bash
# Check error logs
docker-compose logs

# Rebuild image
docker-compose build --no-cache
docker-compose up -d
```

### OAuth Token Issues

```bash
# OAuth tokens are stored in the myuplink_tokens volume
# To reset tokens, remove the volume (warning: loses stored tokens)
docker-compose down -v
docker-compose up -d
```

### MQTT Connection Refused

```bash
# Check MQTT broker is running
docker-compose ps mosquitto

# Check broker logs
docker-compose logs mosquitto

# Verify connection settings in .env
cat .env | grep MQTT
```

### High Memory Usage

Check resource usage:

```bash
docker stats myuplink2mqtt
```

Reduce polling frequency in `.env`:

```bash
POLL_INTERVAL=600  # Increase to 10 minutes
```

### Viewing Logs

```bash
# Follow real-time logs
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# View logs for specific service
docker-compose logs mosquitto
```

## Updating and Maintenance

### Update Application

```bash
cd /opt/stacks/myuplink2mqtt
git pull origin main
docker-compose build
docker-compose up -d
```

### Backup Data

```bash
# Backup OAuth tokens
docker run --rm -v myuplink2mqtt_myuplink_tokens:/data \
  -v $(pwd):/backup alpine \
  tar czf /backup/myuplink_tokens_backup.tar.gz -C /data .

# Backup MQTT data (if using Mosquitto)
docker run --rm -v myuplink2mqtt_mosquitto_data:/data \
  -v $(pwd):/backup alpine \
  tar czf /backup/mosquitto_backup.tar.gz -C /data .
```

### Clean Up

```bash
# Remove stopped containers
docker-compose rm

# Remove unused volumes
docker volume prune

# Remove unused images
docker image prune
```

## Makefile Commands

The Makefile provides convenient Docker Compose commands:

```bash
make docker-build           # Build Docker image
make docker-up              # Start containers
make docker-down            # Stop containers
make docker-logs            # View logs
make install-docker-stack   # Install to /opt/stacks (requires sudo)
```

## Network Configuration

The Docker Compose setup creates an isolated network `myuplink-net`:

- **Network Driver**: bridge
- **Services**: myuplink2mqtt, mosquitto
- **Service Discovery**: Services can reference each other by name (e.g., `mosquitto`)

### External Network Access

To allow external access to MQTT:

Edit `docker-compose.yml` to change ports:

```yaml
mosquitto:
  ports:
    - "0.0.0.0:1883:1883" # Listen on all interfaces
```

## Security Considerations

### Current Security Features

- ✅ Non-root user execution (UID 1000)
- ✅ Resource limits (CPU, memory)
- ✅ Read-only token storage volume
- ✅ Health monitoring
- ✅ Automatic restart on failure

### Additional Hardening

1. **Run with specific user**:

```bash
export DOCKER_USER_ID=1000
docker-compose up -d
```

2. **Use read-only filesystem** (requires careful setup):

```yaml
read_only: true
tmpfs:
  - /tmp
  - /run
```

3. **Network isolation**: Use separate networks for each service

4. **Secrets management**: Use Docker Secrets (requires Docker Swarm) for sensitive data

## Performance Tuning

### Reduce API Load

Increase polling interval in `.env`:

```bash
POLL_INTERVAL=600  # 10 minutes instead of 5
```

### Reduce Memory Usage

Adjust resource limits in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 128M
```

### Optimize Image Size

Use multi-stage build (already implemented in Dockerfile):

- Builder stage: compiles dependencies
- Runtime stage: only includes runtime requirements

## Development with Docker Compose

### Modify Application Code

When developing, you can mount the source code as a volume:

```bash
# Create docker-compose.override.yml
cat > docker-compose.override.yml << 'EOF'
version: '3.8'
services:
  myuplink2mqtt:
    volumes:
      - .:/app
      - /app/__pycache__
EOF

# Now changes to local code reflect in container
docker-compose up -d
```

### Debug Container

```bash
# Execute shell in running container
docker-compose exec myuplink2mqtt sh

# Or start a new container with shell
docker-compose run --rm myuplink2mqtt sh
```

## Related Documentation

- [Home Assistant Integration](./HOME_ASSISTANT_INTEGRATION.md)
- [Service Setup (Systemd)](./SERVICE_SETUP_README.md)
- [Configuration Guide](./CONFIGURATION_GUIDE.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)
