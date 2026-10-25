"""Main script to bridge myUplink API data to MQTT with Home Assistant auto-discovery.

This script continuously polls the myUplink API for device data and publishes
it to an MQTT broker with Home Assistant auto-discovery configuration.
Follows the repository patterns for OAuth authentication and error handling.
"""

import argparse
import asyncio
import json
import logging
import math
import os
import socket
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from myuplink2mqtt.utils.auto_discovery_utils import (
    clean_enum_text,
    determine_entity_category,
    determine_value_type,
    normalize_enum_value,
    publish_cached_discovery,
    publish_ha_discovery,
    publish_ha_entity_discovery,
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
    set_device_point,
)

# Configure logging
logger = logging.getLogger(__name__)

# MQTT Configuration
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "127.0.0.1")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_BASE_TOPIC = os.getenv("MQTT_BASE_TOPIC", "myuplink")

# Home Assistant Discovery Configuration
HA_DISCOVERY_PREFIX = os.getenv("HA_DISCOVERY_PREFIX", "homeassistant")

# Poll interval in seconds (can be overridden by command line)
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))  # Default: 1 minute

# MQTT client state
MQTT_CONNECTED = False
WRITABLE_POINTS = {}

# Command line options (set by parse_arguments)
SILENT_MODE = False
DEBUG_MODE = False
PUBLISH_TO_MQTT = True
RUN_ONCE = False
DISCOVERY_PREFIX = ""
MQTT_HOST = ""
SEND_ALL_PARAMETERS = False


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
        help="Set poll interval in seconds (default: 60)",
    )

    parser.add_argument(
        "--host",
        metavar="HOST",
        help="Set MQTT broker host (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--discovery-prefix",
        metavar="PREFIX",
        help="Set Home Assistant discovery prefix (default: homeassistant, e.g., 'domoticz')",
    )

    parser.add_argument(
        "--send-all",
        action="store_true",
        help="Send all parameters as-is without filtering (default: filter unused/invalid parameters)",
    )

    return parser.parse_args()


def on_mqtt_connect(client, userdata, flags, reason_code, properties):  # pylint: disable=unused-argument
    """Handle MQTT client connection event."""
    global MQTT_CONNECTED  # pylint: disable=global-statement
    if reason_code.value == 0:
        MQTT_CONNECTED = True
        for topic in (
            f"{MQTT_BASE_TOPIC}/+/+/+/set",
            f"{HA_DISCOVERY_PREFIX}/status",
        ):
            result, _message_id = client.subscribe(topic, qos=1)
            if isinstance(result, int) and result != 0:
                logger.error("Failed to subscribe to MQTT topic %s (rc: %s)", topic, result)
        auth_msg = " (authenticated)" if MQTT_USERNAME else ""
        broker_info = f"{MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}"
        logger.info(f"Connected to MQTT broker at {broker_info}{auth_msg}")
    else:
        MQTT_CONNECTED = False
        broker_info = f"{MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}"
        logger.error(f"Failed MQTT connect to {broker_info}, rc: {reason_code.value}")


def on_mqtt_message(client: Any, userdata: Any, message: Any) -> None:
    """Handle Home Assistant birth messages and writable-point commands."""
    if message.topic == f"{HA_DISCOVERY_PREFIX}/status":
        _handle_home_assistant_status(client, message)
        return

    _handle_mqtt_write(userdata, message)


def _handle_home_assistant_status(client: Any, message: Any) -> None:
    """Replay discovery configurations after Home Assistant reports online."""
    status = message.payload.decode("utf-8", errors="replace").strip().lower()
    if status == "online":
        logger.info("Home Assistant is online; republishing discovery configurations")
        publish_cached_discovery(client)


