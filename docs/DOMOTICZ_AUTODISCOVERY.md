# Domoticz MQTT Auto-Discovery Guide

## Overview

This guide explains how to use MQTT auto-discovery with Domoticz. Domoticz can automatically create virtual devices in its interface when receiving properly formatted discovery messages from MQTT devices. This eliminates the need for manual device configuration.

## Domoticz Discovery Prefix

Unlike Home Assistant which uses `homeassistant` as the default discovery prefix, Domoticz uses a configurable prefix. The default is `domoticz`, but it can be changed in the Domoticz hardware settings.

### Discovery Topic Format

```
<discovery_prefix>/<component>/[<node_id>/]<object_id>/config
```

**Example Topics:**

```
domoticz/sensor/mydevice_temp_01/config
domoticz/climate/mydevice_thermostat_01/config
domoticz/switch/mydevice_lamp_01/config
```

## Supported Component Types

Domoticz supports the following MQTT auto-discovery component types:

### 1. **sensor** - Generic Read-Only Values

Use for read-only measurements: temperature, humidity, energy consumption, light level, etc.

**Example Payload:**

```json
{
  "device": {
    "identifiers": ["my_device_001"],
    "name": "Living Room",
    "manufacturer": "MyVendor",
    "model": "Sensor-X100"
  },
  "unique_id": "living_room_temp_01",
  "name": "Temperature",
  "state_topic": "home/living_room/temperature",
  "unit_of_measurement": "°C",
  "device_class": "temperature",
  "value_template": "{{ value }}"
}
```

**Supported Device Classes:**

- `temperature` - Temperature sensor (°C, °F)
- `humidity` - Humidity sensor (%)
- `pressure` - Air pressure (hPa, Pa, kPa)
- `energy` - Energy meter (kWh, Wh)
- `power` - Power meter (W, kW)
- `voltage` - Voltage (V)
- `current` - Current (A)
- `frequency` - Frequency (Hz)
- `illuminance` - Light level (lux)

**Domoticz Device Type:** General / Custom sensor

---

### 2. **binary_sensor** - Boolean State Sensors

Use for two-state devices: motion detection, door contact, smoke alarms, etc.

**Example Payload:**

```json
{
  "device": {
    "identifiers": ["my_device_001"],
    "name": "Front Door"
  },
  "unique_id": "front_door_motion_01",
  "name": "Motion Detected",
  "state_topic": "home/front_door/motion",
  "device_class": "motion",
  "payload_on": "true",
  "payload_off": "false"
}
```

**Supported Device Classes:**

- `motion` - Motion detection (Motion / No motion)
- `door` - Door contact (Open / Closed)
- `window` - Window contact (Open / Closed)
- `moisture` - Moisture/water detection (Wet / Dry)
- `smoke` - Smoke alarm (Smoke / Clear)
- `problem` - Generic problem (Problem detected / No problem)
- `occupancy` - Occupancy detection (Occupied / Unoccupied)

**Domoticz Device Type:** Switch type "On/Off"

---

### 3. **switch** - On/Off Controllable Devices

Use for devices that can be turned on or off remotely: lights, pumps, relays, etc.

**Example Payload:**

```json
{
  "device": {
    "identifiers": ["my_device_001"],
    "name": "Living Room"
  },
  "unique_id": "living_room_lamp_01",
  "name": "Main Light",
  "state_topic": "home/living_room/lamp/state",
  "command_topic": "home/living_room/lamp/command",
  "payload_on": "ON",
  "payload_off": "OFF"
}
```

**Domoticz Device Type:** Switch type "On/Off"

---

### 4. **light** - Brightness/Color Controllable

Use for advanced lighting with brightness, color, color temperature support.

**Example Payload (RGB + Brightness):**

```json
{
  "device": {
    "identifiers": ["my_device_001"],
    "name": "Living Room"
  },
  "unique_id": "living_room_rgb_light_01",
  "name": "RGB Light",
  "state_topic": "home/light/rgb/state",
  "command_topic": "home/light/rgb/command",
  "brightness": true,
  "brightness_scale": 100,
  "rgb": true,
  "supported_color_modes": ["rgb", "brightness"],
  "payload_on": "ON",
  "payload_off": "OFF"
}
```

**Configuration Options:**

- `brightness` - Supports brightness control (0-100%)
- `brightness_scale` - Maximum brightness value (usually 100 or 255)
- `rgb` - Supports RGB color control
- `color_temp` - Supports color temperature control
- `supported_color_modes` - Available color modes: `["brightness", "rgb", "color_temp"]`

**State Payload Example:**

