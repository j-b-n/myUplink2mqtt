# pytest Test Suite for myUplink2mqtt

This directory contains comprehensive pytest tests for the myUplink2mqtt utilities, ensuring robust OAuth authentication, API interactions, and MQTT functionality.

## Overview

The test suite includes **86 tests** with **91% code coverage** of the utilities module, organized into three main test files:

- **`conftest.py`** - Pytest configuration and shared fixtures
- **`test_utilities.py`** - Tests for myUplink API utilities (53 tests)
- **`test_mqtt.py`** - Tests for MQTT broker/client functionality (33 tests)

## Quick Start

### Running All Tests

```bash
cd /home/pi/python/myUplink2mqtt
pytest tests/ -v
```

### Running Specific Test Files

```bash
# Run only utility tests
pytest tests/test_utilities.py -v

# Run only MQTT tests
pytest tests/test_mqtt.py -v
```

### Running with Coverage Report

```bash
pytest tests/ --cov=utils --cov-report=term-missing
```

### Running Specific Test Classes

```bash
# Test OAuth configuration loading
pytest tests/test_utilities.py::TestLoadConfig -v

# Test MQTT broker functionality
pytest tests/test_mqtt.py::TestMockMQTTBroker -v
```

### Running Specific Tests

```bash
# Test single function
pytest tests/test_utilities.py::TestGetSystems::test_get_systems_success -v

# Run tests matching pattern
pytest tests/ -k "oauth" -v
```

## Test Organization

### Configuration & Fixtures (`conftest.py`)

Provides reusable fixtures for mock data and testing infrastructure:

#### Mock Data Fixtures

- `mock_oauth_token()` - Mock OAuth2 token
- `mock_config()` - Mock client credentials
- `mock_systems_response()` - Mock systems API response
- `mock_device_details_nibe()` - Mock Nibe F1155 device
- `mock_device_details_ivt()` - Mock IVT GEO device
- `mock_device_points_response()` - Mock device sensor data

#### OAuth & Session Fixtures

- `temp_config_files()` - Temporary config/token files
- `mock_oauth_session()` - Pre-configured mock OAuth session
- `mock_oauth_session_with_errors()` - Mock session that returns errors
- `patch_config_paths()` - Patch config file paths for testing
- `patch_oauth_creation()` - Patch OAuth session creation
- `patch_env_credentials()` - Patch environment variables

#### MQTT Fixtures

- `mock_mqtt_client()` - Mock paho-mqtt client
- `mock_mqtt_broker()` - In-memory MQTT broker for testing
- `MockMQTTBroker` - Custom broker implementation

### Utility Function Tests (`test_utilities.py`)

**53 comprehensive tests** covering all utility functions:

#### Configuration Loading (5 tests)

- Loading from files
- Loading from environment variables
- Environment variable priority
- Error handling for missing config
- Invalid JSON handling

#### Token Management (7 tests)

- Token file writing and overwriting
- Token loading success and failures
- JSON parsing errors

#### OAuth Prerequisites (3 tests)

- Successful prerequisite validation
- Missing credentials detection
- Missing token file detection

#### OAuth Session Creation (3 tests)

- Successful session creation
- Error handling for missing credentials
- Error handling for missing tokens

#### Systems API (4 tests)

- Retrieving multiple systems
- Device information in systems
- HTTP error handling
- Exception handling

#### Device Details API (4 tests)

- Retrieving Nibe device details
- Retrieving IVT device details
- HTTP error handling
- Exception handling

#### Device Points API (5 tests)

- Retrieving all points
- Retrieving specific parameters
- Language specification
- Error handling
- Exception handling

#### Device Brands (3 tests)

- Multiple device brand extraction
- API error handling
- Exception handling

#### Manufacturer Extraction (5 tests)

- Nibe manufacturer extraction
- IVT manufacturer extraction
- Single-word product names
- Missing product info
- None input handling

#### Parameter Value Formatting (7 tests)

- Temperature formatting
- BT prefix handling
- Humidity formatting
- Flow rate formatting
- Installation date formatting
- Generic value formatting
- Display name override

#### Parameter Display Names (9 tests)

- Normal parameter names
- Installation year/month/day IDs
- Unmapped parameter IDs
- Device prefix removal (SAK)
- Soft hyphen cleanup
- Whitespace handling

### MQTT Tests (`test_mqtt.py`)

**33 comprehensive tests** covering MQTT functionality:

#### Mock MQTT Broker (6 tests)

- Publishing single messages
- Publishing multiple messages
- Multiple topics
- QoS and retain flags
- Topic subscription
- Message clearing

#### Mock MQTT Client (5 tests)

- Client connection
- Message publishing
- Multiple message publishing
- Client disconnection
- Connection status

#### MQTT Publishing Scenarios (5 tests)

- System discovery payloads
- Device sensor discovery
- Device state updates
- Batch discovery publishing
- Topic organization patterns

#### Error Handling (8 tests)