def _handle_mqtt_write(userdata: Any, message: Any) -> None:
    """Validate and send one writable-point command."""
    address = _get_command_address(message)
    if address is None:
        return

    system_id, device_id, parameter_id = address
    point = WRITABLE_POINTS.get((system_id, device_id, parameter_id))
    if point is None or point.get("writable") is not True:
        logger.error(
            "Ignoring command for unknown or non-writable point %s on device %s",
            parameter_id,
            device_id,
        )
        return

    try:
        requested_value = message.payload.decode("utf-8").strip()
    except UnicodeDecodeError:
        logger.error("Ignoring non-text command for point %s", parameter_id)
        return

    api_value = parse_write_command(point, requested_value)
    if api_value is None:
        logger.error(
            "Rejected invalid command value for point %s on device %s: %r",
            parameter_id,
            device_id,
            requested_value,
        )
        return

    if userdata is None:
        logger.error("Cannot write point %s: myUplink session is unavailable", parameter_id)
        return

    if set_device_point(userdata, device_id, parameter_id, api_value):
        logger.info(
            "Accepted MQTT command for point %s on device %s; next poll will publish state",
            parameter_id,
            device_id,
        )


def _get_command_address(message: Any) -> Optional[Tuple[str, str, str]]:
    """Return system, device, and point IDs for a valid non-retained command."""
    if message.retain:
        logger.warning("Ignoring retained MQTT command on %s", message.topic)
        return None

    command_prefix = f"{MQTT_BASE_TOPIC}/"
    if not message.topic.startswith(command_prefix):
        return None

    topic_parts = message.topic[len(command_prefix) :].split("/")
    if len(topic_parts) != 4 or topic_parts[3] != "set":
        logger.warning("Ignoring malformed MQTT command topic %s", message.topic)
        return None
    return topic_parts[0], topic_parts[1], topic_parts[2]


def parse_write_command(point: Dict[str, Any], requested_value: str) -> Optional[str]:
    """Validate an MQTT command and convert it to a myUplink API value."""
    enum_values = point.get("enumValues") or []
    if enum_values:
        return _parse_enum_command(enum_values, requested_value)

    current_value = point.get("value")
    if _is_switch_point(point):
        return _parse_switch_command(current_value, requested_value)

    if isinstance(current_value, (int, float)) and not isinstance(current_value, bool):
        return _parse_numeric_command(point, requested_value)

    return requested_value


def _parse_enum_command(enum_values: List[Dict[str, Any]], requested_value: str) -> Optional[str]:
    """Resolve a displayed enum label to its REST API value."""
    normalized_value = clean_enum_text(requested_value).casefold()
    for item in enum_values:
        label = clean_enum_text(str(item.get("text", "")))
        enum_value = str(item.get("value", "")).strip()
        if enum_value and (
            normalized_value == label.casefold()
            or normalize_enum_value(requested_value) == normalize_enum_value(enum_value)
        ):
            return enum_value
    return None


def _is_switch_point(point: Dict[str, Any]) -> bool:
    """Determine whether a writable point is represented as a switch."""
    value = point.get("value")
    return isinstance(value, bool) or (
        isinstance(value, (int, float)) and not point.get("parameterUnit") and value in (0, 1)
    )


def _parse_switch_command(current_value: Any, requested_value: str) -> Optional[str]:
    """Convert Home Assistant ON/OFF payloads to the point's API representation."""
    normalized = requested_value.strip().upper()
    if normalized not in ("ON", "OFF", "TRUE", "FALSE", "1", "0"):
        return None
    is_on = normalized in ("ON", "TRUE", "1")
    return (
        ("true" if is_on else "false")
        if isinstance(current_value, bool)
        else ("1" if is_on else "0")
    )


def _parse_numeric_command(point: Dict[str, Any], requested_value: str) -> Optional[str]:
    """Validate a numeric command against API-provided bounds."""
    try:
        numeric_value = float(requested_value)
    except ValueError:
        return None
    if not math.isfinite(numeric_value):
        return None

    try:
        minimum = point.get("minValue")
        maximum = point.get("maxValue")
        step = point.get("stepValue")
        if minimum is not None and numeric_value < float(minimum):
            return None
        if maximum is not None and numeric_value > float(maximum):
            return None
        if minimum is not None and step is not None:
            step_value = float(step)
            if step_value > 0:
                increments = (numeric_value - float(minimum)) / step_value
                if not math.isclose(increments, round(increments), abs_tol=1e-8):
                    return None
    except (TypeError, ValueError):
        logger.warning("Ignoring invalid bounds for writable point %s", point.get("parameterId"))
        return None
    return requested_value


