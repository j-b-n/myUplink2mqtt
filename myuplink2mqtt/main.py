"""Main script to bridge myUplink API data to MQTT with Home Assistant auto-discovery.

This script continuously polls the myUplink API for device data and publishes
it to an MQTT broker with Home Assistant auto-discovery configuration.
Follows the repository patterns for OAuth authentication and error handling.
"""

import argparse
import asyncio
import logging
import os
import sys
import time

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from myuplink2mqtt.utils.auto_discovery_utils import (
    determine_entity_category,
    determine_value_type,
    publish_ha_discovery,
)

# Import utilities from the modules
from myuplink2mqtt.utils.myuplink_utils import (
    check_oauth_prerequisites,
    create_oauth_session,
    get_device_details,
    get_device_points,
    get_parameter_display_name,
    get_systems,
    save_api_data_to_file,
)

# Configure logging
logger = logging.getLogger(__name__)

# MQTT Configuration
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "10.0.0.2")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_BASE_TOPIC = os.getenv("MQTT_BASE_TOPIC", "myuplink")

# Home Assistant Discovery Configuration
HA_DISCOVERY_PREFIX = os.getenv("HA_DISCOVERY_PREFIX", "homeassistant")

# Poll interval in seconds (can be overridden by command line)
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "120"))  # Default: 2 minutes

# MQTT client state
MQTT_CONNECTED = False

# Command line options (set by parse_arguments)
SILENT_MODE = False
DEBUG_MODE = False
PUBLISH_TO_MQTT = True
RUN_ONCE = False


def setup_logging(debug_mode=False, silent_mode=False):
    """Configure logging with appropriate level and format.

    Args:
        debug_mode (bool): Enable debug level logging.
        silent_mode (bool): Enable silent mode (WARNING level only).

    """
    # Determine log level
    if silent_mode:
        log_level = logging.WARNING
    elif debug_mode:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    # Create console handler with formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # Configure module logger
    logger.setLevel(log_level)


def parse_arguments():
    """Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.

    """
    parser = argparse.ArgumentParser(
        description="Bridge myUplink API data to MQTT with Home Assistant auto-discovery"
    )

    parser.add_argument(
        "-s",
        "--silent",
        action="store_true",
        help="Silent mode - no output except errors and warnings",
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Debug mode - show detailed output but do not publish to MQTT",
    )

    parser.add_argument("--once", action="store_true", help="Run once and exit (single poll cycle)")

    parser.add_argument("--show-config", action="store_true", help="Display configuration and exit")

    parser.add_argument(
        "--save",
        nargs="?",
        const="/tmp/myuplink.json",
        metavar="FILE",
        help="Save all API data to JSON file and exit (default: /tmp/myuplink.json)",
    )

    parser.add_argument(
        "-p",
        "--poll",
        type=int,
        metavar="SECONDS",
        help="Set poll interval in seconds (default: 300)",
    )

    return parser.parse_args()


def on_mqtt_connect(client, userdata, flags, reason_code, properties):  # pylint: disable=unused-argument
    """Handle MQTT client connection event."""
    global MQTT_CONNECTED  # pylint: disable=global-statement
    if reason_code.value == 0:
        MQTT_CONNECTED = True
        auth_msg = " (authenticated)" if MQTT_USERNAME else ""
        broker_info = f"{MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}"
        logger.info(f"Connected to MQTT broker at {broker_info}{auth_msg}")
    else:
        MQTT_CONNECTED = False
        broker_info = f"{MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}"
        logger.error(f"Failed MQTT connect to {broker_info}, rc: {reason_code.value}")


def on_mqtt_disconnect(client, userdata, flags, reason_code, properties):  # pylint: disable=unused-argument
    """Handle MQTT client disconnection event."""
    global MQTT_CONNECTED  # pylint: disable=global-statement
    MQTT_CONNECTED = False
    logger.error(f"Disconnected from MQTT broker (rc: {reason_code.value})")


def create_mqtt_client():
    """Create and configure MQTT client.

    Returns:
        mqtt.Client: Configured MQTT client instance.

    """
    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)

    # Set username and password if provided
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    client.on_connect = on_mqtt_connect
    client.on_disconnect = on_mqtt_disconnect

    return client


