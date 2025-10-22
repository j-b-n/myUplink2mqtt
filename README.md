# myUplink2mqtt

A Python utility to bridge myUplink API data to MQTT with Home Assistant auto-discovery support.

## Overview

This project provides:

- **`myuplink_utils.py`**: Reusable utility module for myUplink API operations with OAuth2 authentication
- **`myUplink2mqtt.py`**: Main bridge script that continuously polls myUplink devices and publishes data to MQTT
- **Demo scripts**: Located in `demo/` folder - practical examples of API operations and MQTT integration
- **Test scripts**: Located in `tests/` folder to validate functionality
- **Auto-discovery utilities**: Automatic Home Assistant MQTT entity configuration

## Features

- 🔐 OAuth2 authentication with automatic token refresh
- 🏠 Home Assistant MQTT auto-discovery
- 🔄 Continuous polling with configurable intervals
- 📊 Publishes all device parameters as individual sensors
- 🎯 Intelligent sensor type detection (temperature, humidity, energy, etc.)
- 🔧 Configuration via environment variables or config files

## Documentation

For comprehensive documentation, visit the [docs/](docs/) folder:

- **[Documentation Index](docs/index.md)** - Central hub for all documentation
- **[Demo Scripts Guide](docs/DEMO_GUIDE.md)** - Learn by example with demo scripts
- **[Quick Start Guide](docs/QUICK_START.md)** - Get running in minutes
- **[Configuration Guide](docs/CONFIGURATION_GUIDE.md)** - Detailed configuration options
- **[Service Setup](docs/SERVICE_SETUP.md)** - Systemd service installation
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Development Guide](docs/DEVELOPMENT.md)** - For developers and contributors

## Quick Start