def on_mqtt_disconnect(client, userdata, flags, reason_code, properties):  # pylint: disable=unused-argument
    """Handle MQTT client disconnection event."""
    global MQTT_CONNECTED  # pylint: disable=global-statement
    MQTT_CONNECTED = False
    logger.error(f"Disconnected from MQTT broker (rc: {reason_code.value})")


def create_mqtt_client(userdata: Optional[Any] = None) -> Any:
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
    client.on_message = on_mqtt_message
    client.user_data_set(userdata)

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


def should_send_parameter(parameter_info):
    """Check if a parameter should be sent to MQTT.

    By default, filters out parameters with "Not used" value (case-insensitive).
    Can be disabled with --send-all flag.

    Args:
        parameter_info (dict): Parameter information with keys: value, strVal, etc.

    Returns:
        bool: True if parameter should be sent, False otherwise.

    """
    # If SEND_ALL_PARAMETERS is enabled, send everything
    if SEND_ALL_PARAMETERS:
        return True

    # Filter out "Not used" values (case-insensitive)
    # Check both value (direct string values) and strVal (for enum parameters)
    value = parameter_info.get("value")
    if isinstance(value, str) and value.lower() == "not used":
        return False

    str_val = parameter_info.get("strVal")
    if isinstance(str_val, str) and str_val.lower() == "not used":
        return False

    return True


def extract_installation_date_values(points_data):
    """Extract installation year, month, day from point data.

    Looks for both simple (Year/Month/Day) and text-not-found parameter versions.

    Args:
        points_data (list): List of parameter points.

    Returns:
        tuple: (year, month, day, year_point, month_point, day_point) or (None, None, None, None, None, None).

    """
    # Map param IDs to their corresponding variables
    param_map = {
        "8556": ("year", "year_point"),  # Year
        "8557": ("month", "month_point"),  # Month
        "8558": ("day", "day_point"),  # Day
        "60305": ("year", "year_point"),  # Installation year (text not found)
        "60306": ("month", "month_point"),  # Installation month (text not found)
        "60307": ("day", "day_point"),  # Installation day (text not found)
    }

    values = {
        "year": None,
        "month": None,
        "day": None,
        "year_point": None,
        "month_point": None,
        "day_point": None,
    }

    for point in points_data:
        param_id = point.get("parameterId")
        if param_id in param_map:
            var_name, point_var = param_map[param_id]
            values[point_var] = point
            # For simple IDs (855x), always set value; for text-not-found (603x), only if not set
            if values[var_name] is None or not param_id.startswith("603"):
                values[var_name] = (
                    int(point["value"]) if isinstance(point["value"], (int, float)) else None
                )

    return (
        values["year"],
        values["month"],
        values["day"],
        values["year_point"],
        values["month_point"],
        values["day_point"],
    )


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
        value_str = normalize_enum_value(value)
        # Find matching enum text
        for enum_item in enum_values:
            if normalize_enum_value(enum_item.get("value")) == value_str:
                state_value = clean_enum_text(str(enum_item.get("text", value)))
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


def process_installation_date_parameter(
    mqtt_client, device_info, system_id, year, month, day, send_discovery
):
    """Process installation date as a virtual parameter.

    Args:
        mqtt_client: MQTT client instance or None.
        device_info (dict): Device information.
        system_id (str): System ID.
        year: Installation year component.
        month: Installation month component.
        day: Installation day component.
        send_discovery (bool): Whether to send discovery.

    Returns:
        tuple: (points_published, discovery_sent)

    """
    points_published = 0
    discovery_sent = 0

    if year is not None and month is not None and day is not None:
        installation_date_value = f"{year:04d}-{month:02d}-{day:02d}"
        parameter_info = {
            "id": "installation_date",
            "name": "Installation date",
            "value": installation_date_value,
            "unit": "",
            "value_type": "string",
            "category": "diagnostic",
            "enum_values": [],
        }

        if should_send_parameter(parameter_info):
            if PUBLISH_TO_MQTT and mqtt_client is not None:
                if send_discovery:
                    publish_ha_discovery(
                        mqtt_client, device_info, parameter_info, system_id, HA_DISCOVERY_PREFIX
                    )
                    discovery_sent += 1

                publish_sensor_state(
                    mqtt_client,
                    system_id,
                    parameter_info["id"],
                    parameter_info["value"],
                    parameter_info.get("enum_values", []),
                )

            points_published += 1
            logger.debug(
                f"Published virtual parameter: {parameter_info['name']} = {installation_date_value}"
            )

    return points_published, discovery_sent