```json
{
  "state": "ON",
  "brightness": 200,
  "color": { "r": 255, "g": 100, "b": 50 }
}
```

**Domoticz Device Type:** Color Switch

---

### 5. **climate** - Thermostat/HVAC Control

Use for thermostat and HVAC system control with temperature setpoints, modes, presets.

**Example Payload:**

```json
{
  "device": {
    "identifiers": ["my_device_001"],
    "name": "Main Floor"
  },
  "unique_id": "main_floor_thermostat_01",
  "name": "Thermostat",
  "current_temperature_topic": "home/climate/current_temp",
  "temperature_state_topic": "home/climate/setpoint",
  "temperature_command_topic": "home/climate/setpoint/set",
  "mode_state_topic": "home/climate/mode",
  "mode_command_topic": "home/climate/mode/set",
  "modes": ["heat", "cool", "auto", "off"],
  "preset_modes": ["eco", "comfort", "boost"],
  "min_temp": 5,
  "max_temp": 35,
  "temp_step": 0.5,
  "temperature_unit": "C"
}
```

**Configuration Options:**

- `modes` - Available HVAC modes: `["heat", "cool", "auto", "dry", "fan", "off"]`
- `preset_modes` - Preset operation modes: `["eco", "comfort", "boost", "away"]`
- `min_temp` / `max_temp` - Temperature range
- `temp_step` - Temperature adjustment step (0.1, 0.5, 1.0)
- `temperature_unit` - "C" or "F"

**State Topics to Publish:**

```
home/climate/current_temp        → "21.5"
home/climate/setpoint            → "22.0"
home/climate/mode                → "heat"
```

**Domoticz Device Type:** Setpoint / Thermostat

---

### 6. **cover** - Blinds, Shutters, Garage Doors

Use for window blinds, shutters, garage doors, and other covering devices.

**Example Payload:**

```json
{
  "device": {
    "identifiers": ["my_device_001"],
    "name": "Living Room"
  },
  "unique_id": "living_room_blinds_01",
  "name": "Roller Blinds",
  "command_topic": "home/blinds/command",
  "position_topic": "home/blinds/position",
  "set_position_topic": "home/blinds/set_position",
  "payload_open": "OPEN",
  "payload_close": "CLOSE",
  "payload_stop": "STOP",
  "position_open": 100,
  "position_closed": 0
}
```

**Configuration Options:**

- `payload_open` - Command to fully open
- `payload_close` - Command to fully close
- `payload_stop` - Command to stop (optional)
- `position_open` - Position value when fully open (0 or 100)
- `position_closed` - Position value when closed (0 or 100)

**Domoticz Device Type:** Blind

---

### 7. **lock** - Door Lock Control

Use for smart door locks that can be locked/unlocked remotely.

**Example Payload:**

```json
{
  "device": {
    "identifiers": ["my_device_001"],
    "name": "Front Door"
  },
  "unique_id": "front_door_lock_01",
  "name": "Front Door Lock",
  "state_topic": "home/door/lock/state",
  "command_topic": "home/door/lock/command",
  "payload_lock": "LOCK",
  "payload_unlock": "UNLOCK",
  "state_locked": "locked",
  "state_unlocked": "unlocked"
}
```

**Domoticz Device Type:** Switch type "On/Off" (locked/unlocked)

---

### 8. **button** - Push Button / Momentary Action

Use for trigger actions like alarm silence, scene activation, etc.

**Example Payload:**

```json
{
  "device": {
    "identifiers": ["my_device_001"],
    "name": "Alarm Panel"
  },
  "unique_id": "alarm_silence_button_01",
  "name": "Silence Alarm",
  "command_topic": "home/alarm/silence",
  "payload_press": "press"
}
```

**Domoticz Device Type:** Switch type "Push On"

---

### 9. **number** - Numeric Input with Min/Max/Step

Use for numeric parameters that need to be set within a range: fan speed %, brightness %, volume, etc.

**Example Payload:**

```json
{
  "device": {
    "identifiers": ["my_device_001"],
    "name": "Living Room"
  },
  "unique_id": "living_room_fan_speed_01",
  "name": "Fan Speed",
  "state_topic": "home/fan/speed/state",
  "command_topic": "home/fan/speed/set",
  "min": 0,
  "max": 100,
  "step": 5,
  "unit_of_measurement": "%"
}
```

**Domoticz Device Type:** Selector / Level

---

### 10. **select** - Dropdown Selection (Enum)

Use for choosing from a fixed list of options: mode selection, profile selection, etc.

**Example Payload:**

