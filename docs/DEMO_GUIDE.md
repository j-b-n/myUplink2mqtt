# Demo Scripts Guide

This guide provides detailed information about the demo scripts in the `demo/` folder. These scripts demonstrate how to use the myUplink API utilities and MQTT integration functionality.

## Overview

The demo scripts are practical examples that show:

- How to authenticate with the myUplink API using OAuth2
- How to retrieve system and device information
- How to fetch device parameters and sensor data
- How to interact with MQTT brokers
- How to work with Home Assistant auto-discovery

All demo scripts include error handling and informative output for learning purposes.

## Prerequisites

Before running any demo scripts, ensure:

1. **OAuth Credentials Configured**

   - Store your myUplink API credentials at `~/.myUplink_API_Config.json`
   - Or set environment variables: `MYUPLINK_CLIENT_ID` and `MYUPLINK_CLIENT_SECRET`

2. **OAuth Token Obtained**

   - The first successful API call will create `~/.myUplink_API_Token.json`
   - Tokens are automatically refreshed when needed

3. **Virtual Environment Activated** (Recommended)

   ```bash
   source .venv/bin/activate
   ```

4. **Dependencies Installed**
   ```bash
   pip install -r requirements.txt
   ```

## Demo Scripts

### 1. demo_ping.py

**Purpose**: Test myUplink API connectivity and OAuth authentication

**What it does**:

- Checks OAuth prerequisites (credentials are configured)
- Tests API availability using async ping
- Creates an authenticated OAuth session
- Retrieves and displays all available systems
- Shows device information and brands

**Usage**:

```bash
python demo/demo_ping.py
```

**Example output**:

```
Starting myUplink API ping test...
✓ OAuth prerequisites met
Testing API availability asynchronously...
✓ API is available
Creating authenticated OAuth session...
✓ OAuth session created
Retrieving systems...
Found 1 system(s):
  System 1: NIBE Heat Pump
    Device: NIBE F1155 (ID: abc123)
    Brand: NIBE
```

**Use cases**:

- Verify OAuth credentials are correctly configured
- Test network connectivity to myUplink API
- Confirm that devices are accessible

### 2. demo_get_names.py

**Purpose**: Retrieve and display system and device names/information

**What it does**:

- Retrieves all systems associated with your account
- For each system, fetches device details
- Extracts manufacturer/brand information
- Displays system names, device names, and product information

**Usage**:

```bash
python demo/demo_names.py
```

**Example output**:

```
System 1: "Heat Pump at Home"
  Device 1: "Basement Heat Pump"
    Product: NIBE F1155 50
    Manufacturer: NIBE
```

**Use cases**:

- Map device IDs to human-readable names
- Verify device naming in your myUplink account
- Understand product models and manufacturers
- Prepare device names for MQTT topic configuration

### 3. demo_get_overview.py

**Purpose**: Display device overview with key sensor readings and status

**What it does**:

- Retrieves systems and devices
- Fetches a predefined set of overview parameters
- Common parameters include:
  - Current outdoor temperature (BT1)
  - Supply heating temperature (BT2)
  - Return heating temperature (BT3)
  - Humidity and status information
  - System operation status

**Usage**:

```bash
python demo/demo_get_overview.py
```

**Example output**:

```
System: Heat Pump at Home
Device: Basement Heat Pump (ID: abc123)
  BT1 - Outdoor Temp:           12.5 °C
  BT2 - Supply Heating:         35.2 °C
  BT3 - Return Heating:         32.1 °C
  BT69.1 - Primary Return:      30.5 °C
  Humidity:                      65 %
```

**Use cases**:

- Quick status check of all systems
- Verify sensor readings are working
- Monitor key operating parameters
- Identify which parameters are available on your devices
- Create custom dashboards with specific parameters

### 4. demo_get_all_points.py

**Purpose**: Retrieve and display all available device parameters

**What it does**:

