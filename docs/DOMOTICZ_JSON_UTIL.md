"""Documentation for Domoticz JSON API Utility Module.

This document describes the domoticz_json_util.py module and how to use it
for interacting with Domoticz via its JSON API.
"""

# Domoticz JSON API Utility - Documentation

## Overview

The `domoticz_json_util.py` module provides a Python interface to interact with Domoticz
via its JSON HTTP API. It enables programmatic access to device lists, validation of
discovered devices, and state management.

## Module Structure

### DomoticzClient Class

Main class for interacting with Domoticz API.

#### Constructor

```python
from myuplink2mqtt.utils.domoticz_json_util import DomoticzClient

client = DomoticzClient(
    host="192.168.1.100",
    port=8080,
    use_https=False,
    username="admin",  # optional
    password="password"  # optional
)
```

**Parameters:**

- `host` (str): Domoticz host or IP address
- `port` (int): Domoticz port (default: 8080)
- `use_https` (bool): Use HTTPS instead of HTTP (default: False)
- `username` (str, optional): HTTP Basic Auth username
- `password` (str, optional): HTTP Basic Auth password

#### Methods

##### verify_connection()

Verify connection to Domoticz server.

```python
if client.verify_connection():
    print("Connected to Domoticz")
else:
    print("Connection failed")
```

**Returns:** `bool` - True if connection successful

##### get_status()

Get Domoticz server status information.

```python
status = client.get_status()
if status:
    print(f"Server: {status.get('ServerTime')}")
```

**Returns:** `dict` or `None` - Status information

**API Endpoint:** `GET /json.htm?type=command&param=getStatus`

##### get_devices()

Get list of all active devices.

```python
devices = client.get_devices()
for device in devices:
    print(f"Device: {device['Name']} (ID: {device['idx']})")
```

**Returns:** `list` or `None` - List of device dictionaries

**API Endpoint:** `GET /json.htm?type=devices&filter=all&used=1`

##### get_device(device_id)

Get details for a specific device by ID.

```python
device = client.get_device(1)  # ID 1
if device:
    print(f"Device name: {device['Name']}")
    print(f"Status: {device['Status']}")
```

**Parameters:**

- `device_id` (int): Device ID in Domoticz

**Returns:** `dict` or `None` - Device details

**API Endpoint:** `GET /json.htm?type=devices&rid={id}`

##### get_device_by_name(device_name)

Find device by its name.

```python
device = client.get_device_by_name("Living Room Temperature")
if device:
    print(f"Found device ID: {device['idx']}")
```

**Parameters:**

- `device_name` (str): Name of the device

**Returns:** `dict` or `None` - Device details if found

##### find_devices_by_mqtt_id(mqtt_id)

Find MQTT-based devices by MQTT device ID.

```python
devices = client.find_devices_by_mqtt_id("domoticz_demo")
for device in devices:
    print(f"MQTT Device: {device['Name']}")
```

**Parameters:**

- `mqtt_id` (str): MQTT device ID to search for

**Returns:** `list` - Matching devices (may be empty)

##### validate_discovery_devices(discovery_prefix)

Validate all MQTT auto-discovered devices.

```python
validation = client.validate_discovery_devices("domoticz")
print(f"Total devices: {validation['total_devices']}")
print(f"MQTT auto-discovery devices: {validation['mqtt_auto_discovery_devices']}")

for device in validation['devices']:
    print(f"  - {device['name']} (Type: {device['type']})")
```

**Parameters:**

- `discovery_prefix` (str): MQTT discovery prefix (e.g., "domoticz")

**Returns:** `dict` with structure:

```python
{
    "total_devices": int,           # Total devices in Domoticz
    "mqtt_devices": int,            # MQTT-based devices
    "mqtt_auto_discovery_devices": int,  # Auto-discovered via MQTT
    "devices": [
        {
            "id": int,              # Device ID
            "name": str,            # Device name
            "type": str,            # Device type
            "subtype": str,         # Device subtype
            "status": str,          # Current status
            "last_update": str,     # Last update timestamp
            "hardware": str         # Hardware name
        }
    ],
    "errors": [str]                 # Any validation errors
}
```

##### get_device_state(device_id)

Get current state/status of a device.

```python
state = client.get_device_state(1)
print(f"Device state: {state}")
```

**Parameters:**

- `device_id` (int): Device ID

**Returns:** `str` or `None` - Device status

##### set_device_state(device_id, state, brightness=None)

Set device state (on/off, brightness).

```python
# Turn on device
if client.set_device_state(1, "On"):
    print("Device turned on")

# Set brightness to 75%
if client.set_device_state(1, "On", brightness=75):
    print("Device brightness set to 75%")
```

**Parameters:**

- `device_id` (int): Device ID
- `state` (str): State to set (e.g., "On", "Off")
- `brightness` (int, optional): Brightness level (0-100)

**Returns:** `bool` - True if successful