1. **myUplink API Credentials**

   - Client ID and Client Secret from [myUplink API Portal](https://dev.myuplink.com/)
   - OAuth token (obtained through initial authentication flow)

2. **MQTT Broker**

   - Running MQTT broker (e.g., Mosquitto)
   - Optional: MQTT authentication credentials

3. **Python 3.8+** with pip

## Installation

### Quick Start

```bash
# Clone repository
git clone https://github.com/j-b-n/myUplink2mqtt.git
cd myUplink2mqtt

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: For development (includes RUFF, pytest)
pip install -r requirements-dev.txt
```

### Using Makefile (Recommended)

```bash
# Install runtime dependencies
make install

# Install with development tools (RUFF, pytest)
make install-dev
```

## Configuration

### OAuth Credentials

Store your myUplink API credentials in one of these ways:

**Option 1: Config File** (Recommended)

```bash
# Create ~/.myUplink_API_Config.json
{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret"
}
```

**Option 2: Environment Variables**

```bash
export MYUPLINK_CLIENT_ID="your_client_id"
export MYUPLINK_CLIENT_SECRET="your_client_secret"
```

### OAuth Token

The OAuth token must be stored at `~/.myUplink_API_Token.json`. This file is automatically updated when tokens are refreshed.

### MQTT Configuration

Configure MQTT connection via environment variables:

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

# Poll Interval (seconds)
export POLL_INTERVAL="300"                     # Default: 300 (5 minutes)
```

## Usage

### Basic Commands

```bash
# Run with default configuration
python myUplink2mqtt.py

# Show configuration and exit
python myUplink2mqtt.py --show-config

# Display help
python myUplink2mqtt.py --help
```

### Command Line Parameters

The script supports the following command line parameters:

#### `-s, --silent`

Run in silent mode - suppresses all output except errors and warnings.

```bash
python myUplink2mqtt.py --silent
```

#### `-d, --debug`

Run in debug mode - shows detailed output but does NOT publish to MQTT. Useful for testing and troubleshooting.

```bash
python myUplink2mqtt.py --debug
```

#### `--once`

Run a single poll cycle and exit. Useful for testing, cron jobs, or scheduled tasks.

```bash
python myUplink2mqtt.py --once
```

#### `--show-config`

Display the current configuration (myUplink, MQTT, polling settings, and runtime modes) and exit.

```bash
python myUplink2mqtt.py --show-config
```

#### `-p SECONDS, --poll=SECONDS`

Set the polling interval in seconds. Overrides the `POLL_INTERVAL` environment variable and the default of 300 seconds (5 minutes).

```bash
# Poll every 120 seconds
python myUplink2mqtt.py -p 120

# Or using long form
python myUplink2mqtt.py --poll=60
```

### Example Usage Scenarios

**Scenario 1: Normal operation (default 5-minute polling)**

```bash
python myUplink2mqtt.py
```

**Scenario 2: Debug mode to test without publishing to MQTT**

```bash
python myUplink2mqtt.py --debug --poll=10
```

Shows detailed output with faster polling (10 seconds) but doesn't actually publish to MQTT.

**Scenario 3: Silent mode for production with custom polling**

```bash
python myUplink2mqtt.py --silent --poll=600
```

Runs silently with 10-minute polling interval, only showing errors/warnings.

**Scenario 4: Check configuration before running**

```bash
python myUplink2mqtt.py --show-config
```

**Scenario 5: Run once for testing or cron job**

```bash
# Single poll cycle with normal output
python myUplink2mqtt.py --once

# Single poll cycle in silent mode (ideal for cron)
python myUplink2mqtt.py --once --silent
```

Add to crontab for periodic updates:

```bash
# Run every 5 minutes
*/5 * * * * /usr/bin/python3 /path/to/myUplink2mqtt.py --once --silent
```

Displays all settings including OAuth, MQTT broker, topics, and polling interval.

### Running the Bridge

When running without `--show-config`, the script will:

1. Verify OAuth prerequisites
2. Create authenticated session with myUplink API
3. Connect to MQTT broker (unless in debug mode)
4. Poll myUplink devices at configured intervals
5. Publish data to MQTT with Home Assistant discovery

## Logging

The script uses Python's standard `logging` module with appropriate severity levels.

### Log Levels

- **DEBUG**: Detailed diagnostic information (use `--debug` flag)
- **INFO**: Normal operational information (default)
- **WARNING**: Important messages to review
- **ERROR**: Error conditions that need attention

### Log Output Example

```
2025-10-18 19:40:48 - INFO - myUplink to MQTT Bridge with Home Assistant Auto-Discovery
2025-10-18 19:40:48 - INFO - ✓ Connected to MQTT broker at 10.0.0.2:1883
2025-10-18 19:40:48 - DEBUG - === Poll cycle 1 at 2025-10-18 19:40:48 ===
2025-10-18 19:40:48 - ERROR - OAuth prerequisites not met: Client credentials not found
```

### Log Configuration by Mode

- **Normal mode**: Shows INFO, WARNING, ERROR messages
- **Debug mode** (`--debug`): Shows DEBUG, INFO, WARNING, ERROR messages
- **Silent mode** (`--silent`): Shows only WARNING and ERROR messages

For detailed logging information, see [LOGGING_GUIDE.md](docs/LOGGING_GUIDE.md).

### Running the Bridge

When running without `--show-config`, the script will:

1. Verify OAuth prerequisites
2. Create authenticated session with myUplink API
3. Connect to MQTT broker (unless in debug mode)
4. Poll myUplink devices at configured intervals
5. Publish data to MQTT with Home Assistant discovery

Press `Ctrl+C` to stop gracefully.

### Running Tests

```bash
# Run all tests (automatically uses venv if available)
make test

# Run tests with coverage report
make test-cov

# Run specific test file directly
pytest tests/test_utilities.py -v
```

### Demo Scripts

The `demo/` folder contains practical examples showing how to use the myUplink API and MQTT integration. These are useful for learning and testing:

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

# List all MQTT topics and values
python demo/demo_mqtt_list_topics.py
```

See [DEMO_GUIDE.md](docs/DEMO_GUIDE.md) for detailed information about each demo script.

## Home Assistant Integration

Sensors are automatically discovered in Home Assistant through MQTT discovery. Each device parameter appears as a separate sensor entity.

**Entity naming pattern:**

```
sensor.{device_name}_{parameter_name}
```

**Example entities:**

- `sensor.nibe_f1155_current_outd_temp_bt1`
- `sensor.nibe_f1155_supply_heating_bt2`
- `sensor.nibe_f1155_hot_water_out_bt38`

## MQTT Topics Structure

### Discovery Topics

```
homeassistant/sensor/myuplink/{device}_{parameter}/config
```

### State Topics

```
myuplink/{device}/{parameter}/state
```

## Development

### Virtual Environment

The Makefile automatically detects and uses the virtual environment if it exists. No manual activation required!

```bash
# Create virtual environment (one-time setup)
python -m venv .venv

# Now all make commands automatically use the venv:
make lint
make format
make test
```

### Code Quality

This project uses **RUFF** for linting and formatting (fast, unified, modern):

```bash
# Check code quality (automatically uses venv if available)
make lint              # Run RUFF linter

# Format code (automatically uses venv if available)
make format            # Auto-fix formatting and auto-fixable issues

# Check formatting (without changes)
make format-check

# Run all checks (lint + tests)
make check
```

### Running Tests

```bash
# Run all tests (automatically uses venv if available)
make test

# Run tests with coverage report
make test-cov

# Run specific test file directly
pytest tests/test_utilities.py -v
```

**Note**: If you run pytest directly (not through make), you'll need to activate the venv first:

```bash
source .venv/bin/activate
pytest tests/test_utilities.py -v
```

### Project Configuration

Configuration is centralized in `pyproject.toml`:

- Project metadata (name, version, description)
- Dependencies (runtime and development)
- RUFF linter and formatter settings
- Pytest configuration
- Coverage configuration

See `DEVELOPMENT.md` for comprehensive development guide.

## Code Quality

All Python files must pass RUFF checks:

```bash
python -m ruff check .
```

### Project Structure

```
.
├── pyproject.toml                 # Project configuration (modern setup)
├── pytest.ini                     # Pytest configuration
├── Makefile                       # Common development commands
├── requirements.txt               # Runtime dependencies
├── requirements-dev.txt           # Development dependencies
│
├── myUplink2mqtt.py               # Main bridge script
├── clear_mqtt_discovery.py        # Clear MQTT discovery topics
├── verify_setup.sh                # Setup verification script
│
├── utils/
│   ├── myuplink_utils.py          # myUplink API utilities
│   └── auto_discovery_utils.py    # Home Assistant auto-discovery
│
├── tests/
│   ├── test_utilities.py          # General utilities test
│   ├── test_auto_discovery.py     # Auto-discovery test
│   ├── test_mqtt.py               # MQTT connectivity test
│   ├── conftest.py                # Pytest configuration
│   └── README.md                  # Testing documentation
│
├── demo/
│   ├── demo_ping.py               # API connectivity demo
│   ├── demo_get_names.py          # System/device names demo
│   ├── demo_get_all_points.py     # All parameters demo
│   ├── demo_get_overview.py       # Overview data demo
│   ├── demo_specific_points.py    # Specific parameters demo
│   ├── demo_mqtt.py               # MQTT connectivity demo
│   └── demo_mqtt_list_topics.py   # MQTT topics listing demo
│
├── docs/                          # Documentation
│   └── (see docs/ folder)
│
├── scripts/
│   ├── install_service.sh         # Systemd service installation
│   ├── uninstall_service.sh       # Systemd service removal
│   └── myuplink2mqtt.service      # Systemd service file
│
├── .github/
│   └── copilot-instructions.md    # AI agent development guidelines
│
├── README.md                      # This file
├── LICENSE                        # GPLv3 License
└── .gitignore
```

## Troubleshooting

### OAuth Errors

If you see "OAuth prerequisites not met":

1. Verify client credentials are configured
2. Ensure OAuth token file exists at `~/.myUplink_API_Token.json`
3. Check token hasn't expired (auto-refresh should handle this)

### MQTT Connection Issues

If MQTT connection fails:

1. Verify broker is running: `mosquitto -v`
2. Check broker host/port configuration
3. Verify authentication credentials if using auth
4. Test with: `python tests/test_mqtt.py`

### No Data Published

If no sensor data appears:

1. Check myUplink API credentials and token
2. Verify devices are accessible via myUplink API
3. Check MQTT broker logs for published messages
4. Ensure Home Assistant MQTT integration is configured

## License

See [LICENSE](LICENSE) file for details.

## Contributing

When contributing:

1. Follow existing code patterns and conventions
2. Use `make format` to format your code before committing
3. Ensure all files pass `make lint` and `make test`
4. Add tests for new functionality
5. Update documentation accordingly
6. All Python files must pass RUFF checks

For detailed development information, see `DEVELOPMENT.md`.
