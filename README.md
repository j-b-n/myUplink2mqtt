# myUplink2mqtt

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: RUFF](https://img.shields.io/badge/code%20style-RUFF-4B8BBE.svg)](https://github.com/astral-sh/ruff)

A Python utility to bridge myUplink API data to MQTT with Home Assistant auto-discovery support.

## 📋 Overview

This project provides a complete bridge between the **myUplink API** (for HVAC/heat pump systems) and MQTT brokers, with automatic Home Assistant integration via MQTT discovery. It enables seamless integration of heating and cooling systems into Home Assistant and other MQTT-compatible platforms.

**Key components:**

- **`myuplink2mqtt`**: Python package with main bridge application
- **Utilities**: Reusable modules for myUplink API operations and Home Assistant auto-discovery
- **Demo scripts**: Practical examples of API operations and MQTT integration
- **Tests**: Comprehensive test suite with pytest
- **Docker support**: Ready-to-deploy containerized setup
- **Systemd service**: Production-ready Linux service installation

## ✨ Features

- 🔐 **OAuth2 Authentication**: Secure API access with automatic token refresh
- 🏠 **Home Assistant Integration**: Automatic MQTT discovery for seamless sensor configuration
- 🔄 **Continuous Polling**: Configurable polling intervals (default: 2 minutes)
- 📊 **Complete Data Export**: Publishes all device parameters as individual MQTT topics
- 🎯 **Smart Sensor Detection**: Intelligent sensor type detection (temperature, humidity, energy, power, etc.)
- 🔧 **Flexible Configuration**: Environment variables or config files
- 🐳 **Container Ready**: Docker and Docker Compose support included
- 🛠️ **Easy Deployment**: Systemd service installation scripts
- 🧪 **Well Tested**: Full test coverage with pytest
- ⚡ **High Quality**: Code quality enforced with RUFF linter

## 🛠️ Technology Stack

### Core Technologies

- **Language**: Python 3.8+
- **Package Manager**: pip with modern `pyproject.toml` configuration
- **API Client**: `myuplink` library for HVAC API access
- **MQTT Client**: `paho-mqtt` for broker communication
- **OAuth**: `requests_oauthlib` for OAuth2 authentication
- **Async Operations**: `aiohttp` for async HTTP requests

### Development Tools

- **Linting & Formatting**: RUFF (100-1000x faster than traditional tools)
- **Testing**: pytest with coverage support
- **Build System**: Modern Python packaging with `pyproject.toml`
- **Task Automation**: Makefile for common operations

### Deployment Options

- **Local**: Direct Python installation
- **Docker**: Containerized deployment with official image
- **Systemd**: Production Linux service
- **Scheduled Tasks**: Cron job compatible

## 📚 Documentation

Comprehensive documentation is available in the [docs/](docs/) folder:

- **[Demo Scripts Guide](docs/DEMO_GUIDE.md)** - Learn by example with practical demo scripts
- **[Docker Quick Start](docs/DOCKER_QUICK_START.md)** - Get running with Docker in minutes
- **[Docker Compose Guide](docs/DOCKER_COMPOSE_GUIDE.md)** - Complete stack with MQTT broker included
- **[Docker Quick Reference](docs/DOCKER_QUICK_REFERENCE.md)** - Docker commands and troubleshooting tips

For more details on available documentation, see the [docs/index.md](docs/index.md) file.

## 📋 Prerequisites

Before you begin, ensure you have:

### 1. myUplink API Credentials

- **Client ID** and **Client Secret** from [myUplink API Portal](https://dev.myuplink.com/)
- OAuth token (obtained through initial authentication flow - obtained automatically on first run)

### 2. MQTT Broker

- Running MQTT broker (e.g., Mosquitto, AWS IoT Core, etc.)
- Optional: MQTT authentication credentials

### 3. Python Environment

- **Python 3.8+** with pip
- Virtual environment recommended (e.g., venv or conda)

## 🚀 Getting Started

### Installation Methods

#### Method 1: Standard Python Installation (Recommended)

```bash
# Clone repository
git clone https://github.com/j-b-n/myUplink2mqtt.git
cd myUplink2mqtt

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package in editable mode with dependencies
pip install -e .

# Optional: Install development tools (RUFF, pytest, coverage)
pip install -e ".[dev]"
```

#### Method 2: Using Makefile (Quickest)

```bash
cd myUplink2mqtt

# Install runtime dependencies only
make install

# Or install with development tools
make install-dev
```

#### Method 3: Docker

See [Docker Quick Start](docs/DOCKER_QUICK_START.md) for containerized deployment.

#### Method 4: Direct Requirements Installation

```bash
# Install only runtime dependencies
pip install -r requirements.txt

# Install with development dependencies
pip install -r requirements.txt -r requirements-dev.txt
```

## ⚙️ Configuration

### Step 1: OAuth Credentials

Store your myUplink API credentials using one of these methods:

**Option A: Config File** (Recommended)

Create `~/.myUplink_API_Config.json`:

```json
{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret"
}
```

**Option B: Environment Variables**

```bash
export MYUPLINK_CLIENT_ID="your_client_id"
export MYUPLINK_CLIENT_SECRET="your_client_secret"
```

### Step 2: OAuth Token

The OAuth token is stored at `~/.myUplink_API_Token.json` and is automatically refreshed during API operations. The token file will be automatically created and updated when needed.

### Step 3: MQTT Configuration

Configure MQTT connection via environment variables (optional - defaults are provided):

```bash
# MQTT Broker (default: 10.0.0.2:1883)
export MQTT_BROKER_HOST="10.0.0.2"
export MQTT_BROKER_PORT="1883"

# MQTT Authentication (optional)
export MQTT_USERNAME="your_username"
export MQTT_PASSWORD="your_password"

# MQTT Topics
export MQTT_BASE_TOPIC="myuplink"              # Default: myuplink
export HA_DISCOVERY_PREFIX="homeassistant"     # Default: homeassistant

# Poll Interval (seconds, default: 120)
export POLL_INTERVAL="120"                     # Default: 120 (2 minutes)
```

## 🏗️ Project Architecture

### High-Level Overview

The bridge operates as a polling service that:

1. **Authenticates** with myUplink API using OAuth2
2. **Retrieves** system and device information periodically
3. **Transforms** device data into MQTT messages
4. **Publishes** to MQTT broker with Home Assistant discovery metadata
5. **Maintains** continuous operation with automatic token refresh

### Core Components

```
myUplink API (HVAC Systems)
        ↓
    OAuth2 Auth
        ↓
myuplink_utils.py (API Operations)
        ↓
Device Data Processing
        ↓
auto_discovery_utils.py (HA Metadata)
        ↓
MQTT Broker
        ↓
Home Assistant + MQTT Integrations
```

### Key Design Patterns

- **Modular Architecture**: Reusable utility modules (`myuplink_utils.py`, `auto_discovery_utils.py`)
- **Error Handling**: Functions return `None` on failure with descriptive error messages
- **Configuration Priority**: File-based config overridden by environment variables
- **Async Operations**: Efficient async HTTP requests for API calls
- **Retained Messages**: MQTT discovery payloads retained at broker for persistence

## 📖 Usage

### Running the Bridge

The application can be run in several ways:

**As a Python module (Recommended):**

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run the bridge
python -m myuplink2mqtt

# Or if installed as a package
myuplink2mqtt
```

**Direct script execution:**

```bash
python myuplink2mqtt/main.py
```

### Command Line Options

#### `-h, --help`

Display help message with all available options.

```bash
python -m myuplink2mqtt --help
```

#### `-s, --silent`

Run in silent mode - suppresses all output except errors and warnings.

```bash
python -m myuplink2mqtt --silent
```

#### `-d, --debug`

Run in debug mode - shows detailed output but does NOT publish to MQTT. Useful for testing and troubleshooting.

```bash
python -m myuplink2mqtt --debug
```

#### `--once`

Run a single poll cycle and exit. Useful for testing, cron jobs, or scheduled tasks.

```bash
python -m myuplink2mqtt --once
```

#### `--show-config`

Display the current configuration (myUplink API, MQTT broker, polling settings, and runtime modes) and exit.

```bash
python -m myuplink2mqtt --show-config
```

#### `-p SECONDS, --poll=SECONDS`

Set the polling interval in seconds. Overrides the `POLL_INTERVAL` environment variable.

```bash
# Poll every 60 seconds
python -m myuplink2mqtt -p 60

# Or using long form
python -m myuplink2mqtt --poll=60
```

### Usage Examples

**Run continuously with default settings (2-minute polling):**

```bash
python -m myuplink2mqtt
```

**Debug mode without publishing to MQTT:**

```bash
python -m myuplink2mqtt --debug --poll=10
```

Shows detailed output with faster polling (10 seconds) but doesn't actually publish to MQTT.

**Silent mode for production with custom polling interval:**

```bash
python -m myuplink2mqtt --silent --poll=300
```

Runs silently with 5-minute polling interval, only showing errors/warnings.

**Check configuration before running:**

```bash
python -m myuplink2mqtt --show-config
```

**Run once for testing or scheduled tasks:**

```bash
# Single poll cycle with normal output
python -m myuplink2mqtt --once

# Single poll cycle in silent mode (ideal for cron)
python -m myuplink2mqtt --once --silent
```

**Cron job example:**

Add to crontab for periodic updates:

```cron
# Run every 5 minutes
*/5 * * * * cd /home/pi/python/myUplink2mqtt && /home/pi/python/myUplink2mqtt/.venv/bin/python -m myuplink2mqtt --once --silent
```

### What the Bridge Does

When running (without `--show-config`), the bridge will:

1. Verify OAuth prerequisites (credentials and token)
2. Create authenticated session with myUplink API
3. Connect to MQTT broker (unless in `--debug` mode)
4. Poll myUplink devices at configured intervals
5. Publish data to MQTT with Home Assistant discovery messages (first cycle only, retained)
6. Continue polling until stopped (unless `--once` flag is used)

Press `Ctrl+C` to stop gracefully.

## Logging

The application uses Python's standard `logging` module with appropriate severity levels.

### Log Levels

- **DEBUG**: Detailed diagnostic information (enabled with `--debug` flag)
- **INFO**: Normal operational information (default)
- **WARNING**: Important messages that should be reviewed
- **ERROR**: Error conditions that need attention

### Log Configuration by Mode

- **Normal mode**: Shows INFO, WARNING, ERROR messages
- **Debug mode** (`--debug`): Shows DEBUG, INFO, WARNING, ERROR messages
- **Silent mode** (`--silent`): Shows only WARNING and ERROR messages

### Log Output Example

```
2025-10-22 19:40:48 - INFO - ======================================================================
2025-10-22 19:40:48 - INFO - myUplink to MQTT Bridge with Home Assistant Auto-Discovery
2025-10-22 19:40:48 - INFO - ======================================================================
2025-10-22 19:40:48 - INFO -
2025-10-22 19:40:48 - INFO - ✓ Connected to MQTT broker at 10.0.0.2:1883
2025-10-22 19:40:48 - DEBUG - === Poll cycle 1 at 2025-10-22 19:40:48 ===
2025-10-22 19:40:48 - INFO - First cycle: Sending Home Assistant discovery messages (retained at broker)
```

## 💡 Key Features

### OAuth2 & Authentication

- Automatic token refresh during API operations
- Secure credential storage in home directory
- Support for both file-based and environment variable configuration
- Graceful error handling with prerequisite checking

### Home Assistant Integration

- Automatic MQTT discovery - no manual configuration needed
- Device grouping and organization in HA
- Proper device classes (temperature, humidity, energy, power, etc.)
- Correct units of measurement (°C, %, kWh, W, rpm, etc.)
- Intelligent entity categorization (diagnostic, config)
- Manufacturer and model information included
- Discovery messages retained at broker for broker restarts

### MQTT Publishing

- Individual MQTT topics for each device parameter
- Configurable base topic prefix
- Automatic topic structure: `{base_topic}/{system_id}_{device_id}/{parameter_id}/value`
- Continuous state updates at configured polling intervals
- Retained messages for persistence

### Deployment Flexibility

- **Local**: Direct Python installation with venv
- **Docker**: Containerized deployment with volume mounts
- **Docker Compose**: Complete stack with MQTT broker included
- **Systemd**: Production-grade Linux service
- **Scheduled Tasks**: Compatible with cron jobs

### Development & Testing

- Full pytest test suite with coverage reports
- RUFF code quality enforcement
- Demo scripts for learning and testing
- Configuration validation utilities
- Comprehensive logging with multiple levels

## 📚 Demo Scripts

The `demo/` folder contains practical examples for learning and testing:

```bash
# Test API connectivity and OAuth authentication
python demo/demo_ping.py

# Retrieve and display system and device names
python demo/demo_get_names.py

# Display device overview with key sensor readings
python demo/demo_get_overview.py

# Retrieve all available device parameters
python demo/demo_get_all_points.py

# Retrieve specific device parameters
python demo/demo_specific_points.py

# Test MQTT broker connectivity
python demo/demo_mqtt.py

# List all MQTT topics and their current values
python demo/demo_mqtt_list_topics.py
```

See [DEMO_GUIDE.md](docs/DEMO_GUIDE.md) for detailed information about each demo script.

## 🧪 Testing

### Running Tests

The project uses pytest for testing. Tests can be run using the Makefile or directly:

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run all tests (using make - automatically uses venv)
make test

# Run tests with coverage report
make test-cov

# Run specific test file directly
pytest tests/test_utilities.py -v

# Run tests with verbose output
pytest -v

# Run specific test
pytest tests/test_utilities.py::test_check_oauth_prerequisites -v
```

**Note**: The Makefile automatically detects and uses the virtual environment if it exists.

### Available Test Suites

- `tests/test_utilities.py` - Tests for myUplink API utility functions
- `tests/test_auto_discovery.py` - Tests for Home Assistant auto-discovery messaging
- `tests/test_mqtt.py` - Tests for MQTT connectivity and operations

### Test Coverage

Run tests with coverage reports:

```bash
make test-cov
```

This generates a detailed coverage report showing which parts of the codebase are covered by tests.

## 🏠 Home Assistant Integration

Sensors are automatically discovered in Home Assistant through MQTT discovery. Each device parameter appears as a separate sensor entity with appropriate metadata.

**Entity naming pattern:**

```
sensor.{device_name}_{parameter_name}
```

**Example entities:**

- `sensor.nibe_f1155_current_outd_temp_bt1`
- `sensor.nibe_f1155_supply_heating_bt2`
- `sensor.nibe_f1155_hot_water_out_bt38`

### Auto-Discovery Features

- Automatic device grouping in Home Assistant
- Proper device classes (temperature, humidity, energy, power, etc.)
- Correct units of measurement (°C, %, kWh, W, etc.)
- Entity categories (diagnostic, config) for cleaner UI
- Manufacturer and model information
- Discovery messages are retained at the broker (sent only on first cycle)

## MQTT Topics Structure

### Discovery Topics

Home Assistant discovery configurations:

```
homeassistant/sensor/myuplink_{system_id}_{device_id}_{parameter_id}/config
```

### State Topics

Device parameter values:

```
myuplink/{system_id}_{device_id}/{parameter_id}/value
```

### Example

For a temperature sensor on device 12345 in system 67890, parameter 40004:

- **Discovery**: `homeassistant/sensor/myuplink_67890_12345_40004/config`
- **State**: `myuplink/67890_12345/40004/value`

## Utility Scripts

### Clear MQTT Discovery Topics

Remove all myUplink-related MQTT topics (discovery configs and values):

```bash
python -m myuplink2mqtt.clear_mqtt_discovery
```

This utility:

- Scans for all existing myUplink topics
- Clears Home Assistant discovery configurations
- Clears data value topics
- Clears availability topics
- Reports statistics on cleared topics

## Systemd Service Installation

For running the bridge as a system service on Linux:

```bash
# Install the service
sudo ./scripts/install_service.sh

# Start the service
sudo systemctl start myuplink2mqtt

# Enable auto-start on boot
sudo systemctl enable myuplink2mqtt

# Check status
sudo systemctl status myuplink2mqtt

# View logs
sudo journalctl -u myuplink2mqtt -f
```

To uninstall:

```bash
sudo ./scripts/uninstall_service.sh
```

## Docker Deployment

The project includes full Docker support with ready-to-use configurations.

### Quick Start with Docker

```bash
# Build and run (see Docker Quick Start guide)
docker build -t myuplink2mqtt .
docker run -d --name myuplink2mqtt \
  -e MYUPLINK_CLIENT_ID="your_id" \
  -e MYUPLINK_CLIENT_SECRET="your_secret" \
  -e MQTT_BROKER_HOST="10.0.0.2" \
  -v ~/.myUplink_API_Token.json:/root/.myUplink_API_Token.json \
  myuplink2mqtt
```

### Docker Compose Stack

Complete stack with MQTT broker included:

```bash
# Start the full stack
docker-compose up -d

# View logs
docker-compose logs -f myuplink2mqtt
```

For detailed Docker instructions, see:

- [Docker Quick Start](docs/DOCKER_QUICK_START.md)
- [Docker Compose Guide](docs/DOCKER_COMPOSE_GUIDE.md)
- [Docker Quick Reference](docs/DOCKER_QUICK_REFERENCE.md)

## 💻 Development

### Code Quality Standards

This project enforces strict coding standards using RUFF:

#### Quality Requirements

- **Language**: Python 3.8+ compatible
- **Linter**: RUFF with comprehensive rule set (E, W, F, B, C4, I, RUF, UP, N, BLE, A, C90, D)
- **Formatter**: RUFF for consistent code style
- **Line Length**: 100 characters maximum
- **Imports**: Sorted and organized (standard library → third-party → local)
- **Docstrings**: PEP 257 compliant with comprehensive documentation
- **Error Handling**: All functions return `None` on failure with descriptive messages

#### Code Quality Workflow

```bash
# Check code quality
make lint              # Run RUFF linter

# Format code
make format            # Auto-fix formatting and auto-fixable issues

# Check formatting without changes
make format-check

# Run all checks (lint + tests)
make check

# Manual RUFF commands
ruff check .           # Check all files
ruff check . --fix     # Fix auto-fixable issues
ruff format .          # Format code
```

### Development Environment Setup

```bash
# Create virtual environment (one-time setup)
python -m venv .venv

# Activate it
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with development tools
make install-dev

# Now all make commands automatically use the venv
make lint
make format
make test
```

### Project Configuration

All project configuration is centralized in `pyproject.toml`:

- Project metadata (name, version, description, dependencies)
- RUFF linter and formatter settings
- Pytest configuration and coverage settings
- Package build configuration

## 📁 Project Structure

```
myUplink2mqtt/
├── pyproject.toml                 # Project configuration (modern Python packaging)
├── Makefile                       # Common development commands
├── requirements.txt               # Runtime dependencies
├── requirements-dev.txt           # Development dependencies
├── LICENSE                        # GPLv3 License
├── README.md                      # This file
│
├── myuplink2mqtt/                 # Main package
│   ├── __init__.py
│   ├── __main__.py                # Entry point for python -m myuplink2mqtt
│   ├── main.py                    # Main bridge application
│   ├── clear_mqtt_discovery.py   # Utility to clear MQTT topics
│   └── utils/                     # Utility modules
│       ├── __init__.py
│       ├── myuplink_utils.py      # myUplink API operations
│       └── auto_discovery_utils.py # Home Assistant auto-discovery
│
├── demo/                          # Demo scripts for learning
│   ├── demo_ping.py               # API connectivity test
│   ├── demo_get_names.py          # Get system/device names
│   ├── demo_get_overview.py       # Device overview data
│   ├── demo_get_all_points.py     # All device parameters
│   ├── demo_specific_points.py    # Specific parameters
│   ├── demo_mqtt.py               # MQTT connectivity test
│   └── demo_mqtt_list_topics.py   # List MQTT topics
│
├── tests/                         # Test suite (pytest)
│   ├── __init__.py
│   ├── conftest.py                # Pytest configuration
│   ├── pytest.ini                 # Pytest settings
│   ├── test_utilities.py          # Utility function tests
│   ├── test_auto_discovery.py     # Auto-discovery tests
│   ├── test_mqtt.py               # MQTT connectivity tests
│   └── README.md                  # Testing documentation
│
├── scripts/                       # Installation and setup scripts
│   ├── install_service.sh         # Install systemd service
│   ├── uninstall_service.sh       # Remove systemd service
│   ├── myuplink2mqtt.service      # Systemd service file
│   ├── install_docker_stack.sh    # Docker stack installation
│   ├── verify_docker_setup.sh     # Docker setup verification
│   └── verify_setup.sh            # General setup verification
│
├── docker/                        # Docker configuration
│   ├── Dockerfile                 # Docker image definition
│   └── docker-compose.yml         # Docker Compose stack
│
├── configs/                       # Configuration examples
│   └── mosquitto/
│       └── mosquitto.conf         # Mosquitto MQTT broker config
│
├── docs/                          # Documentation (all .md files)
│   ├── DEMO_GUIDE.md              # Demo scripts guide
│   ├── DOCKER_QUICK_START.md      # Docker quick start
│   ├── DOCKER_COMPOSE_GUIDE.md    # Docker Compose guide
│   └── DOCKER_QUICK_REFERENCE.md  # Docker commands reference
│
├── htmlcov/                       # Code coverage reports (generated)
│   └── index.html                 # Coverage report
│
└── .github/                       # GitHub and CI/CD
    ├── copilot-instructions.md    # AI coding agent guidelines
    ├── instructions/              # VS Code instructions
    │   └── python.instructions.md # Python coding conventions
    └── prompts/                   # AI assistant prompts
        └── readme-blueprint-generator.prompt.md
```

### Key Directories

- **`myuplink2mqtt/`**: Main application package
- **`demo/`**: Practical examples for learning and testing
- **`tests/`**: Comprehensive test suite
- **`docs/`**: All documentation (keep all `.md` files here)
- **`scripts/`**: Installation and deployment automation

## Troubleshooting

### OAuth Errors

**Error: "OAuth prerequisites not met: Client credentials not found"**

1. Verify client credentials are configured in `~/.myUplink_API_Config.json` or environment variables
2. Check the file has correct JSON format
3. Ensure `MYUPLINK_CLIENT_ID` and `MYUPLINK_CLIENT_SECRET` are set if using env vars

**Error: Token issues**

1. Ensure OAuth token file exists at `~/.myUplink_API_Token.json`
2. Token should be obtained through initial OAuth flow
3. Auto-refresh should handle expired tokens, but you may need to re-authenticate

### MQTT Connection Issues

**Error: "Failed to connect to MQTT broker"**

1. Verify broker is running: `mosquitto -v` or `systemctl status mosquitto`
2. Check broker host/port configuration (default: 10.0.0.2:1883)
3. Verify authentication credentials if using auth
4. Test connectivity: `python demo/demo_mqtt.py`

**Error: No data appearing in Home Assistant**

1. Check MQTT integration is enabled in Home Assistant
2. Verify discovery prefix matches (default: `homeassistant`)
3. Check MQTT broker logs for published messages
4. Use `python demo/demo_mqtt_list_topics.py` to verify topics exist

### API Issues

**Error: No systems or devices found**

1. Verify myUplink API credentials are correct
2. Check that your account has devices associated
3. Test API access: `python demo/demo_ping.py`
4. Review API logs for authentication errors

### General Debugging

**Enable debug mode to see detailed output:**

```bash
python -m myuplink2mqtt --debug
```

**Check configuration:**

```bash
python -m myuplink2mqtt --show-config
```

**Test components individually:**

```bash
# Test OAuth and API
python demo/demo_ping.py

# Test MQTT
python demo/demo_mqtt.py

# Check what data is available
python demo/demo_get_overview.py
```

## 🤝 Contributing

Contributions are welcome! When contributing, please follow these guidelines:

### Code Contributions

1. Follow existing code patterns and conventions
2. Use `make format` to format your code with RUFF
3. Ensure all files pass `make lint` checks
4. Run `make test` and ensure all tests pass
5. Add tests for new functionality
6. Update documentation in `docs/` directory
7. Follow the project structure and naming conventions

### Development Workflow

```bash
# 1. Setup development environment
python -m venv .venv
source .venv/bin/activate
make install-dev

# 2. Make your changes
# ... edit files ...

# 3. Format and check code
make format
make lint

# 4. Run tests
make test

# 5. Run all checks together
make check

# 6. Commit and push
git add .
git commit -m "Descriptive commit message"
git push
```

### Code Style Requirements

- All Python files must pass RUFF linting
- Use double quotes for strings
- Maximum line length: 100 characters
- Comprehensive docstrings following PEP 257
- Clear variable and function names
- Proper error handling

### Documentation Updates

- All new `.md` files must be placed in `docs/` directory
- Keep `docs/index.md` updated as the central documentation index
- Cross-reference related documentation
- Include code examples where appropriate
- Update README.md only for major changes

### Testing Requirements

- Add tests for new functionality
- Ensure test coverage doesn't decrease
- Run `make test-cov` to verify coverage
- All tests must pass before submitting PR

## 📄 License

This project is licensed under the **GNU General Public License v3.0** (GPL-3.0-only).

See [LICENSE](LICENSE) file for full license details.

## 🆘 Support & Resources

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/j-b-n/myUplink2mqtt/issues) - Report bugs and request features
- **Documentation**: See [docs/](docs/) folder for comprehensive guides
- **Demo Scripts**: See [demo/](demo/) folder for practical examples
- **Discussion**: Check existing issues and discussions for solutions

### Useful Links

- **myUplink API**: [dev.myuplink.com](https://dev.myuplink.com/)
- **Home Assistant**: [home-assistant.io](https://www.home-assistant.io/)
- **Home Assistant MQTT**: [Home Assistant MQTT Integration](https://www.home-assistant.io/integrations/mqtt/)
- **Mosquitto MQTT**: [mosquitto.org](https://mosquitto.org/)

## 🙏 Acknowledgments

- **myUplink API** - For providing access to HVAC system data
- **Home Assistant** - For excellent MQTT discovery protocol
- **RUFF** - For fast, comprehensive code quality tools
- **pytest** - For reliable testing framework
- Open-source community - For inspiration and tools