- Connection failures
- Publish failures
- Non-existent topics
- Large payloads
- Special characters in topics
- Special characters in payloads
- JSON payload validation
- UTF-8 character support

#### Discovery Payloads (4 tests)

- Sensor discovery format
- Binary sensor discovery format
- Device information inclusion
- Availability topic format

#### QoS and Retain Flags (5 tests)

- QoS level 0 (at most once)
- QoS level 1 (at least once)
- QoS level 2 (exactly once)
- Discovery payloads with retain
- State updates without retain

## Mock Data Examples

### Mock Systems Response

```python
{
    'systems': [
        {
            'systemId': 'system-123',
            'name': 'My Home System',
            'devices': [
                {
                    'id': 'device-001',
                    'deviceType': 'HEAT_PUMP',
                    'connectionStatus': 'ONLINE',
                    'activationDate': '2023-01-15'
                }
            ]
        }
    ]
}
```

### Mock Device Details

```python
{
    'id': 'device-001',
    'product': {
        'name': 'Nibe F1155',
        'brand': 'Nibe',
        'productSeries': 'F-series'
    },
    'connectionStatus': 'ONLINE',
    'lastStatusUpdateTime': '2025-10-19T14:30:00Z',
    'firmwareVersion': '6.125',
    'serialNumber': 'ABC123456'
}
```

### Mock Device Points

```python
{
    'points': [
        {
            'parameterId': 40004,
            'parameterName': 'Actual room temperature',
            'parameterUnit': '°C',
            'value': 21.5,
            'timestamp': '2025-10-19T14:30:00Z'
        }
    ]
}
```

## MockMQTTBroker API

The `MockMQTTBroker` class provides an in-memory MQTT broker for testing:

```python
broker = MockMQTTBroker()

# Publish a message
broker.publish('test/topic', 'payload', qos=1, retain=True)

# Get messages from specific topic
messages = broker.get_messages('test/topic')

# Get all published messages
all_messages = broker.get_all_messages()

# Subscribe to a topic
broker.subscribe('test/topic')

# Clear all messages
broker.clear()
```

## Test Coverage

Current coverage: **91% of utils/myuplink_utils.py**

```
Name                      Stmts   Miss  Cover
-------------------------------------------------------
utils/__init__.py             0      0   100%
utils/myuplink_utils.py     174     16    91%
```

Missing coverage primarily in:

- Async ping functionality (async context)
- Specific error paths
- Edge cases in legacy code

## Pytest Configuration

Configuration is defined in `pytest.ini`:

```ini
[pytest]
pythonpath = .
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

## Dependencies

The test suite requires:

```
pytest >= 8.0.0
pytest-asyncio >= 1.2.0
pytest-mock >= 3.10.0
pytest-cov >= 7.0.0
```

Install with:

```bash
pip install pytest pytest-asyncio pytest-mock pytest-cov
```

## Writing New Tests

### Using Existing Fixtures

```python
def test_my_function(mock_oauth_session, mock_systems_response):
    """Test with mocked OAuth session and systems response."""
    systems = get_systems(mock_oauth_session)
    assert len(systems) == 2
```

### Creating MQTT Test Scenarios

```python
def test_mqtt_scenario(mock_mqtt_broker):
    """Test MQTT publishing workflow."""
    mock_mqtt_broker.publish('topic', 'payload', qos=1, retain=True)
    messages = mock_mqtt_broker.get_messages('topic')
    assert len(messages) == 1
```

### Testing with Temporary Files

```python
def test_config_file(temp_config_files):
    """Test with temporary config files."""
    config_path, token_path = temp_config_files
    with patch('utils.myuplink_utils.CONFIG_FILENAME', config_path):
        client_id, secret = load_config()
        assert client_id is not None
```

## Continuous Integration

For CI/CD pipelines, use:

```bash
# Run all tests with XML output
pytest tests/ -v --junitxml=test-results.xml

# Generate coverage report
pytest tests/ --cov=utils --cov-report=html

# Run with minimal output
pytest tests/ -q
```

## Troubleshooting

### Tests Failing with Import Errors

Ensure pytest.ini exists and pythonpath is set:

```bash
cat pytest.ini  # Should show pythonpath = .
```

### Mock Fixtures Not Working

Verify patch paths are correct for your environment:

```python
from unittest.mock import patch
patch('utils.myuplink_utils.CONFIG_FILENAME', '/path/to/config')
```

### Async Test Failures

Ensure pytest-asyncio is installed and events loop is properly configured:

```bash
pip install pytest-asyncio
```

## Contributing

When adding new tests:

1. Follow existing test organization (test classes grouped by functionality)
2. Use descriptive test names following `test_<function>_<scenario>` pattern
3. Add docstrings explaining what is being tested
4. Reuse fixtures from `conftest.py` when possible
5. Maintain > 90% code coverage
6. Run full test suite before committing: `pytest tests/ -v`

## References

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-mock](https://pytest-mock.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [MQTT Protocol](https://mqtt.org/)
