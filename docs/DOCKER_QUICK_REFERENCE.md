# Docker Compose Quick Reference

Quick reference guide for common Docker Compose commands and operations.

## Installation

```bash
# Install Docker Compose stack to /opt/stacks
sudo make install-docker-stack

# Or manually with script
sudo ./scripts/install_docker_stack.sh
```

## Basic Operations

### Starting Services

```bash
# Start services in background
docker-compose up -d

# Start with verbose output
docker-compose up

# Build and start
docker-compose up -d --build

# Start specific service
docker-compose up -d myuplink2mqtt
```

### Stopping Services

```bash
# Stop running containers (keep data)
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove everything including volumes (WARNING: loses data)
docker-compose down -v

# Restart services
docker-compose restart
```

## Viewing Status and Logs

```bash
# Show running containers
docker-compose ps

# Show logs from all services
docker-compose logs

# Follow logs in real-time (Ctrl+C to exit)
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# View logs for specific service
docker-compose logs myuplink2mqtt

# Follow logs for specific service
docker-compose logs -f myuplink2mqtt
```

## Configuration

### Environment Variables

```bash
# Copy template to create .env file
cp .env.example .env

# Edit configuration
nano .env

# Load from specific .env file
docker-compose --env-file .env.custom up -d
```

### Viewing Configuration

```bash
# Show current environment
docker-compose config

# Validate configuration
docker-compose config --quiet

# Show all environment variables
docker-compose exec myuplink2mqtt env
```

## Container Interaction

### Execute Commands

```bash
# Open shell in running container
docker-compose exec myuplink2mqtt sh

# Run command in running container
docker-compose exec myuplink2mqtt ls -la

# Run command with specific user
docker-compose exec -u root myuplink2mqtt apt-get update
```

### Debugging

```bash
# Check container health
docker-compose ps

# View container resource usage
docker stats

# Inspect running container
docker inspect $(docker-compose ps -q myuplink2mqtt)

# Check container events
docker events --filter container=myuplink2mqtt
```

## Building and Updates

### Image Management

```bash
# Build image
docker-compose build

# Build without cache (force rebuild)
docker-compose build --no-cache

# Build specific service
docker-compose build myuplink2mqtt

# List images
docker images | grep myuplink
```

### Updating Application

```bash
# Pull latest code
cd /opt/stacks/myuplink2mqtt
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose down
docker-compose up -d

# Or in one step
docker-compose up -d --build
```

## Volumes and Data

### Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect myuplink2mqtt_myuplink_tokens

# Backup volume
docker run --rm -v myuplink2mqtt_myuplink_tokens:/data \
  -v $(pwd):/backup alpine \
  tar czf /backup/myuplink_tokens_backup.tar.gz -C /data .

# Remove volume (WARNING: loses data)
docker volume rm myuplink2mqtt_myuplink_tokens
```

### Accessing Files in Volumes

```bash
# List files in volume
docker run --rm -v myuplink2mqtt_myuplink_tokens:/data \
  alpine ls -la /data

# Copy from volume
docker run --rm -v myuplink2mqtt_myuplink_tokens:/data \
  -v $(pwd):/backup alpine \
  cp /data/myUplink_API_Token.json /backup/
```

## Network Debugging

```bash
# View network details
docker network ls

# Inspect Docker network
docker network inspect myuplink2mqtt_myuplink-net

# Test connectivity from container
docker-compose exec myuplink2mqtt ping mosquitto

# Check MQTT port
docker-compose exec myuplink2mqtt nc -zv mosquitto 1883
```

## Cleaning Up

```bash
# Remove stopped containers
docker-compose rm

# Remove unused volumes
docker volume prune

# Remove unused images
docker image prune

# Remove unused networks
docker network prune

# Complete cleanup (WARNING: removes unused Docker resources)
docker system prune -a
```

## Common Issues

### Container Keeps Restarting

```bash
# Check logs
docker-compose logs myuplink2mqtt

# Check restart policy
docker inspect $(docker-compose ps -q myuplink2mqtt) \
  | grep -A 5 RestartPolicy
```

### Out of Disk Space

```bash
# Check Docker disk usage
docker system df

# Clean up old images, containers, volumes
docker system prune -a --volumes
```

### Memory Issues

```bash
# Check resource usage
docker stats myuplink2mqtt

# View memory limit
docker inspect $(docker-compose ps -q myuplink2mqtt) \
  | grep -A 5 Memory
```

### MQTT Connection Issues

```bash
# Check Mosquitto is running
docker-compose ps mosquitto

# Check Mosquitto logs
docker-compose logs mosquitto

# Test MQTT connection
docker-compose exec myuplink2mqtt \
  nc -zv mosquitto 1883
```

## Makefile Commands

```bash
make docker-build     # Build Docker image
make docker-up        # Start containers
make docker-down      # Stop containers
make docker-logs      # View logs
```

## Advanced Operations

### Using Docker Compose Override

Create `docker-compose.override.yml` for local customizations:

```yaml
version: "3.8"
services:
  myuplink2mqtt:
    volumes:
      - .:/app
      - /app/__pycache__
    environment:
      LOG_LEVEL: DEBUG
```

### Production Deployment Checklist

- [ ] Set strong MQTT username/password
- [ ] Use external secrets management (Docker Secrets, Vault)
- [ ] Configure resource limits appropriately
- [ ] Set up log rotation
- [ ] Regular backups of configuration and data
- [ ] Monitor resource usage with `docker stats`
- [ ] Implement health checks and monitoring
- [ ] Use non-root user (already done in Dockerfile)
- [ ] Read-only filesystem where possible
- [ ] Network policies/segmentation

### Using Environment Variables from File

```bash
# Create .env file
cat > .env << EOF
MYUPLINK_CLIENT_ID=your_id
MYUPLINK_CLIENT_SECRET=your_secret
EOF

# Use environment file
docker-compose --env-file .env up -d
```

## Related Documentation

- [Docker Compose Guide](./DOCKER_COMPOSE_GUIDE.md) - Full deployment documentation
- [Configuration Guide](./CONFIGURATION_GUIDE.md) - Configuration reference
- [Troubleshooting](./TROUBLESHOOTING.md) - Troubleshooting guide
