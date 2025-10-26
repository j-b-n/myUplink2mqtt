"""Demo script for Domoticz MQTT Auto-Discovery integration.

This script demonstrates all Domoticz-supported MQTT auto-discovery component types
and publishes representative example data for each sensor type. This is useful for
testing Domoticz MQTT auto-discovery integration and understanding how to structure
discovery payloads for different device types.

Domoticz supports the following component types:
- binary_sensor: Boolean state sensors (door, motion, etc.)
- button: Push button actions
- climate: Thermostat/HVAC control
- cover: Blinds, shutters, garage doors
- device_automation: Device automation triggers
- light: RGB/brightness controllable lights
- lock: Door locks
- number: Numeric input controls (min/max/step)
- select: Dropdown selection (enum values)
- sensor: Generic sensors (temperature, humidity, etc.)
- switch: On/Off controllable devices
- fan: Fan speed control
- text: Text input/display

Usage:
    python demo_domoticz_autodiscovery.py --host 127.0.0.1 \\
        --discovery-prefix domoticz --username user --password pass

Example with environment variables:
    export MQTT_BROKER_HOST=192.168.1.100
    export MQTT_BROKER_PORT=1883
    export MQTT_USERNAME=mqtt_user
    export MQTT_PASSWORD=mqtt_pass
    python demo_domoticz_autodiscovery.py --discovery-prefix domoticz

For more information, see docs/DOMOTICZ_AUTODISCOVERY.md
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from myuplink2mqtt.utils.domoticz_json_util import (
    create_domoticz_client,
)

# Configure logging
logger = logging.getLogger(__name__)

# MQTT Configuration defaults
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "127.0.0.1")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_BASE_TOPIC = os.getenv("MQTT_BASE_TOPIC", "domoticz_demo")

# Domoticz Discovery Configuration
DISCOVERY_PREFIX = os.getenv("DISCOVERY_PREFIX", "domoticz")

# Domoticz API Configuration
DOMOTICZ_HOST = os.getenv("DOMOTICZ_HOST")
DOMOTICZ_PORT = int(os.getenv("DOMOTICZ_PORT", "8080"))
DOMOTICZ_USERNAME = os.getenv("DOMOTICZ_USERNAME")
DOMOTICZ_PASSWORD = os.getenv("DOMOTICZ_PASSWORD")

# MQTT client state
MQTT_CONNECTED = False


def setup_logging(debug_mode=False, silent_mode=False):
    """Configure logging with appropriate level and format.

    Args:
        debug_mode (bool): Enable debug level logging.
        silent_mode (bool): Enable silent mode (WARNING level only).

    """
    if silent_mode:
        log_level = logging.WARNING
    elif debug_mode:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)

    logger.setLevel(log_level)


def parse_arguments():
    """Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.

    """
    parser = argparse.ArgumentParser(
        description="Domoticz MQTT Auto-Discovery Demo - Publish example sensors"
    )

    parser.add_argument(
        "--host",
        metavar="HOST",
        help="MQTT broker host (default: 127.0.0.1, env: MQTT_BROKER_HOST)",
    )

    parser.add_argument(
        "--port",
        type=int,
        metavar="PORT",
        help="MQTT broker port (default: 1883, env: MQTT_BROKER_PORT)",
    )

    parser.add_argument(
        "--username",
        metavar="USERNAME",
        help="MQTT username (env: MQTT_USERNAME)",
    )

    parser.add_argument(
        "--password",
        metavar="PASSWORD",
        help="MQTT password (env: MQTT_PASSWORD)",
    )

    parser.add_argument(
        "--discovery-prefix",
        metavar="PREFIX",
        default="domoticz",
        help="Domoticz discovery prefix (default: domoticz)",
    )

    parser.add_argument(
        "--base-topic",
        metavar="TOPIC",
        default="domoticz_demo",
        help="Base MQTT topic for demo data (default: domoticz_demo)",
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    parser.add_argument(
        "-s",
        "--silent",
        action="store_true",
        help="Silent mode - errors only",
    )

    # Domoticz API arguments
    parser.add_argument(
        "--domoticz-host",
        metavar="HOST",
        default=DOMOTICZ_HOST,
        help="Domoticz host/IP for device validation (default: None, env: DOMOTICZ_HOST)",
    )

    parser.add_argument(
        "--domoticz-port",
        type=int,
        default=DOMOTICZ_PORT,
        metavar="PORT",
        help="Domoticz port (default: 8080, env: DOMOTICZ_PORT)",
    )

    parser.add_argument(
        "--domoticz-username",
        metavar="USERNAME",
        default=DOMOTICZ_USERNAME,
        help="Domoticz HTTP Basic Auth username (env: DOMOTICZ_USERNAME)",
    )

    parser.add_argument(
        "--domoticz-password",
        metavar="PASSWORD",
        default=DOMOTICZ_PASSWORD,
        help="Domoticz HTTP Basic Auth password (env: DOMOTICZ_PASSWORD)",
    )

    return parser.parse_args()


def on_mqtt_connect(client, userdata, flags, reason_code, properties):  # pylint: disable=unused-argument
    """Handle MQTT connection event."""
    global MQTT_CONNECTED  # pylint: disable=global-statement
    if reason_code.value == 0:
        MQTT_CONNECTED = True
        auth_msg = " (authenticated)" if MQTT_USERNAME else ""
        logger.info(
            f"✓ Connected to MQTT broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}{auth_msg}"
        )
    else:
        MQTT_CONNECTED = False
        logger.error(f"✗ Failed to connect to MQTT broker (rc: {reason_code.value})")


def on_mqtt_disconnect(client, userdata, flags, reason_code, properties):  # pylint: disable=unused-argument
    """Handle MQTT disconnection event."""
    global MQTT_CONNECTED  # pylint: disable=global-statement
    MQTT_CONNECTED = False
    logger.warning(f"Disconnected from MQTT broker (rc: {reason_code.value})")


def create_mqtt_client():
    """Create and configure MQTT client.

    Returns:
        mqtt.Client: Configured MQTT client instance.

    """
    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)

    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    client.on_connect = on_mqtt_connect
    client.on_disconnect = on_mqtt_disconnect

    return client


def connect_mqtt_broker():
    """Connect to MQTT broker.

    Returns:
        mqtt.Client or None: MQTT client if successful, None otherwise.

    """
    logger.info("Connecting to MQTT broker...")
    mqtt_client = create_mqtt_client()

    try:
        mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
        mqtt_client.loop_start()

        wait_time = 0
        while not MQTT_CONNECTED and wait_time < 5:
            time.sleep(0.5)
            wait_time += 0.5

        if not MQTT_CONNECTED:
            logger.error("Failed to connect to MQTT broker")
            mqtt_client.loop_stop()
            return None

        return mqtt_client

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"MQTT connection error: {e}")
        return None


def publish_discovery_and_state(mqtt_client, component, object_id, config_payload, state_value):
    """Publish discovery config and initial state value.

    Args:
        mqtt_client: MQTT client instance.
        component (str): Component type (sensor, switch, etc.).
        object_id (str): Unique object ID.
        config_payload (dict): Discovery configuration payload.
        state_value (str): Initial state value to publish.

    """
    # Publish discovery config
    config_topic = f"{DISCOVERY_PREFIX}/{component}/{object_id}/config"
    mqtt_client.publish(config_topic, json.dumps(config_payload), qos=1, retain=True)
    logger.debug(f"Published discovery config to {config_topic}")

    # Publish initial state
    if "state_topic" in config_payload:
        mqtt_client.publish(config_payload["state_topic"], state_value, qos=1, retain=True)
        logger.debug(f"Published initial state '{state_value}' to {config_payload['state_topic']}")


def demo_sensor(mqtt_client):
    """Demo: Generic sensor - Temperature readings.

    Sensors are read-only values from devices (temperature, humidity, energy, etc.).
    """
    logger.info("📊 Publishing SENSOR (Temperature)...")

    config = {
        "device": {
            "identifiers": ["domoticz_demo_system_001"],
            "name": "Demo System 1",
            "manufacturer": "Demo Manufacturer",
            "model": "DemoDevice-1000",
        },
        "unique_id": "domoticz_demo_temp_01",
        "name": "Living Room Temperature",
        "state_topic": f"{MQTT_BASE_TOPIC}/temperature",
        "unit_of_measurement": "°C",
        "device_class": "temperature",
        "value_template": "{{ value }}",
    }

    publish_discovery_and_state(mqtt_client, "sensor", "temp_01", config, "23.5")


def demo_binary_sensor(mqtt_client):
    """Demo: Binary sensor - Motion detection (on/off).

    Binary sensors have two states (on/off, open/closed, detected/not detected).
    """
    logger.info("👁️  Publishing BINARY_SENSOR (Motion)...")

    config = {
        "device": {
            "identifiers": ["domoticz_demo_system_001"],
            "name": "Demo System 1",
        },
        "unique_id": "domoticz_demo_motion_01",
        "name": "Front Door Motion",
        "state_topic": f"{MQTT_BASE_TOPIC}/motion",
        "device_class": "motion",
        "payload_on": "true",
        "payload_off": "false",
        "value_template": "{{ value }}",
    }

    publish_discovery_and_state(mqtt_client, "binary_sensor", "motion_01", config, "false")


def demo_switch(mqtt_client):
    """Demo: Switch - On/Off controllable device.

    Switches can be turned on and off remotely.
    """
    logger.info("🔘 Publishing SWITCH (Light)...")

    config = {
        "device": {
            "identifiers": ["domoticz_demo_system_001"],
            "name": "Demo System 1",
        },
        "unique_id": "domoticz_demo_switch_01",
        "name": "Bedroom Light",
        "state_topic": f"{MQTT_BASE_TOPIC}/light/state",
        "command_topic": f"{MQTT_BASE_TOPIC}/light/command",
        "payload_on": "ON",
        "payload_off": "OFF",
        "value_template": "{{ value }}",
    }

    publish_discovery_and_state(mqtt_client, "switch", "switch_01", config, "OFF")


def demo_light(mqtt_client):
    """Demo: Light - RGB+Brightness controllable.

    Lights support color, brightness, and other advanced features.
    """
    logger.info("💡 Publishing LIGHT (RGB Lamp)...")

    config = {
        "device": {
            "identifiers": ["domoticz_demo_system_001"],
            "name": "Demo System 1",
        },
        "unique_id": "domoticz_demo_light_01",
        "name": "Desk RGB Light",
        "state_topic": f"{MQTT_BASE_TOPIC}/light_rgb/state",
        "command_topic": f"{MQTT_BASE_TOPIC}/light_rgb/command",
        "brightness": True,
        "brightness_scale": 100,
        "rgb": True,
        "supported_color_modes": ["rgb", "brightness"],
        "payload_on": "ON",
        "payload_off": "OFF",
    }

    publish_discovery_and_state(
        mqtt_client,
        "light",
        "light_01",
        config,
        json.dumps({"state": "ON", "brightness": 200, "color": {"r": 255, "g": 100, "b": 50}}),
    )


def demo_climate(mqtt_client):
    """Demo: Climate - Thermostat/HVAC control.

    Climate devices control temperature and heating/cooling modes.
    """
    logger.info("🌡️  Publishing CLIMATE (Thermostat)...")

    config = {
        "device": {
            "identifiers": ["domoticz_demo_system_001"],
            "name": "Demo System 1",
        },
        "unique_id": "domoticz_demo_climate_01",
        "name": "Main Thermostat",
        "current_temperature_topic": f"{MQTT_BASE_TOPIC}/climate/current_temp",
        "temperature_state_topic": f"{MQTT_BASE_TOPIC}/climate/setpoint",
        "temperature_command_topic": f"{MQTT_BASE_TOPIC}/climate/setpoint/set",
        "mode_state_topic": f"{MQTT_BASE_TOPIC}/climate/mode",
        "mode_command_topic": f"{MQTT_BASE_TOPIC}/climate/mode/set",
        "modes": ["heat", "cool", "auto", "off"],
        "preset_modes": ["eco", "comfort", "boost"],
        "min_temp": 5,
        "max_temp": 35,
        "temp_step": 0.5,
        "temperature_unit": "C",
    }

    publish_discovery_and_state(
        mqtt_client,
        "climate",
        "climate_01",
        config,
        "22.0",
    )
    mqtt_client.publish(f"{MQTT_BASE_TOPIC}/climate/current_temp", "21.5", qos=1, retain=True)
    mqtt_client.publish(f"{MQTT_BASE_TOPIC}/climate/mode", "heat", qos=1, retain=True)


def demo_cover(mqtt_client):
    """Demo: Cover - Blinds/shutters/garage door.

    Covers can be opened, closed, or set to a specific position.
    """
    logger.info("🪟 Publishing COVER (Blinds)...")

    config = {
        "device": {
            "identifiers": ["domoticz_demo_system_001"],
            "name": "Demo System 1",
        },
        "unique_id": "domoticz_demo_cover_01",
        "name": "Living Room Blinds",
        "command_topic": f"{MQTT_BASE_TOPIC}/blinds/command",
        "position_topic": f"{MQTT_BASE_TOPIC}/blinds/position",
        "set_position_topic": f"{MQTT_BASE_TOPIC}/blinds/set_position",
        "payload_open": "OPEN",
        "payload_close": "CLOSE",
        "payload_stop": "STOP",
        "position_open": 100,
        "position_closed": 0,
    }

    publish_discovery_and_state(mqtt_client, "cover", "cover_01", config, "50")


def demo_lock(mqtt_client):
    """Demo: Lock - Door lock control.

    Locks can be locked or unlocked remotely.
    """
    logger.info("🔒 Publishing LOCK (Door)...")

    config = {
        "device": {
            "identifiers": ["domoticz_demo_system_001"],
            "name": "Demo System 1",
        },
        "unique_id": "domoticz_demo_lock_01",
        "name": "Front Door Lock",
        "state_topic": f"{MQTT_BASE_TOPIC}/lock/state",
        "command_topic": f"{MQTT_BASE_TOPIC}/lock/command",
        "payload_lock": "LOCK",
        "payload_unlock": "UNLOCK",
        "state_locked": "locked",
        "state_unlocked": "unlocked",
    }

    publish_discovery_and_state(mqtt_client, "lock", "lock_01", config, "locked")


def demo_button(mqtt_client):
    """Demo: Button - Push button / momentary action.

    Buttons trigger an action when pressed (no state maintained).
    """
    logger.info("🔔 Publishing BUTTON (Action)...")

    config = {
        "device": {
            "identifiers": ["domoticz_demo_system_001"],
            "name": "Demo System 1",
        },
        "unique_id": "domoticz_demo_button_01",
        "name": "Alarm Silence",
        "command_topic": f"{MQTT_BASE_TOPIC}/button/alarm_silence",
        "payload_press": "press",
        "entity_category": "diagnostic",
    }

    publish_discovery_and_state(mqtt_client, "button", "button_01", config, "press")


def demo_number(mqtt_client):
    """Demo: Number - Numeric input with min/max/step.

    Numbers allow setting numeric values within a range.
    """
    logger.info("🔢 Publishing NUMBER (Fan Speed)...")

    config = {
        "device": {
            "identifiers": ["domoticz_demo_system_001"],
            "name": "Demo System 1",
        },
        "unique_id": "domoticz_demo_number_01",
        "name": "Fan Speed",
        "state_topic": f"{MQTT_BASE_TOPIC}/fan_speed/state",
        "command_topic": f"{MQTT_BASE_TOPIC}/fan_speed/set",
        "min": 0,
        "max": 100,
        "step": 10,
        "unit_of_measurement": "%",
    }

    publish_discovery_and_state(mqtt_client, "number", "number_01", config, "50")


def demo_select(mqtt_client):
    """Demo: Select - Dropdown/enum selection.

    Selects allow choosing from a list of predefined options.
    """
    logger.info("📋 Publishing SELECT (Mode)...")

    config = {
        "device": {
            "identifiers": ["domoticz_demo_system_001"],
            "name": "Demo System 1",
        },
        "unique_id": "domoticz_demo_select_01",
        "name": "HVAC Mode",
        "state_topic": f"{MQTT_BASE_TOPIC}/hvac_mode/state",
        "command_topic": f"{MQTT_BASE_TOPIC}/hvac_mode/set",
        "options": ["heat", "cool", "auto", "dry", "fan"],
        "value_template": "{{ value }}",
    }

    publish_discovery_and_state(mqtt_client, "select", "select_01", config, "auto")


def demo_fan(mqtt_client):
    """Demo: Fan - Fan speed control.

    Fans support speed control and possibly preset speeds.
    """
    logger.info("🌀 Publishing FAN (Ceiling Fan)...")

    config = {
        "device": {
            "identifiers": ["domoticz_demo_system_001"],
            "name": "Demo System 1",
        },
        "unique_id": "domoticz_demo_fan_01",
        "name": "Ceiling Fan",
        "state_topic": f"{MQTT_BASE_TOPIC}/fan/state",
        "command_topic": f"{MQTT_BASE_TOPIC}/fan/command",
        "percentage_state_topic": f"{MQTT_BASE_TOPIC}/fan/speed",
        "percentage_command_topic": f"{MQTT_BASE_TOPIC}/fan/speed/set",
        "preset_modes": ["low", "medium", "high"],
        "payload_off": "OFF",
        "payload_on": "ON",
    }

    publish_discovery_and_state(
        mqtt_client,
        "fan",
        "fan_01",
        config,
        json.dumps({"state": "ON", "percentage": 60}),
    )


def demo_text(mqtt_client):
    """Demo: Text - Text input/display.

    Text entities allow setting or reading text values.
    """
    logger.info("📝 Publishing TEXT (Notification)...")

    config = {
        "device": {
            "identifiers": ["domoticz_demo_system_001"],
            "name": "Demo System 1",
        },
        "unique_id": "domoticz_demo_text_01",
        "name": "System Status",
        "state_topic": f"{MQTT_BASE_TOPIC}/text/status",
        "command_topic": f"{MQTT_BASE_TOPIC}/text/status/set",
    }

    publish_discovery_and_state(mqtt_client, "text", "text_01", config, "System operational")


def demo_device_automation(mqtt_client):
    """Demo: Device Automation - Device trigger/automation.

    Device automations represent triggers from devices (button presses, etc.).
    """
    logger.info("⚙️  Publishing DEVICE_AUTOMATION (Motion Trigger)...")

    config = {
        "device": {
            "identifiers": ["domoticz_demo_system_001"],
            "name": "Demo System 1",
        },
        "unique_id": "domoticz_demo_automation_01",
        "automation_type": "trigger",
        "type": "motion",
        "subtype": "motion",
        "state_topic": f"{MQTT_BASE_TOPIC}/automation/motion",
        "payload": "triggered",
    }

    publish_discovery_and_state(
        mqtt_client, "device_automation", "automation_01", config, "triggered"
    )


def show_banner():
    """Display startup banner."""
    banner = [
        "",
        "=" * 80,
        "🚀 Domoticz MQTT Auto-Discovery Demo",
        "=" * 80,
        "",
        "This script publishes representative example data for all Domoticz-supported",
        "MQTT auto-discovery component types.",
        "",
        "Discovery Prefix: " + DISCOVERY_PREFIX,
        "Base Topic:       " + MQTT_BASE_TOPIC,
        "Broker:           " + MQTT_BROKER_HOST + ":" + str(MQTT_BROKER_PORT),
        "",
        "Component Types Being Demonstrated:",
        "  ✓ sensor              - Generic read-only values (temp, humidity, etc.)",
        "  ✓ binary_sensor       - Boolean state (motion, door contact, etc.)",
        "  ✓ switch              - On/Off controllable devices",
        "  ✓ light               - Brightness/color controllable lights",
        "  ✓ climate             - Thermostat/HVAC control",
        "  ✓ cover               - Blinds, shutters, garage doors",
        "  ✓ lock                - Door locks",
        "  ✓ button              - Push button actions",
        "  ✓ number              - Numeric inputs (min/max/step)",
        "  ✓ select              - Dropdown selections (enums)",
        "  ✓ fan                 - Fan speed control",
        "  ✓ text                - Text input/display",
        "  ✓ device_automation   - Device triggers",
        "",
        "=" * 80,
        "",
    ]

    for line in banner:
        logger.info(line)


def validate_domoticz_devices(discovery_prefix, expected_device_count=13):
    """Validate discovered devices in Domoticz.

    Args:
        discovery_prefix (str): MQTT discovery prefix to look for.
        expected_device_count (int): Expected number of auto-discovered devices.

    Returns:
        bool: True if validation successful, False otherwise.

    """
    if not DOMOTICZ_HOST:
        logger.info(
            "Domoticz host not configured. Skipping device validation.\n"
        )
        return True

    logger.info("")
    logger.info("=" * 80)
    logger.info("🔍 Validating discovered devices in Domoticz...")
    logger.info("=" * 80)
    logger.info("")

    # Create Domoticz client
    client = create_domoticz_client(
        DOMOTICZ_HOST,
        DOMOTICZ_PORT,
        False,
        DOMOTICZ_USERNAME,
        DOMOTICZ_PASSWORD,
    )

    if client is None:
        logger.error(
            f"❌ ERROR: Could not connect to Domoticz at {DOMOTICZ_HOST}:{DOMOTICZ_PORT}"
        )
        return False

    logger.info(f"✓ Connected to Domoticz at {DOMOTICZ_HOST}:{DOMOTICZ_PORT}")
    logger.info("")

    # Validate discovered devices
    validation = client.validate_discovery_devices(discovery_prefix)

    logger.info("📊 Device Summary:")
    logger.info(f"  Total devices in Domoticz: {validation['total_devices']}")
    logger.info(f"  MQTT-based devices: {validation['mqtt_devices']}")
    logger.info(
        f"  Auto-discovered device instances: {validation['mqtt_auto_discovery_devices']}"
    )
    logger.info(f"  Unique auto-discovery IDs: {validation['unique_auto_discovery_ids']}")
    logger.info(f"  Expected unique devices: {expected_device_count}")
    logger.info("")

    # Check if expected number of unique devices were created
    # Note: Some components (like climate) create multiple device instances
    if validation["unique_auto_discovery_ids"] != expected_device_count:
        logger.error(
            f"❌ ERROR: Expected {expected_device_count} unique auto-discovered device IDs, "
            f"but found {validation['unique_auto_discovery_ids']}"
        )
        logger.error("The following devices are missing:")
        logger.error("")
        validation_passed = False
    else:
        logger.info("✅ Correct number of auto-discovered devices found!")
        logger.info("")
        validation_passed = True

    if validation["mqtt_auto_discovery_devices"] > 0:
        logger.info("📋 Auto-discovered devices:")
        logger.info("")

        for device in validation["devices"]:
            logger.info(f"  ✓ {device['name']} (ID: {device['id']})")
            logger.info(f"    Type: {device['type']} / {device['subtype']}")
            logger.info(f"    Status: {device['status']}")
            logger.info(f"    Hardware: {device['hardware']}")
            logger.info(f"    Last Update: {device['last_update']}")
            logger.info("")
    else:
        logger.error("❌ ERROR: No auto-discovered devices found!")
        logger.error(
            "The MQTT discovery messages may not have been processed by Domoticz yet."
        )
        logger.error("Possible causes:")
        logger.error("  1. MQTT broker connectivity issue")
        logger.error("  2. Domoticz MQTT plugin not enabled")
        logger.error("  3. Discovery prefix mismatch")
        logger.error("  4. Insufficient delay between publishing and checking")
        logger.error("")
        validation_passed = False

    if validation["errors"]:
        logger.error("Validation errors:")
        for error in validation["errors"]:
            logger.error(f"  ❌ {error}")
        logger.info("")
        validation_passed = False

    if validation_passed:
        logger.info("=" * 80)
        logger.info("✅ VALIDATION SUCCESSFUL: All expected devices created!")
        logger.info("=" * 80)
        logger.info("")
    else:
        logger.info("=" * 80)
        logger.error("❌ VALIDATION FAILED: Not all devices were created as expected.")
        logger.info("=" * 80)
        logger.info("")

    return validation_passed


def apply_configuration(args):  # noqa: C901
    """Apply command-line arguments to global configuration.

    Args:
        args: Parsed command-line arguments.

    """
    global MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_USERNAME, MQTT_PASSWORD, MQTT_BASE_TOPIC, DISCOVERY_PREFIX, DOMOTICZ_HOST, DOMOTICZ_PORT, DOMOTICZ_USERNAME, DOMOTICZ_PASSWORD  # pylint: disable=global-statement

    # Override MQTT defaults with command line arguments
    if args.host:
        MQTT_BROKER_HOST = args.host
    if args.port:
        MQTT_BROKER_PORT = args.port
    if args.username:
        MQTT_USERNAME = args.username
    if args.password:
        MQTT_PASSWORD = args.password
    if args.base_topic:
        MQTT_BASE_TOPIC = args.base_topic
    if args.discovery_prefix:
        DISCOVERY_PREFIX = args.discovery_prefix

    # Apply Domoticz API arguments
    if args.domoticz_host:
        DOMOTICZ_HOST = args.domoticz_host
    if args.domoticz_port:
        DOMOTICZ_PORT = args.domoticz_port
    if args.domoticz_username:
        DOMOTICZ_USERNAME = args.domoticz_username
    if args.domoticz_password:
        DOMOTICZ_PASSWORD = args.domoticz_password


def main():
    """Main entry point."""
    args = parse_arguments()

    # Setup logging
    setup_logging(debug_mode=args.debug, silent_mode=args.silent)

    # Apply configuration
    apply_configuration(args)

    # Show banner
    show_banner()

    # Connect to MQTT
    mqtt_client = connect_mqtt_broker()
    if mqtt_client is None:
        logger.error("Failed to connect to MQTT broker")
        sys.exit(1)

    try:
        # Wait for connection to be fully established
        time.sleep(1)

        logger.info("Publishing demo sensors for all supported component types...\n")

        # Publish all demo sensors
        demo_sensor(mqtt_client)
        time.sleep(0.5)

        demo_binary_sensor(mqtt_client)
        time.sleep(0.5)

        demo_switch(mqtt_client)
        time.sleep(0.5)

        demo_light(mqtt_client)
        time.sleep(0.5)

        demo_climate(mqtt_client)
        time.sleep(0.5)

        demo_cover(mqtt_client)
        time.sleep(0.5)

        demo_lock(mqtt_client)
        time.sleep(0.5)

        demo_button(mqtt_client)
        time.sleep(0.5)

        demo_number(mqtt_client)
        time.sleep(0.5)

        demo_select(mqtt_client)
        time.sleep(0.5)

        demo_fan(mqtt_client)
        time.sleep(0.5)

        demo_text(mqtt_client)
        time.sleep(0.5)

        demo_device_automation(mqtt_client)
        time.sleep(0.5)

        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ All demo sensors published successfully!")
        logger.info("")
        logger.info("Discovery configs are retained at the MQTT broker.")
        logger.info("You should now see these devices in your Domoticz interface.")
        logger.info("")
        logger.info("To test state changes, publish updates to the topics, e.g.:")
        logger.info(
            f"  mosquitto_pub -h {MQTT_BROKER_HOST} -t {MQTT_BASE_TOPIC}/temperature -m '25.0'"
        )
        logger.info(f"  mosquitto_pub -h {MQTT_BROKER_HOST} -t {MQTT_BASE_TOPIC}/motion -m 'true'")
        logger.info("=" * 80)
        logger.info("")

        # Keep connection alive briefly for message delivery
        time.sleep(2)

        # Wait 5 seconds to allow Domoticz to process MQTT discovery messages
        if DOMOTICZ_HOST:
            logger.info("⏳ Waiting 5 seconds for Domoticz to process MQTT discovery messages...")
            for remaining in range(5, 0, -1):
                logger.info(f"   {remaining}...")
                time.sleep(1)
            logger.info("")

        # Validate devices in Domoticz if host is provided
        # Note: 12 unique devices expected (number component not supported by Domoticz)
        validation_passed = validate_domoticz_devices(DISCOVERY_PREFIX, expected_device_count=12)

        # Exit with appropriate code
        if DOMOTICZ_HOST and not validation_passed:
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"Error: {e}")
        sys.exit(1)
    finally:
        logger.info("Disconnecting from MQTT broker...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        logger.info("Done!")


if __name__ == "__main__":
    main()