```json
{
  "device": {
    "identifiers": ["my_device_001"],
    "name": "Heating System"
  },
  "unique_id": "heating_mode_select_01",
  "name": "Operation Mode",
  "state_topic": "home/heating/mode/state",
  "command_topic": "home/heating/mode/set",
  "options": ["heat", "cool", "auto", "dry", "fan_only"]
}
```

**Domoticz Device Type:** Selector

---

### 11. **fan** - Fan Speed Control

Use for fans with speed control and optional preset speeds.

**Example Payload:**

```json
{
  "device": {
    "identifiers": ["my_device_001"],
    "name": "Living Room"
  },
  "unique_id": "ceiling_fan_01",
  "name": "Ceiling Fan",
  "state_topic": "home/fan/state",
  "command_topic": "home/fan/command",
  "percentage_state_topic": "home/fan/speed",
  "percentage_command_topic": "home/fan/speed/set",
  "preset_modes": ["low", "medium", "high"],
  "payload_off": "OFF",
  "payload_on": "ON"
}
```

**Domoticz Device Type:** Fan

---

### 12. **text** - Text Input/Display

Use for text-based information or commands: system status, messages, etc.

**Example Payload:**

```json
{
  "device": {
    "identifiers": ["my_device_001"],
    "name": "System"
  },
  "unique_id": "system_status_text_01",
  "name": "Status Display",
  "state_topic": "home/system/status",
  "command_topic": "home/system/status/set"
}
```

**Domoticz Device Type:** Text sensor

---

### 13. **device_automation** - Device Triggers

Use for automation triggers: button presses, motion triggers, etc.

**Example Payload:**

```json
{
  "device": {
    "identifiers": ["my_device_001"],
    "name": "Wireless Button"
  },
  "unique_id": "button_press_trigger_01",
  "automation_type": "trigger",
  "type": "button_short_press",
  "subtype": "button_1",
  "state_topic": "home/button/trigger",
  "payload": "pressed"
}
```

**Domoticz Device Type:** Event trigger

---

## Common Device Configuration Fields

All discovery payloads should include these fields:

### Device Context (Required for grouping)

```json
{
  "device": {
    "identifiers": ["my_device_001"],
    "name": "My Device",
    "manufacturer": "Device Manufacturer",
    "model": "Model-123",
    "sw_version": "1.0.0"
  }
}
```

**Fields:**

- `identifiers` (required) - Unique device identifier(s) to group related entities
- `name` - Human-readable device name
- `manufacturer` - Manufacturer name
- `model` - Device model
- `sw_version` - Software version
- `hw_version` - Hardware version

### Entity Configuration

```json
{
  "unique_id": "device_sensor_001",
  "name": "Sensor Name",
  "state_topic": "home/sensor/state",
  "unit_of_measurement": "°C",
  "device_class": "temperature",
  "entity_category": "diagnostic"
}
```

**Fields:**

- `unique_id` (required) - Unique identifier for entity deduplication
- `name` - Entity name (null to use device name)
- `state_topic` - MQTT topic for state updates
- `unit_of_measurement` - Unit (°C, %, kWh, etc.)
- `device_class` - Type hint for Domoticz (temperature, humidity, etc.)
- `entity_category` - Category: "config", "diagnostic", or none

### Availability

```json
{
  "availability_topic": "home/device/online",
  "payload_available": "online",
  "payload_not_available": "offline"
}
```

---

## Publishing Discovery Messages

### Format

Discovery messages must be published to the discovery topic with:

- **QoS: 1** (at least once)
- **Retain: true** (message persists at broker)
- **Payload:** Valid JSON

### Example Using mosquitto_pub

```bash
# Sensor
mosquitto_pub -h 127.0.0.1 \
  -t "domoticz/sensor/temp_01/config" \
  -r -q 1 \
  -m '{
    "unique_id": "temp_001",
    "name": "Room Temperature",
    "state_topic": "home/temp/state",
    "unit_of_measurement": "°C",
    "device_class": "temperature"
  }'

# Switch
mosquitto_pub -h 127.0.0.1 \
  -t "domoticz/switch/light_01/config" \
  -r -q 1 \
  -m '{
    "unique_id": "light_001",
    "name": "Main Light",
    "state_topic": "home/light/state",
    "command_topic": "home/light/command",
    "payload_on": "ON",
    "payload_off": "OFF"
  }'
```

### Example Using Python