def sanitize_name(name):
    """Sanitize a name for use in MQTT topics and Home Assistant entity IDs.

    Args:
        name (str): The name to sanitize.

    Returns:
        str: Sanitized name with only lowercase alphanumeric and underscores.

    """
    # Remove special characters and replace spaces with underscores
    sanitized = "".join(c if c.isalnum() or c in (" ", "_", "-") else "" for c in name)
    sanitized = sanitized.replace(" ", "_").replace("-", "_").lower()
    # Remove consecutive underscores
    while "__" in sanitized:
        sanitized = sanitized.replace("__", "_")
    return sanitized.strip("_")


def publish_sensor_state(mqtt_client, system_id, parameter_id, value, enum_values=None):
    """Publish sensor state to MQTT.

    For enum parameters, publishes the text representation of the value.
    For other parameters, publishes the numeric/string value as-is.

    Args:
        mqtt_client: MQTT client instance.
        system_id (str): System ID.
        parameter_id (str): Parameter ID.
        value: Parameter value (numeric or string).
        enum_values (list, optional): List of enum value dicts with 'value' and 'text' keys.

    """
    # State topic
    state_topic = f"{MQTT_BASE_TOPIC}/{system_id}/{parameter_id}/value"

    # If this is an enum parameter, convert numeric value to text
    state_value = value
    if enum_values and len(enum_values) > 0:
        # Convert value to string for comparison
        value_str = str(int(value)) if isinstance(value, float) else str(value)
        # Find matching enum text
        for enum_item in enum_values:
            if enum_item.get("value") == value_str:
                state_value = enum_item.get("text", value)
                break

    # Publish state
    mqtt_client.publish(state_topic, str(state_value), qos=1, retain=True)


def publish_availability(mqtt_client, system_id, available=True):
    """Publish availability status to MQTT.

    Args:
        mqtt_client: MQTT client instance.
        system_id (str): System ID.
        available (bool): Whether the system is available.

    """
    availability_topic = f"{MQTT_BASE_TOPIC}/{system_id}/available"
    payload = "online" if available else "offline"
    mqtt_client.publish(availability_topic, payload, qos=1, retain=True)


def process_device(myuplink, mqtt_client, system_id, device_id, send_discovery=False):
    """Process a single device: retrieve data and publish to MQTT.

    Args:
        myuplink: OAuth2Session for myUplink API.
        mqtt_client: MQTT client instance or None if not publishing.
        system_id (str): System ID.
        device_id (str): Device ID.
        send_discovery (bool): Whether to send HA discovery messages (first cycle only).

    Returns:
        bool: True if successful, False otherwise.

    """
    # Get device details
    device_data = get_device_details(myuplink, device_id)
    if device_data is None:
        logger.error(f"Could not retrieve device details for {device_id}")
        return False

    device_name = device_data["product"]["name"]
    product_name = device_data["product"]["name"]
    manufacturer = product_name.split(" ", 1)[0] if " " in product_name else "Unknown"
    model = product_name.split(" ", 1)[1] if " " in product_name else product_name

    device_info = {
        "id": device_id,
        "device_name": device_name,
        "manufacturer": manufacturer,
        "model": model,
        "serial": device_data.get("serialNumber", ""),
    }
    logger.debug(f"Processing device: {device_name} ({device_id})")

    # Get all data points
    points_data = get_device_points(myuplink, device_id)
    if points_data is None:
        logger.error(f"Could not retrieve data points for {device_id}")
        return False
    logger.debug(f"Retrieved {len(points_data)} data points")

    # Publish availability as online
    if PUBLISH_TO_MQTT and mqtt_client is not None:
        publish_availability(mqtt_client, system_id, available=True)

    # Process each data point
    points_published = 0
    discovery_sent = 0
    for point in points_data:
        parameter_info = {
            "id": point["parameterId"],
            "name": get_parameter_display_name(point),
            "value": point["value"],
            "unit": point.get("parameterUnit", ""),
            "value_type": determine_value_type(point["value"]),
            "category": determine_entity_category(
                point["parameterId"], get_parameter_display_name(point)
            ),
            "enum_values": point.get("enumValues", []),
        }

        # Publish to MQTT if not in debug mode
        if PUBLISH_TO_MQTT and mqtt_client is not None:
            # Publish Home Assistant discovery configuration (only on first cycle)
            if send_discovery:
                publish_ha_discovery(mqtt_client, device_info, parameter_info, system_id)
                discovery_sent += 1

            # Publish current state (every cycle)
            publish_sensor_state(
                mqtt_client,
                system_id,
                parameter_info["id"],
                parameter_info["value"],
                parameter_info.get("enum_values", []),
            )

        points_published += 1

    if PUBLISH_TO_MQTT:
        if send_discovery:
            logger.info(f"Sent {discovery_sent} HA discovery configs (retained at broker)")
        logger.debug(f"Published {points_published} state updates to MQTT")
    else:
        logger.debug(f"Would publish {points_published} data points (debug mode)")
    return True