def process_data_points(mqtt_client, device_info, system_id, points_data, send_discovery):
    """Process each data point for the device.

    Args:
        mqtt_client: MQTT client instance or None.
        device_info (dict): Device information.
        system_id (str): System ID.
        points_data (list): List of data points.
        send_discovery (bool): Whether to send discovery.

    Returns:
        tuple: (points_published, discovery_sent)

    """
    points_published = 0
    discovery_sent = 0

    for point in points_data:
        param_id = point.get("parameterId")
        if param_id in (
            "8556",
            "8557",
            "8558",
            "60305",
            "60306",
            "60307",
        ):
            logger.debug(f"Skipping installation date component: {param_id}")
            continue

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
            "strVal": point.get("strVal"),
            "writable": point.get("writable") is True,
            "min_value": point.get("minValue"),
            "max_value": point.get("maxValue"),
            "step_value": point.get("stepValue"),
            "scale_value": point.get("scaleValue"),
        }

        if not should_send_parameter(parameter_info):
            logger.debug(
                f"Skipping parameter {parameter_info['id']}: {parameter_info['name']} (filtered)"
            )
            continue

        if parameter_info["writable"]:
            WRITABLE_POINTS[(str(system_id), str(device_info["id"]), str(param_id))] = point

        if PUBLISH_TO_MQTT and mqtt_client is not None:
            if send_discovery:
                publish_ha_discovery(
                    mqtt_client, device_info, parameter_info, system_id, HA_DISCOVERY_PREFIX
                )
                discovery_sent += 1

            is_switch = parameter_info["writable"] and (
                isinstance(point["value"], bool)
                or (
                    not parameter_info["unit"]
                    and isinstance(point["value"], (int, float))
                    and point["value"] in (0, 1)
                )
            )
            state_value = parameter_info["value"]
            is_binary = (
                is_switch
                or isinstance(state_value, bool)
                or (
                    not parameter_info["writable"]
                    and parameter_info["value_type"] == "int"
                    and not parameter_info["unit"]
                )
            )
            if is_binary:
                state_value = "ON" if bool(state_value) else "OFF"
            publish_sensor_state(
                mqtt_client,
                system_id,
                parameter_info["id"],
                state_value,
                parameter_info.get("enum_values", []),
            )

        points_published += 1

    return points_published, discovery_sent


def publish_device_connection(
    mqtt_client: Any,
    system_id: str,
    device_id: str,
    device_name: str,
    device_info: Dict[str, Any],
    device_data: Dict[str, Any],
    send_discovery: bool,
) -> None:
    """Publish a device connectivity binary sensor when the API reports state."""
    connection_state = device_data.get("connectionState")
    if connection_state is None:
        connection_state = device_data.get("connectionStatus")
    if connection_state in ("Connected", "ONLINE", True, 1):
        connected = True
    elif connection_state in ("Disconnected", "OFFLINE", False, 0):
        connected = False
    else:
        connected = None

    connection_topic = f"{MQTT_BASE_TOPIC}/{system_id}/{device_id}/connection"
    if send_discovery:
        publish_ha_entity_discovery(
            mqtt_client,
            "binary_sensor",
            f"myuplink_{device_id}_connection",
            f"{device_name} connection",
            device_info,
            connection_topic,
            f"{MQTT_BASE_TOPIC}/{system_id}/available",
            {
                "device_class": "connectivity",
                "entity_category": "diagnostic",
                "payload_on": "ON",
                "payload_off": "OFF",
            },
            HA_DISCOVERY_PREFIX,
        )
    if connected is not None:
        mqtt_client.publish(
            connection_topic,
            "ON" if connected else "OFF",
            qos=1,
            retain=True,
        )