**API Endpoint:** `GET /json.htm?type=command&param=switchlight&idx={id}&switchcmd={state}`

##### get_scenes()

Get list of all scenes.

```python
scenes = client.get_scenes()
for scene in scenes:
    print(f"Scene: {scene['Name']} (ID: {scene['idx']})")
```

**Returns:** `list` or `None` - List of scene dictionaries

**API Endpoint:** `GET /json.htm?type=scenes&used=1`

### Factory Function

#### create_domoticz_client()

Factory function to create and verify a client connection.

```python
from myuplink2mqtt.utils.domoticz_json_util import create_domoticz_client

client = create_domoticz_client(
    host="192.168.1.100",
    port=8080,
    use_https=False,
    username="admin",
    password="password"
)

if client:
    # Connection verified
    devices = client.get_devices()
else:
    print("Failed to connect to Domoticz")
```

**Parameters:**

- `host` (str): Domoticz host
- `port` (int): Domoticz port (default: 8080)
- `use_https` (bool): Use HTTPS (default: False)
- `username` (str, optional): Basic auth username
- `password` (str, optional): Basic auth password

**Returns:** `DomoticzClient` or `None` - Client if connection successful

## Usage in Demo Script

The `domoticz_autodiscovery.py` script uses this utility to validate
discovered devices after publishing MQTT discovery messages:

```bash
# With Domoticz validation
python demo/domoticz_autodiscovery.py \
    --host 127.0.0.1 \
    --domoticz-host 192.168.1.100 \
    --domoticz-port 8080

# With Domoticz authentication
python demo/domoticz_autodiscovery.py \
    --host 127.0.0.1 \
    --domoticz-host 192.168.1.100 \
    --domoticz-username admin \
    --domoticz-password password
```

**Environment Variables:**

- `DOMOTICZ_HOST` - Domoticz host/IP
- `DOMOTICZ_PORT` - Domoticz port (default: 8080)
- `DOMOTICZ_USERNAME` - HTTP Basic Auth username
- `DOMOTICZ_PASSWORD` - HTTP Basic Auth password

## Error Handling

All methods follow consistent error handling patterns:

- Connection errors are logged and methods return `None`
- HTTP errors (non-200 status codes) are logged
- JSON parsing errors are caught and logged
- Timeout errors (10s default) are handled gracefully

```python
device = client.get_device(999)  # Non-existent device
if device is None:
    print("Device not found or error occurred")
    # Check logs for details
```

## Domoticz Device Structure

Example device returned by `get_device()`:

```python
{
    "idx": 1,                    # Device ID
    "Name": "Living Room Temp",  # Device name
    "Type": "Temp",              # Device type
    "SubType": "Temperature",    # Device subtype
    "Status": "21.5",            # Current status/value
    "LastUpdate": "2025-10-26 15:30:45",
    "HardwareName": "MQTT Auto Discovery",
    "Description": "",
    "AddjValue": "",
    "AddjValue2": "",
    "AddjValue3": "",
    "Protected": False,
    "NextCheck": "2025-10-26 15:31:45"
}
```

## HTTP Basic Authentication

If Domoticz requires HTTP Basic Authentication:

```python
client = DomoticzClient(
    host="192.168.1.100",
    username="admin",
    password="your_password"
)

# Credentials are automatically sent with each request
status = client.get_status()
```

## Integration with MQTT Auto-Discovery

The utility is specifically designed to validate MQTT auto-discovered devices:

1. Demo script publishes MQTT discovery payloads
2. Domoticz receives and processes the payloads
3. Utility validates that devices appear in Domoticz
4. Reports on discovery success/failure

```python
validation = client.validate_discovery_devices("domoticz")

if validation["mqtt_auto_discovery_devices"] > 0:
    print(f"✅ {validation['mqtt_auto_discovery_devices']} devices discovered")
else:
    print("⚠️  No auto-discovered devices found")
    for error in validation["errors"]:
        print(f"  Error: {error}")
```

## API Endpoint Reference

| Method             | Endpoint                                   | Description     |
| ------------------ | ------------------------------------------ | --------------- |
| get_status()       | `/json.htm?type=command&param=getStatus`   | Server status   |
| get_devices()      | `/json.htm?type=devices&filter=all&used=1` | All devices     |
| get_device()       | `/json.htm?type=devices&rid={id}`          | Specific device |
| get_scenes()       | `/json.htm?type=scenes&used=1`             | All scenes      |
| set_device_state() | `/json.htm?type=command&param=switchlight` | Control device  |

For more details, see: https://wiki.domoticz.com/Domoticz_API/JSON_URL%27s

## Dependencies

The module requires:

- `requests` - HTTP client library
- Python 3.8+

## See Also

- `demo/domoticz_autodiscovery.py` - Demo script using this utility
- `docs/DOMOTICZ_AUTODISCOVERY.md` - MQTT discovery documentation
- `docs/DOMOTICZ_DEMO_README.md` - Demo script quick reference
