# myUplink2mqtt - AI Coding Agent Instructions

## Project Overview

This is a Python utility library for interacting with the myUplink API, which provides access to HVAC/heat pump system data. The project consists of a reusable `myuplink_utils.py` module and test scripts that demonstrate OAuth authentication and API operations.

## Modern Project Setup

This project uses modern Python development tools and practices:

- **`pyproject.toml`**: Centralized project configuration (replaces setup.py)
- **RUFF**: Fast Python linter and formatter (100-1000x faster than pylint)
- **Pytest**: Testing framework with coverage support
- **Makefile**: Common development commands for ease of use

### Configuration Files

- **`pyproject.toml`**: Main configuration file containing project metadata, dependencies, RUFF settings, pytest configuration, and coverage settings
- **`.ruff.toml`**: Optional RUFF-specific configuration (mirrors pyproject.toml)
- **`requirements.txt`**: Runtime dependencies
- **`requirements-dev.txt`**: Development dependencies (includes RUFF, pytest, pytest-cov)
- **`Makefile`**: Common development tasks (lint, format, test, check)

## Architecture & Design Patterns

### Core Module Structure

- **`myuplink_utils.py`**: Central utility module containing all reusable functions
- **`tests/`**: Test scripts that import and use the utility module
- **`docs/`**: Documentation directory containing all Markdown documentation files
- Configuration stored in user home directory (`~/.myUplink_API_*` files)

### Authentication Flow

```python
# Always check prerequisites first
can_proceed, error = check_oauth_prerequisites()
if not can_proceed:
    print(error)
    return

# Create authenticated session
session = create_oauth_session()
```

### Key Design Decisions

- **Token Storage**: Follows "MarshFlattsFarm pattern" - stores OAuth tokens in `~/.myUplink_API_Token.json`
- **Config Priority**: File-based config (`~/.myUplink_API_Config.json`) overridden by environment variables
- **Error Handling**: All functions return `None` on failure with descriptive error messages
- **Async Operations**: API availability testing uses `aiohttp` for async ping operations

## Critical Developer Workflows

### Running Tests

Use the Makefile for easy access to testing commands:

```bash
cd /path/to/project
source .venv/bin/activate

# Show all available commands
make help

# Run all tests
make test

# Run tests with coverage report
make test-cov

# Run specific test file
pytest tests/test_utilities.py -v
```

### Code Quality Validation with RUFF

RUFF is the primary linter and formatter. It's fast, comprehensive, and replaces pylint, black, and isort.

```bash
cd /path/to/project

# Check code quality
make lint              # Run RUFF linter on all files

# Check formatting
make format-check      # Check without making changes

# Format and fix code
make format            # Auto-fix all formatting and auto-fixable linting issues

# Run complete verification
make check             # Runs lint + tests

# Advanced RUFF commands
ruff check .                     # Check all files
ruff check . --fix               # Fix auto-fixable issues
ruff format .                    # Format code
ruff check . --select E          # Check only specific rules
```

**Critical**: All Python files must pass RUFF checks before committing.

**RUFF Configuration**:

- Configured in `pyproject.toml` under `[tool.ruff]` and `[tool.ruff.lint]`
- Target Python: 3.8+
- Line length: 100 characters
- Quote style: Double quotes
- Enabled rules: E, W, F, B, C4, I, RUF, UP, N, BLE, A, C90, D
- Per-file ignoring: Tests and demos have relaxed docstring rules

**Important**: RUFF automatically detects and fixes most issues. If it can't auto-fix something, the issue will be shown in lint output.

### OAuth Setup Requirements

1. Obtain client credentials (ID + secret)
2. Store in `~/.myUplink_API_Config.json` or environment variables
3. Run initial token acquisition (not included in this codebase)
4. Token automatically refreshes and saves during API calls

### Import Pattern for Tests

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))  # Add project root to path
from utils.myuplink_utils import create_oauth_session, get_systems
```

## Project-Specific Conventions

### Documentation Management

**Critical**: All documentation files (`.md` files) must be managed according to these rules:

- **Location**: All `.md` files belong in the `docs/` directory
- **No Root Documentation**: NEVER create new `.md` files in the project root directory
- **Existing Root Files**: Only `README.md` and `LICENSE` remain in root (do not move these)
- **Updates**: When functionality changes, update relevant documentation files in `docs/`:
  - `docs/UTILITIES_GUIDE.md` - Function documentation for `myuplink_utils.py`
  - `docs/CHANGELOG_CLI.md` - Version history and changes
  - `docs/LOGGING_GUIDE.md` - Logging configuration and usage
  - `docs/QUICK_START_SERVICE.md` - Quick start guide
  - `docs/SERVICE_SETUP_README.md` - Service installation guide
  - `docs/SYSTEMD_SERVICE_SETUP.md` - Systemd service setup details
  - `docs/index.md` - Main documentation index

### Dependencies & Imports

- `aiohttp` for async HTTP operations
- `requests_oauthlib` for OAuth2 session management
- `myuplink` library for API client functionality
- All imports at top of file, grouped by standard library → third-party → local

### Error Handling Pattern

```python
try:
    result = function_call(session)
    if result is None:
        print("Operation failed - check error messages above")
        return