def publish_device_firmware(
    mqtt_client: Any,
    system_id: str,
    device_id: str,
    device_name: str,
    device_info: Dict[str, Any],
    device_data: Dict[str, Any],
    send_discovery: bool,
) -> None:
    """Publish installed and desired firmware as a read-only MQTT update entity."""
    firmware = device_data.get("firmware") or {}
    installed_version = firmware.get("currentFwVersion") or device_data.get("currentFwVersion")
    latest_version = firmware.get("desiredFwVersion") or device_data.get("desiredFwVersion")
    firmware_topic = f"{MQTT_BASE_TOPIC}/{system_id}/{device_id}/firmware"
    if send_discovery:
        publish_ha_entity_discovery(
            mqtt_client,
            "update",
            f"myuplink_{device_id}_firmware",
            f"{device_name} firmware",
            device_info,
            firmware_topic,
            f"{MQTT_BASE_TOPIC}/{system_id}/available",
            {"device_class": "firmware", "title": "Firmware"},
            HA_DISCOVERY_PREFIX,
        )
    firmware_state = {}
    if installed_version:
        firmware_state["installed_version"] = installed_version
    if latest_version:
        firmware_state["latest_version"] = latest_version
    if firmware_state:
        mqtt_client.publish(
            firmware_topic,
            json.dumps(firmware_state),
            qos=1,
            retain=True,
        )


def process_device(myuplink, mqtt_client, system_id, device_id, send_discovery=False):
    """Process a single device: retrieve data and publish to MQTT.

    Args:
        myuplink: OAuth2Session for myUplink API.
        mqtt_client: MQTT client instance or None if not publishing.
        system_id (str): System ID.
        device_id (str): Device ID.
        send_discovery (bool): Whether to send HA discovery messages (first cycle only).

    Returns:
        int: Number of entities (data points) published for this device.

    """
    device_data = get_device_details(myuplink, device_id)
    if device_data is None:
        logger.error(f"Could not retrieve device details for {device_id}")
        return 0

    device_name = device_data["product"]["name"]
    product_name = device_data["product"]["name"]
    manufacturer = product_name.split(" ", 1)[0] if " " in product_name else "Unknown"
    model = product_name.split(" ", 1)[1] if " " in product_name else product_name

    device_info = {
        "id": device_id,
        "name": device_name,
        "manufacturer": manufacturer,
        "model": model,
        "serial": device_data.get("serialNumber", ""),
    }
    logger.debug(f"Processing device: {device_name} ({device_id})")

    for key in tuple(WRITABLE_POINTS):
        if key[:2] == (system_id, str(device_id)):
            del WRITABLE_POINTS[key]

    points_data = get_device_points(myuplink, device_id)
    if points_data is None:
        logger.error(f"Could not retrieve data points for {device_id}")
        return 0
    logger.debug(f"Retrieved {len(points_data)} data points")

    year, month, day, _year_point, _month_point, _day_point = extract_installation_date_values(
        points_data
    )

    if PUBLISH_TO_MQTT and mqtt_client is not None:
        publish_device_connection(
            mqtt_client, system_id, device_id, device_name, device_info, device_data, send_discovery
        )
        publish_device_firmware(
            mqtt_client, system_id, device_id, device_name, device_info, device_data, send_discovery
        )

    points_published, discovery_sent = process_installation_date_parameter(
        mqtt_client, device_info, system_id, year, month, day, send_discovery
    )

    additional_points, additional_discovery = process_data_points(
        mqtt_client, device_info, system_id, points_data, send_discovery
    )

    points_published += additional_points
    discovery_sent += additional_discovery

    if PUBLISH_TO_MQTT:
        if send_discovery:
            logger.info(f"Sent {discovery_sent} HA discovery configs (retained at broker)")
        logger.debug(f"Published {points_published} state updates to MQTT")
    else:
        logger.debug(f"Would publish {points_published} data points (debug mode)")
    return points_published


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