```python
import paho.mqtt.client as mqtt
import json

client = mqtt.Client()
client.connect("127.0.0.1", 1883, 60)

# Create sensor
config = {
    "unique_id": "temp_001",
    "name": "Room Temperature",
    "state_topic": "home/temp/state",
    "unit_of_measurement": "°C",
    "device_class": "temperature"
}

# Publish discovery
topic = "domoticz/sensor/temp_01/config"
client.publish(topic, json.dumps(config), qos=1, retain=True)

# Publish state
client.publish("home/temp/state", "23.5", qos=1, retain=True)

client.loop_stop()
client.disconnect()
```

---

## State Topic Updates

After publishing the discovery configuration, regularly publish state updates to the `state_topic`:

```bash
# Temperature sensor
mosquitto_pub -h 127.0.0.1 -t "home/temp/state" -m "23.5"

# Switch state
mosquitto_pub -h 127.0.0.1 -t "home/light/state" -m "ON"

# JSON state (for complex entities)
mosquitto_pub -h 127.0.0.1 -t "home/light_rgb/state" -m \
  '{"state":"ON","brightness":200,"color":{"r":255,"g":100,"b":50}}'
```

---

## Handling Command Topics

Devices with `command_topic` receive commands from Domoticz. Your device must subscribe to the command topic and respond to commands:

```python
def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()

    if topic == "home/light/command":
        if payload == "ON":
            turn_light_on()
        elif payload == "OFF":
            turn_light_off()

client.on_message = on_message
client.subscribe("home/light/command")
```

---

## Discovery Lifecycle

### 1. **Initialization**

- Publish discovery config (retained)
- Publish initial state value

### 2. **Operation**

- Subscribe to `command_topic` and respond to changes
- Publish state updates regularly to `state_topic`

### 3. **Removal**

- Publish empty string to config topic to remove entity:
  ```bash
  mosquitto_pub -h 127.0.0.1 -t "domoticz/sensor/temp_01/config" -r -n
  ```

---

## Best Practices

1. **Use Meaningful IDs**: Make `unique_id` descriptive and persistent
2. **Retain Discovery Messages**: Always set retain flag on discovery payloads
3. **Include Device Context**: Group related entities using same `device.identifiers`
4. **Regular State Updates**: Publish state frequently (every 30-60 seconds minimum)
5. **Use Proper Units**: Specify `unit_of_measurement` for numeric sensors
6. **Choose Correct Device Classes**: Helps Domoticz auto-select icons and display formats
7. **Handle Availability**: Publish to `availability_topic` to indicate online/offline status
8. **Clean Payloads**: Remove empty or unnecessary fields to reduce MQTT traffic

---

## Testing Discovery

### 1. Monitor MQTT Traffic

```bash
# Subscribe to all discovery messages
mosquitto_sub -h 127.0.0.1 -t "domoticz/#" -v
```

### 2. Run Demo Script

```bash
python demo_domoticz_autodiscovery.py --host 127.0.0.1 --discovery-prefix domoticz
```

### 3. Check Domoticz Interface

After running the demo, you should see new devices appearing in:

- **Setup → Devices**
- Individual device pages showing discovered entities

---

## Troubleshooting

### Devices Not Appearing in Domoticz

**Check:**

- MQTT broker connectivity
- Discovery prefix matches Domoticz configuration
- Payload is valid JSON
- `unique_id` is unique
- Topics use correct format

### State Not Updating

**Check:**

- State topic matches `state_topic` in discovery config
- Publishing to correct topic
- QoS is at least 1
- State values are within expected range

### Command Not Received

**Check:**

- Device is subscribed to `command_topic`
- Payload format matches expected values
- Command topic is in discovery config

---

## References

- [Domoticz MQTT Auto-Discovery Source](https://github.com/domoticz/domoticz/blob/development/hardware/MQTTAutoDiscover.cpp)
- [Home Assistant MQTT Discovery](https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery) (similar concept, different prefix)
- [MQTT 3.1.1 Specification](http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html)

---

## Demo Script Usage

The `demo_domoticz_autodiscovery.py` script provides working examples for all component types:

```bash
# Basic usage (uses defaults)
python demo/demo_domoticz_autodiscovery.py

# With custom MQTT broker
python demo/demo_domoticz_autodiscovery.py \
  --host 192.168.1.100 \
  --port 1883

# With authentication
python demo/demo_domoticz_autodiscovery.py \
  --host 192.168.1.100 \
  --username mqtt_user \
  --password mqtt_pass

# With custom discovery prefix
python demo/demo_domoticz_autodiscovery.py \
  --discovery-prefix domoticz_custom

# Debug mode
python demo/demo_domoticz_autodiscovery.py --debug

# Silent mode
python demo/demo_domoticz_autodiscovery.py --silent
```

The script creates one example entity for each supported component type and publishes representative initial state values. Monitor Domoticz to see the devices appear automatically.