- Fetches ALL available parameters from devices
- Displays parameter IDs, names, and values
- Shows units and parameter types
- Useful for understanding what data is available

**Usage**:

```bash
python demo/demo_get_all_points.py
```

**Example output**:

```
System: Heat Pump at Home
Device: Basement Heat Pump (ID: abc123)
Available parameters: 127

Parameter ID 40004: Current Outdoor Temperature (BT1)
  Value: 12.5
  Unit: °C
  Category: Temperature

Parameter ID 40005: Supply Heating (BT2)
  Value: 35.2
  Unit: °C
  Category: Temperature

...
```

**Use cases**:

- Discover all available sensor parameters on devices
- Identify parameter IDs for use in other scripts
- Understand device capabilities
- Create comprehensive sensor configurations
- Document available data points

### 5. demo_specific_points.py

**Purpose**: Retrieve specific device parameters by ID

**What it does**:

- Demonstrates how to fetch only specific parameters
- Useful when you only need certain data points
- More efficient than retrieving all parameters
- Shows how to specify parameter IDs

**Usage**:

```bash
python demo/demo_specific_points.py
```

**Example output**:

```
Retrieving specific parameters from device abc123:

Parameter 40004 (Outdoor Temperature): 12.5 °C
Parameter 40005 (Supply Heating):      35.2 °C
Parameter 40013 (Humidity):            65 %
```

**Use cases**:

- Reduce API load by fetching only needed parameters
- Monitor specific sensors
- Optimize polling cycles
- Integrate into custom monitoring solutions

**How to customize**:
Edit the demo script to specify your own parameter IDs:

```python
SPECIFIC_PARAMETERS = ["40004", "40005", "40013"]  # Modify this list
```

### 6. demo_mqtt.py

**Purpose**: Test MQTT broker connectivity

**What it does**:

- Connects to MQTT broker using configured credentials
- Tests publish and subscribe functionality
- Verifies broker is accessible and responding
- Supports optional authentication

**Usage**:

```bash
python demo/demo_mqtt.py
```

**Configuration via environment variables**:

```bash
export MQTT_BROKER_HOST="10.0.0.2"
export MQTT_BROKER_PORT="1883"
export MQTT_USERNAME="your_username"      # Optional
export MQTT_PASSWORD="your_password"      # Optional
python demo/demo_mqtt.py
```

**Example output**:

```
Testing MQTT connectivity...
Broker: 10.0.0.2:1883
Connecting...
✓ Connected to MQTT broker
✓ Successfully published test message
✓ Received message on test topic
✓ All MQTT tests passed
```

**Use cases**:

- Verify MQTT broker is running and accessible
- Test authentication credentials
- Troubleshoot MQTT connection issues
- Confirm network connectivity to broker

### 7. demo_mqtt_list_topics.py

**Purpose**: List all current MQTT topics and their values

**What it does**:

- Subscribes to all MQTT topics (`#`)
- Displays each published message
- Shows topic names and message values
- Useful for monitoring MQTT traffic

**Usage**:

```bash
python demo/demo_mqtt_list_topics.py
```

**Example output**:

```
Listening for MQTT messages (press Ctrl+C to stop)...

Topic: myuplink/nibe_f1155/40004/state
Value: 12.5

Topic: myuplink/nibe_f1155/40005/state
Value: 35.2

Topic: homeassistant/sensor/myuplink/nibe_f1155_temp_bt1/config
Value: {"name": "Current Outdoor Temperature", ...}
```

**Use cases**:

- Monitor current MQTT traffic
- Verify myUplink2mqtt.py is publishing correctly
- Debug topic naming conventions
- Verify Home Assistant auto-discovery configuration
- Monitor real-time sensor data

## Running Demo Scripts in Different Modes

### Quick Start (Using Makefile)

If you prefer not to activate the venv manually:

```bash
# The Makefile automatically uses venv if available
cd /path/to/myUplink2mqtt
make demo-ping          # Run demo_ping.py
```

(Note: Makefile targets may vary - check your Makefile for available targets)