def show_configuration():
    """Display current configuration and exit."""
    config_lines = [
        "",
        "=" * 70,
        "myUplink2mqtt Configuration",
        "=" * 70,
        "",
        "📡 myUplink API Configuration:",
        "  OAuth Config File: ~/.myUplink_API_Config.json",
        "  OAuth Token File:  ~/.myUplink_API_Token.json",
        "",
        "🏠 MQTT Broker Configuration:",
        f"  Broker Host:       {MQTT_BROKER_HOST}",
        f"  Broker Port:       {MQTT_BROKER_PORT}",
        f"  Authentication:    {'Yes' if MQTT_USERNAME else 'No'}",
    ]

    if MQTT_USERNAME:
        config_lines.append(f"  Username:          {MQTT_USERNAME}")

    config_lines.extend(
        [
            "",
            "📝 MQTT Topics Configuration:",
            f"  Base Topic:        {MQTT_BASE_TOPIC}",
            f"  HA Discovery Pfx:  {HA_DISCOVERY_PREFIX}",
            "",
            "⏱️  Polling Configuration:",
            f"  Poll Interval:     {POLL_INTERVAL} seconds",
            "",
            "⚙️  Runtime Modes:",
            f"  Silent Mode:       {'Enabled' if SILENT_MODE else 'Disabled'}",
            f"  Debug Mode:        {'Enabled' if DEBUG_MODE else 'Disabled'}",
            f"  Publish to MQTT:   {'Yes' if PUBLISH_TO_MQTT else 'No (debug mode)'}",
            "",
            "=" * 70,
            "",
        ]
    )

    # Log configuration lines
    for line in config_lines:
        logger.info(line)


def setup_oauth_session():
    """Set up OAuth session with prerequisites check.

    Returns:
        OAuth2Session or None: OAuth session if successful, None otherwise.

    """
    # Check OAuth prerequisites
    logger.info("Checking OAuth prerequisites...")
    can_proceed, error_msg = check_oauth_prerequisites()

    if not can_proceed:
        logger.error("OAuth prerequisites not met:")
        logger.error(error_msg)
        return None

    logger.info("OAuth prerequisites met")

    # Create OAuth session
    logger.info("Creating OAuth session...")
    try:
        myuplink = create_oauth_session()
        logger.info("OAuth session created")
        return myuplink
    except (OSError, ValueError, KeyError) as e:
        logger.error(f"Failed to create OAuth session: {e}")
        return None


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

        # Wait for connection
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