except (OSError, ValueError, KeyError) as e:
    print(f"Error: {e}")
```

### Function Signatures

- OAuth session always first parameter: `def get_systems(myuplink):`
- Optional parameters use `None` defaults: `def get_device_points(myuplink, device_id, parameters=None):`
- Return `None` on failure, actual data on success

### Code Quality Standards

- **RUFF Score**: All Python files must pass RUFF checks before committing
- **RUFF Linting**:
  - Use `make lint` to check code quality
  - Use `make format` to auto-fix formatting and auto-fixable issues
  - Do NOT suppress RUFF warnings - fix the code instead
- **Docstrings**: Comprehensive with Args/Returns/Raises sections
- **Type Hints**: Not used (Python 2/3 compatibility)
- **Line Length**: 100 characters (enforced by RUFF)

## Integration Points

### External APIs

- **myUplink API Base**: `https://api.myuplink.com`
- **Endpoints Used**:
  - `/v2/systems/me` - Get user systems
  - `/v2/devices/{id}` - Device details
  - `/v2/devices/{id}/points` - Device data points

### File System Dependencies

- `~/.myUplink_API_Token.json` - OAuth token storage (auto-created)
- `~/.myUplink_API_Config.json` - Client credentials (user-created)

### Environment Variables

- `MYUPLINK_CLIENT_ID` - OAuth client ID
- `MYUPLINK_CLIENT_SECRET` - OAuth client secret

## Common Patterns & Examples

### Device Data Retrieval Flow

```python
# 1. Get systems
systems = get_systems(session)

# 2. Iterate through devices
for system in systems:
    for device in system['devices']:
        device_id = device['id']

        # 3. Get device details
        details = get_device_details(session, device_id)

        # 4. Get data points (all or specific)
        points = get_device_points(session, device_id, parameters=["40004", "40940"])
```

### Brand Extraction Logic

```python
# Simple manufacturer parsing from product names
if ' ' in product_name:
    manufacturer, model = product_name.split(' ', 1)
    brand = f"{manufacturer} {model}"
```

### HTTP Status Checking

```python
HTTP_STATUS_OK = 200
if response.status_code != HTTP_STATUS_OK:
    print(f"API Error: {response.status_code}")
    return None
```

## Home Assistant MQTT Auto-Discovery

The project implements Home Assistant MQTT auto-discovery to automatically configure sensors and entities in Home Assistant without manual YAML configuration. For official documentation, see the Home Assistant MQTT integration guide at https://www.home-assistant.io/integrations/mqtt/ (refer to the discovery section in the documentation).

### Discovery Topic Format

Discovery messages must follow this topic structure:

```
<discovery_prefix>/<component>/[<node_id>/]<object_id>/config
```

**Components**: Binary sensors, sensors, switches, lights, number inputs, etc.

**Example Topic**: `homeassistant/sensor/myuplink_system01/device_sensor_001/config`

### Discovery Payload Structure

All discovery payloads must be valid JSON with:

1. **Device Context** (`dev` - abbreviated):

   - `ids`: Device identifier (string or list)
   - `name`: Human-readable device name
   - `mf`: Manufacturer (optional)
   - `mdl`: Model (optional)
   - `sw`: Software version (optional)
   - `hw`: Hardware version (optional)
   - `sn`: Serial number (optional)

2. **Origin Information** (`o` - REQUIRED for device discovery):

   - `name`: Application name (e.g., "myUplink2mqtt")
   - `sw`: Software version
   - `url`: Support URL (optional)

3. **Entity/Component Configuration**:
   - `unique_id`: Unique identifier for deduplication (required)
   - `name`: Entity name (set to `null` to use device name)
   - `state_topic`: MQTT topic for state updates
   - `unit_of_measurement`: Unit (e.g., "°C", "%", "kWh")
   - `device_class`: Type of sensor (e.g., "temperature", "humidity", "energy")
   - `value_template`: Jinja2 template to extract value from state JSON
   - `availability_topic`: Availability status (optional)

### Typical Sensor Discovery Example