### With Verbose Output

Most demo scripts support Python's logging configuration:

```bash
# Run with debug output
export LOGLEVEL=DEBUG
python demo/demo_ping.py
```

### Sequential Testing Workflow

Recommended order for testing a new setup:

1. **Test API connectivity** - Verify OAuth is working

   ```bash
   python demo/demo_ping.py
   ```

2. **Check device names** - Understand your devices

   ```bash
   python demo/demo_get_names.py
   ```

3. **View device overview** - See current sensor values

   ```bash
   python demo/demo_get_overview.py
   ```

4. **Explore all parameters** - Find available sensors

   ```bash
   python demo/demo_get_all_points.py
   ```

5. **Test MQTT connection** - Verify broker connectivity

   ```bash
   python demo/demo_mqtt.py
   ```

6. **Monitor MQTT topics** - Watch data flow
   ```bash
   python demo/demo_mqtt_list_topics.py
   ```

## Troubleshooting Demo Scripts

### "OAuth prerequisites not met"

**Problem**: Script cannot find OAuth credentials

**Solution**:

1. Verify credentials file: `cat ~/.myUplink_API_Config.json`
2. Or check environment variables:
   ```bash
   echo $MYUPLINK_CLIENT_ID
   echo $MYUPLINK_CLIENT_SECRET
   ```
3. Create config file if needed:
   ```bash
   mkdir -p ~
   cat > ~/.myUplink_API_Config.json << EOF
   {
     "client_id": "your_client_id",
     "client_secret": "your_client_secret"
   }
   EOF
   ```

### "No systems found"

**Problem**: Account has no systems or devices

**Solution**:

1. Verify your myUplink account has active devices
2. Log in to myUplink portal to confirm device setup
3. Check that OAuth credentials have proper permissions

### "MQTT Connection failed"

**Problem**: Cannot connect to MQTT broker

**Solution**:

1. Verify broker is running: `sudo systemctl status mosquitto`
2. Check broker host/port: `nc -zv 10.0.0.2 1883`
3. Verify authentication credentials
4. Check firewall rules if on different network

### Script hangs or times out

**Problem**: Script doesn't complete

**Solution**:

1. Check network connectivity
2. Verify API/broker is responding (ping test)
3. Try with longer timeout (edit script if needed)
4. Check system logs for errors

## Customizing Demo Scripts

You can modify demo scripts to suit your needs:

### Change demo_specific_points.py to use your parameters

```python
# Edit this section with your parameter IDs
SPECIFIC_PARAMETERS = ["40004", "40005", "40013", "40040"]
```

### Change MQTT broker in demo_mqtt.py

```python
# Edit these constants
MQTT_BROKER_HOST = "your-broker.com"
MQTT_BROKER_PORT = 1883
```

### Modify polling interval in demo_get_overview.py

```python
# Edit the sleep duration
time.sleep(5)  # Change this value
```

## Integration with Main Script

Once you're comfortable with the demo scripts, you can use similar patterns in your own code:

### Import utilities

```python
from utils.myuplink_utils import create_oauth_session, get_systems
```

### Basic pattern

```python
# Check prerequisites
can_proceed, error = check_oauth_prerequisites()
if not can_proceed:
    print(error)
    exit(1)

# Create session
session = create_oauth_session()

# Use API
systems = get_systems(session)
```

## Next Steps

- Run the main **myUplink2mqtt.py** bridge script for continuous monitoring
- Configure Home Assistant MQTT integration
- Set up systemd service for auto-start: See `scripts/` folder
- Customize parameter polling in `myUplink2mqtt.py`
- Configure MQTT topic names and Home Assistant entity names

## Additional Resources

- [Main Bridge Documentation](../README.md)
- [myUplink Utilities Guide](UTILITIES_GUIDE.md)
- [MQTT Configuration Guide](../README.md#mqtt-configuration)
- [myUplink API Documentation](https://dev.myuplink.com/)
