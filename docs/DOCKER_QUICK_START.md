# Docker Compose Setup - Quick Start Guide

Welcome! This guide gets you running myUplink2mqtt with Docker Compose in minutes.

## What You Get

✅ **Containerized Application** - Consistent environment across systems  
✅ **Optional MQTT Broker** - Mosquitto included in the same stack  
✅ **Persistent Data** - OAuth tokens survive container restarts  
✅ **Auto-restart** - Service automatically restarts on failure  
✅ **Easy Management** - Simple commands to start, stop, and monitor

## Prerequisites

You need:

- **Docker** - [Install here](https://docs.docker.com/install/)
- **Docker Compose** - Usually included with Docker (or [install separately](https://docs.docker.com/compose/install/))
- **myUplink Credentials** - Get from [dev.myuplink.com](https://dev.myuplink.com/)

## Quick Start (5 minutes)

### 1. Setup Configuration

```bash
# Copy configuration template
cp .env.example .env

# Edit with your credentials (use your favorite editor)
nano .env
```

Key settings to configure:

```bash
MYUPLINK_CLIENT_ID=your_client_id_here
MYUPLINK_CLIENT_SECRET=your_client_secret_here
MQTT_BROKER_HOST=mosquitto    # Use included Mosquitto
```

### 2. Verify Setup

```bash
# Run validation script
./verify_docker_setup.sh
```

This checks:

- ✓ Docker is installed
- ✓ Configuration files exist
- ✓ Environment variables are set
- ✓ System resources are adequate

### 3. Start Services

```bash
# Build Docker image
make docker-build

# Start containers in background
make docker-up

# Check status
docker-compose ps
```

### 4. Monitor

```bash
# View logs in real-time (Ctrl+C to exit)
make docker-logs

# Or view application logs only
docker-compose logs -f myuplink2mqtt
```

## Making Makefile Commands Easier

If `make` is inconvenient, use Docker Compose directly:

```bash
# Build image
docker-compose build

# Start (background)
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f

# Restart
docker-compose restart
```

## Production Deployment to `/opt/stacks`

For production systems, install to `/opt/stacks` for centralized management:

```bash
# Install (requires sudo)
sudo make install-docker-stack

# Configure
cd /opt/stacks/myuplink2mqtt
sudo nano .env

# Start
docker-compose up -d

# Monitor
docker-compose logs -f
```

## Common Tasks

### Stop Services

```bash
make docker-down
# or
docker-compose stop
```

### Restart Services

```bash
docker-compose restart
```

### Remove Everything (including volumes/data)

```bash
docker-compose down -v
```

### Check Service Status

```bash
docker-compose ps
```

### Execute Command in Container

```bash
docker-compose exec myuplink2mqtt sh
```

## Using External MQTT Broker

If you have an existing MQTT broker:

1. Edit `.env`:

```bash
MQTT_BROKER_HOST=192.168.1.100    # Your broker's IP
MQTT_BROKER_PORT=1883
MQTT_USERNAME=optional_user
MQTT_PASSWORD=optional_pass
```

2. Edit `docker-compose.yml` - comment out the `mosquitto` service:

```yaml
# mosquitto:
#   image: eclipse-mosquitto:2-alpine
#   ...
```

## Troubleshooting

### Service won't start

```bash
# Check logs
docker-compose logs myuplink2mqtt

# Rebuild without cache
docker-compose build --no-cache
docker-compose up -d
```

### MQTT connection refused

```bash
# Is Mosquitto running?
docker-compose ps mosquitto

# Check logs
docker-compose logs mosquitto

# Test connection
docker-compose exec myuplink2mqtt nc -zv mosquitto 1883
```

### High memory usage

```bash
# Check resource usage
docker stats myuplink2mqtt

# Increase poll interval to reduce API calls
# Edit .env: POLL_INTERVAL=600  (10 minutes instead of 5)
```

### Can't connect to Docker daemon

```bash
# Start Docker
sudo systemctl start docker

# Or on macOS
open /Applications/Docker.app
```

## Monitoring Tips

### Real-time Logs

```bash
docker-compose logs -f myuplink2mqtt
```

### Last 50 Lines

```bash
docker-compose logs --tail=50
```

### Resource Usage

```bash
docker stats
```

### Container Health

```bash
docker-compose ps    # Shows health status
```

## Updating to New Version

```bash
cd /opt/stacks/myuplink2mqtt  # or your project directory
git pull origin main
docker-compose build
docker-compose down
docker-compose up -d
```

## Next Steps

1. **View detailed documentation**: See `docs/DOCKER_COMPOSE_GUIDE.md`
2. **Quick reference**: See `docs/DOCKER_QUICK_REFERENCE.md`
3. **Troubleshooting**: See `docs/TROUBLESHOOTING.md`
4. **Configuration options**: See `docs/CONFIGURATION_GUIDE.md`

## Need Help?

- **Check logs**: `docker-compose logs`
- **Run validation**: `./verify_docker_setup.sh`
- **Read documentation**: `docs/DOCKER_COMPOSE_GUIDE.md`
- **GitHub Issues**: [Report problems](https://github.com/j-b-n/myUplink2mqtt/issues)

## Comparison with Systemd Service

| Feature              | Docker Compose                | Systemd Service      |
| -------------------- | ----------------------------- | -------------------- |
| **Setup**            | 5 minutes                     | 10 minutes           |
| **MQTT Broker**      | Optional (Mosquitto included) | External only        |
| **Data Persistence** | Volumes                       | File system          |
| **Isolation**        | Full container isolation      | System-level         |
| **Resource Control** | Built-in limits               | Manual configuration |
| **Updates**          | `docker-compose build`        | Manual/scripts       |
| **Monitoring**       | `docker stats`                | `systemctl status`   |

Both methods are fully supported. Choose based on your needs!

---

**Quick Reference:**

```bash
make help                    # Show all commands
make docker-build           # Build image
make docker-up              # Start services
make docker-down            # Stop services
make docker-logs            # View logs
./verify_docker_setup.sh    # Verify setup
```