def connect_mqtt_broker(myuplink: Optional[Any] = None) -> Optional[Any]:
    """Connect to MQTT broker.

    Returns:
        mqtt.Client or None: MQTT client if successful, None otherwise.

    """
    logger.info("Connecting to MQTT broker...")
    mqtt_client = create_mqtt_client(myuplink)

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

    entities_published = 0

    # Get systems
    systems = get_systems(myuplink)
    if systems is None:
        logger.error("Failed to retrieve systems")
        return entities_published
    logger.debug(f"Retrieved {len(systems)} system(s)")

    # Process each system
    for system in systems:
        system_id = system["systemId"]
        system_name = system["name"]
        logger.debug(f"System: {system_name} (ID: {system_id})")
        logger.debug(f"Devices: {len(system['devices'])}")

        if PUBLISH_TO_MQTT and mqtt_client:
            publish_availability(mqtt_client, system_id, available=True)
            system_device = {
                "id": f"system_{system_id}",
                "name": system_name,
                "manufacturer": "myUplink",
                "model": "System",
            }
            alarm_topic = f"{MQTT_BASE_TOPIC}/{system_id}/alarm"
            if send_discovery:
                publish_ha_entity_discovery(
                    mqtt_client,
                    "binary_sensor",
                    f"myuplink_system_{system_id}_alarm",
                    f"{system_name} active alarm",
                    system_device,
                    alarm_topic,
                    f"{MQTT_BASE_TOPIC}/{system_id}/available",
                    {
                        "device_class": "problem",
                        "entity_category": "diagnostic",
                        "payload_on": "ON",
                        "payload_off": "OFF",
                    },
                    HA_DISCOVERY_PREFIX,
                )
            if isinstance(system.get("hasAlarm"), bool):
                mqtt_client.publish(
                    alarm_topic,
                    "ON" if system["hasAlarm"] else "OFF",
                    qos=1,
                    retain=True,
                )

        # Process each device
        for device in system["devices"]:
            device_id = device["id"]
            entities_published += process_device(
                myuplink, mqtt_client, system_id, device_id, send_discovery
            )

    return entities_published


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


def sd_notify(message):
    """Send a status message to systemd (no-op when not run under a notify service).

    Args:
        message: Notification string, e.g. "READY=1" or "WATCHDOG=1".

    """
    addr = os.getenv("NOTIFY_SOCKET")
    if not addr:
        return
    if addr.startswith("@"):
        addr = "\0" + addr[1:]
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
            sock.connect(addr)
            sock.sendall(message.encode())
    except OSError as e:
        logger.warning(f"sd_notify failed: {e}")


async def main_loop():
    """Poll myUplink API and publish data to MQTT."""
    # Set up OAuth session
    myuplink = setup_oauth_session()
    if myuplink is None:
        return False

    # Connect to MQTT broker (skip if debug mode without publishing)
    mqtt_client = None
    if PUBLISH_TO_MQTT:
        mqtt_client = connect_mqtt_broker(myuplink)
        if mqtt_client is None:
            return False

    # Log startup information
    log_startup_info()

    sd_notify("READY=1")

    loop_count = 0
    try:
        while True:
            loop_count += 1
            entities_published = process_poll_cycle(myuplink, mqtt_client, loop_count)
            logger.info(
                f"Poll cycle {loop_count} complete (entities published: {entities_published})"
            )
            # Only ping after a completed cycle so a hung poll triggers a restart
            sd_notify("WATCHDOG=1")

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
    global SILENT_MODE, DEBUG_MODE, PUBLISH_TO_MQTT, POLL_INTERVAL, RUN_ONCE, DISCOVERY_PREFIX, HA_DISCOVERY_PREFIX, MQTT_BROKER_HOST, MQTT_HOST, SEND_ALL_PARAMETERS  # pylint: disable=global-statement

    # Parse command line arguments
    args = parse_arguments()

    # Update global variables based on arguments
    SILENT_MODE = args.silent
    DEBUG_MODE = args.debug
    PUBLISH_TO_MQTT = not args.debug
    RUN_ONCE = args.once
    SEND_ALL_PARAMETERS = args.send_all

    # Override poll interval if specified
    if args.poll:
        POLL_INTERVAL = args.poll

    # Override MQTT host if specified
    if args.host:
        MQTT_BROKER_HOST = args.host
        MQTT_HOST = args.host

    # Override discovery prefix if specified
    if args.discovery_prefix:
        HA_DISCOVERY_PREFIX = args.discovery_prefix
        DISCOVERY_PREFIX = args.discovery_prefix

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