```json
{
  "dev": {
    "ids": "system_123456",
    "name": "Heat Pump System",
    "mf": "NIBE",
    "mdl": "F2120",
    "sw": "1.0"
  },
  "o": {
    "name": "myUplink2mqtt",
    "sw": "0.1.0",
    "url": "https://github.com/j-b-n/myUplink2mqtt"
  },
  "unique_id": "myuplink_system123_param40004",
  "name": "Outdoor Temperature",
  "state_topic": "myuplink/system_123456/40004/value",
  "unit_of_measurement": "°C",
  "device_class": "temperature",
  "value_template": "{{ value }}"
}
```

### Key Discovery Implementation Guidelines

1. **Retained Messages**: Always set retain flag on discovery payloads (stored at broker)
2. **Unique IDs**: Each entity must have a unique `unique_id` for entity deduplication
3. **Device Sharing**: Multiple entities can reference the same device via `identifiers`
4. **Abbreviations**: Use abbreviated keys to reduce payload size:

   - `dev` (device), `ids` (identifiers), `mf` (manufacturer)
   - `mdl` (model), `sw` (software), `hw` (hardware), `sn` (serial_number)
   - `o` (origin), `cmd_t` (command_topic), `stat_t` (state_topic)
   - `uniq_id` (unique_id), `dev_cla` (device_class), `unit_of_meas` (unit_of_measurement)

5. **Payload Size**: Use base topic (`~`) to conserve space when same base topic used multiple times

### Discovery Lifecycle

1. **Initialization**: When service starts or after HA birth message (`homeassistant/status` = "online")
2. **Publishing**: Send discovery payload to config topic with retain flag set
3. **State Updates**: Publish state updates to state_topic (also with retain flag recommended)
4. **Removal**: Publish empty string to config topic to remove entity
5. **Updates**: Resend discovery payload to update entity configuration

### State Topic Updates

After discovery, publish state updates frequently:

```
Topic: myuplink/system_123456/40004/value
Payload: 23.5
```

Or with JSON for multi-sensor devices:

```
Topic: myuplink/system_123456/state
Payload: {"temperature": 23.5, "humidity": 45.2, "energy": 1234.56}
```

Corresponding `value_template` in discovery: `{{ value_json.temperature }}`

### Common Device Classes for myUplink Parameters

Map parameter types to Home Assistant device classes:

- Temperature sensors → `temperature` (unit: °C)
- Humidity sensors → `humidity` (unit: %)
- Energy meters → `energy` (unit: kWh, MWh)
- Power meters → `power` (unit: W, kW)
- Speed sensors → `frequency` (unit: Hz, rpm)
- Status flags → Binary sensor with device_class: `motion`, `occupancy`, etc.
- Alarms → Binary sensor with device_class: `problem`, `safety`

### Best Practices

1. Always include device context for entity grouping in HA
2. Use `unique_id` matching between discovery payload and state updates
3. Subscribe to `homeassistant/status` and resend discoveries on "online" message
4. Use retained messages to survive broker restarts
5. Include origin information for troubleshooting
6. Set entity `name` to `null` to inherit device name (cleaner UI)
7. Use appropriate device_class for automatic icon/unit display in HA
8. Keep value_template simple for memory-constrained devices

### Testing Discovery

Publish manually to test discovery:

```bash
mosquitto_pub -r -h 127.0.0.1 -p 1883 \
  -t "homeassistant/sensor/myuplink_test/temp/config" \
  -m '{
    "unique_id": "test_temp_001",
    "device_class": "temperature",
    "state_topic": "homeassistant/sensor/test/state",
    "unit_of_measurement": "°C",
    "value_template": "{{ value }}",
    "device": {"identifiers": ["test_device"], "name": "Test"}
  }'
```

## Testing Strategy

- **test_ping.py**: API availability + OAuth authentication + basic system retrieval
- **test_specific_points.py**: Detailed device information + parameter-specific data points
- **test_get_names.py**: System and device name/product information retrieval
- **test_get_overview.py**: Device overview with key sensor readings and status information
- **test_mqtt.py**: MQTT broker connectivity test with optional authentication
- Tests include prerequisite checking and skip gracefully when OAuth not configured
- All tests are executable scripts with clear success/failure indicators

## Extension Guidelines

When adding new functionality to `myuplink_utils.py`:

1. Follow existing error handling patterns (return `None` on failure)
2. Add comprehensive docstrings with Args/Returns/Raises
3. Include prerequisite checking where appropriate
4. Update `docs/UTILITIES_GUIDE.md` with new function documentation
5. Add corresponding tests in `tests/` directory
6. Run `make lint` and `make format` to verify code quality
7. Ensure all Python files pass RUFF checks

When updating or creating documentation:

1. All new `.md` files must be created in the `docs/` directory
2. Never create `.md` files in the project root directory
3. Update relevant existing documentation when features change
4. Ensure cross-references between documentation files remain valid
5. Keep `docs/index.md` updated as the central navigation point