def process_poll_cycle(myuplink, mqtt_client, loop_count):
    """Process a single poll cycle.

    Args:
        myuplink: OAuth2Session for myUplink API.
        mqtt_client: MQTT client instance.
        loop_count (int): Current loop iteration number.

    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    logger.debug(f"=== Poll cycle {loop_count} at {timestamp} ===")

    # Send discovery messages only on first cycle (they are retained at broker)
    send_discovery = loop_count == 1

    if send_discovery and PUBLISH_TO_MQTT:
        logger.info("First cycle: Sending Home Assistant discovery messages (retained at broker)")

    # Get systems
    systems = get_systems(myuplink)
    if systems is None:
        logger.error("Failed to retrieve systems")
        return
    logger.debug(f"Retrieved {len(systems)} system(s)")

    # Process each system
    for system in systems:
        system_id = system["systemId"]
        system_name = system["name"]
        logger.debug(f"System: {system_name} (ID: {system_id})")
        logger.debug(f"Devices: {len(system['devices'])}")

        # Process each device
        for device in system["devices"]:
            device_id = device["id"]
            process_device(myuplink, mqtt_client, system_id, device_id, send_discovery)


def log_startup_info():
    """Log startup information based on configuration."""
    if RUN_ONCE:
        logger.info("Running in single-cycle mode (--once)")
    else:
        logger.info(f"Starting main loop (polling every {POLL_INTERVAL} seconds)...")

    if PUBLISH_TO_MQTT:
        logger.info(f"Publishing to MQTT topic base: {MQTT_BASE_TOPIC}")
        logger.info(f"Home Assistant discovery prefix: {HA_DISCOVERY_PREFIX}")
    else:
        logger.warning("Debug mode: not publishing to MQTT")

    if not RUN_ONCE:
        logger.debug("Press Ctrl+C to stop\n")


async def main_loop():
    """Poll myUplink API and publish data to MQTT."""
    # Set up OAuth session
    myuplink = setup_oauth_session()
    if myuplink is None:
        return False

    # Connect to MQTT broker (skip if debug mode without publishing)
    mqtt_client = None
    if PUBLISH_TO_MQTT:
        mqtt_client = connect_mqtt_broker()
        if mqtt_client is None:
            return False

    # Log startup information
    log_startup_info()

    loop_count = 0
    try:
        while True:
            loop_count += 1
            process_poll_cycle(myuplink, mqtt_client, loop_count)
            logger.info(f"Poll cycle {loop_count} complete")

            # Exit after first cycle if RUN_ONCE mode
            if RUN_ONCE:
                logger.info("Single cycle complete, exiting")
                break

            logger.debug(f"Sleeping for {POLL_INTERVAL} seconds...")
            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Shutdown requested by user (Ctrl+C)")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"Unexpected error in main loop: {e}")
    finally:
        if PUBLISH_TO_MQTT:
            logger.info("Disconnecting from MQTT broker...")
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
            logger.info("Disconnected")

    return True


def main():
    """Entry point for the script."""
    global SILENT_MODE, DEBUG_MODE, PUBLISH_TO_MQTT, POLL_INTERVAL, RUN_ONCE  # pylint: disable=global-statement

    # Parse command line arguments
    args = parse_arguments()

    # Update global variables based on arguments
    SILENT_MODE = args.silent
    DEBUG_MODE = args.debug
    PUBLISH_TO_MQTT = not args.debug
    RUN_ONCE = args.once

    # Override poll interval if specified
    if args.poll:
        POLL_INTERVAL = args.poll

    # Setup logging with appropriate level
    setup_logging(debug_mode=DEBUG_MODE, silent_mode=SILENT_MODE)

    # Show configuration and exit if requested
    if args.show_config:
        show_configuration()
        sys.exit(0)

    # Handle --save mode: save API data to file and exit
    if args.save:
        logger.info("=" * 70)
        logger.info("myUplink API Data Export to JSON")
        logger.info("=" * 70)
        logger.info("")

        # Set up OAuth session
        myuplink = setup_oauth_session()
        if myuplink is None:
            sys.exit(1)

        # Save data to file
        logger.info(f"Saving all API data to: {args.save}")
        success = save_api_data_to_file(myuplink, args.save)

        if success:
            logger.info("Data export completed successfully")
            sys.exit(0)
        else:
            logger.error("Data export failed")
            sys.exit(1)

    # Log banner (only shown if not silent mode)
    logger.info("=" * 70)
    logger.info("myUplink to MQTT Bridge with Home Assistant Auto-Discovery")
    logger.info("=" * 70)
    if DEBUG_MODE:
        logger.warning("Running in DEBUG mode - data will NOT be published to MQTT")
    logger.info("")

    # Run the async main loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        success = loop.run_until_complete(main_loop())
        sys.exit(0 if success else 1)
    finally:
        loop.close()


if __name__ == "__main__":
    main()
