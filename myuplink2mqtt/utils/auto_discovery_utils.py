"""Utilities for Home Assistant MQTT auto-discovery configuration generation.

This module provides functionality to generate Home Assistant compatible
MQTT discovery payloads for myUplink API devices and parameters.
"""

import json
import logging
import os

# Configure logging
logger = logging.getLogger(__name__)

# Home Assistant Discovery Configuration
HA_DISCOVERY_PREFIX = os.getenv("HA_DISCOVERY_PREFIX", "homeassistant")

# MQTT Base Topic
MQTT_BASE_TOPIC = os.getenv("MQTT_BASE_TOPIC", "myuplink")


def normalize_unit(unit):
    """Normalize unit of measurement strings.

    Args:
        unit (str): The unit string to normalize.

    Returns:
        str: Normalized unit string.

    """
    # Map non-standard units to standard representations
    unit_normalization_map = {
        "rh%": "%",  # Relative humidity: rh% -> %
        "l/m": "l/hr",  # Liters per minute: l/m -> l/hr (60x conversion)
        "l/hr": "l/hr",  # Liters per hour: already in desired format
    }
    return unit_normalization_map.get(unit, unit)


def get_unit_to_device_class_mapping():
    """Get mapping of parameter units to Home Assistant device classes.

    Returns:
        dict: Dictionary mapping units to device classes.

    """
    return {
        "°C": "temperature",
        "C": "temperature",
        "°F": "temperature",
        "F": "temperature",
        "kW": "power",
        "W": "power",
        "kWh": "energy",
        "Wh": "energy",
        "A": "current",
        "V": "voltage",
        "rh%": "humidity",
        "bar": "pressure",
        "Pa": "pressure",
        "hPa": "pressure",
        "l/m": "volume_flow_rate",
        "l/min": "volume_flow_rate",
        "l/hr": "volume_flow_rate",
        "m³/h": "volume_flow_rate",
    }


def get_parameter_id_to_device_class_mapping():
    """Get mapping of specific parameter IDs to device classes.

    Returns:
        dict: Dictionary mapping parameter IDs to device classes.

    """
    return {
        "43161": "binary_sensor",  # Electricity add (alarm)
        "60433": "humidity",  # Relative humidity
        "installation_date": "date",  # Installation date (virtual parameter)
    }


def determine_device_class(parameter_unit, parameter_id):
    """Determine Home Assistant device class based on unit or parameter ID.

    Args:
        parameter_unit (str): The parameter unit from API.
        parameter_id (str): The parameter ID.

    Returns:
        str or None: Device class for Home Assistant or None if no specific class.

    """
    # Check if parameter ID maps to a known device class
    id_mapping = get_parameter_id_to_device_class_mapping()
    if parameter_id in id_mapping:
        return id_mapping[parameter_id]

    # Check if unit maps to a known device class
    unit_mapping = get_unit_to_device_class_mapping()
    if parameter_unit in unit_mapping:
        return unit_mapping[parameter_unit]

    return None


def determine_value_type(value):
    """Determine the type of a parameter value.

    Args:
        value: The parameter value.

    Returns:
        str: Type description ('bool', 'int', 'float', or 'string').

    """
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    return "string"


def has_enum_values(parameter_info):
    """Check if parameter has enumValues defined.

    Args:
        parameter_info (dict): Parameter information dictionary.

    Returns:
        bool: True if parameter has enumValues, False otherwise.

    """
    enum_values = parameter_info.get("enum_values", [])
    return bool(enum_values) and len(enum_values) > 0


def clean_enum_text(text):
    """Clean enum text by removing newlines and extra whitespace.

    Args:
        text (str): Enum text to clean.

    Returns:
        str: Cleaned enum text.

    """
    if not text:
        return text
    # Remove newlines, carriage returns, and normalize whitespace
    cleaned = text.replace("\r", "").replace("\n", "")
    # Replace multiple spaces with single space
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned.strip()


def build_enum_options(enum_values):
    """Build list of enum option values for Home Assistant select entity.

    Args:
        enum_values (list): List of enum value dictionaries from API.

    Returns:
        list: List of cleaned enum text values for select options.

    """
    options = []
    for enum_item in enum_values:
        text = enum_item.get("text", "")
        cleaned_text = clean_enum_text(text)
        if cleaned_text:
            options.append(cleaned_text)
    return options


def determine_entity_category(parameter_id, parameter_name):
    """Determine Home Assistant entity category based on parameter.

    Args:
        parameter_id (str): The parameter ID.
        parameter_name (str): The parameter name.

    Returns:
        str or None: Entity category ('diagnostic', 'config') or None for regular sensors.

    """
    # Diagnostic parameters - informational only, not for control
    diagnostic_ids = {
        "43161",  # Electricity add (alarm)
        "43437",  # Compressor active accumulated time
        "43438",  # Compressor starts
    }

    # Check if parameter ID is in diagnostic list
    if parameter_id in diagnostic_ids:
        return "diagnostic"

    # Check if parameter name suggests diagnostic nature
    diagnostic_keywords = ["accumulated", "total", "starts", "runtime", "hours", "alarm", "error"]
    param_lower = parameter_name.lower()
    if any(keyword in param_lower for keyword in diagnostic_keywords):
        return "diagnostic"

    return None


def clean_parameter_name(parameter_name, device_name):
    """Remove device name prefix from parameter name if present.

    Args:
        parameter_name (str): Full parameter name from API (e.g., "SAK (Set automatically)")
        device_name (str): Device name to remove (e.g., "SAK")

    Returns:
        str: Cleaned parameter name (e.g., "Set automatically")

    """
    # Check if parameter starts with "DeviceName (" and ends with ")"
    prefix = f"{device_name} ("
    if parameter_name.startswith(prefix):
        # Find the matching closing parenthesis (handling nested parentheses)
        # Start counting after the opening parenthesis we know is there
        paren_count = 1
        start_idx = len(prefix)

        for i in range(start_idx, len(parameter_name)):
            if parameter_name[i] == "(":
                paren_count += 1
            elif parameter_name[i] == ")":
                paren_count -= 1
                if paren_count == 0:
                    # Found the matching closing parenthesis
                    if i == len(parameter_name) - 1:
                        # It's at the end, so extract the content
                        return parameter_name[start_idx:i]
                    break

    return parameter_name


def _add_enum_configuration(payload, parameter_info, state_topic):
    """Add enum-specific configuration to discovery payload.

    Args:
        payload (dict): Discovery payload to modify.
        parameter_info (dict): Parameter information with enum_values.
        state_topic (str): MQTT state topic.

    """
    enum_values = parameter_info.get("enum_values", [])
    options = build_enum_options(enum_values)
    payload["options"] = options

    # Add command topic for select entity (allows Home Assistant to send commands)
    # Extract system_id from state_topic (format: myuplink/{system_id}/{parameter_id}/value)
    state_topic_parts = state_topic.split("/")
    if len(state_topic_parts) >= 2:
        system_id = state_topic_parts[1]
        command_topic = f"{MQTT_BASE_TOPIC}/{system_id}/{parameter_info['id']}/set"
        payload["command_topic"] = command_topic

    # Get current value's text representation
    current_value = parameter_info.get("value")
    current_text = (
        str(int(current_value)) if isinstance(current_value, float) else str(current_value)
    )

    # Find the text for current value
    for enum_item in enum_values:
        if enum_item.get("value") == current_text:
            payload["value_template"] = "{{ value }}"
            break


def build_discovery_payload(device_info, parameter_info, state_topic, availability_topic):
    """Build Home Assistant discovery payload.

    Args:
        device_info (dict): Device information with keys: id, name, manufacturer, model,
                           serial (optional).
        parameter_info (dict): Parameter information with keys: id, name, value, unit,
                              value_type, category (optional), enum_values (optional).
        state_topic (str): MQTT state topic.
        availability_topic (str): MQTT availability topic.

    Returns:
        dict: Discovery payload for Home Assistant MQTT integration.

    """
    device_class = determine_device_class(parameter_info.get("unit", ""), parameter_info["id"])

    # Clean the parameter name to remove device name prefix
    clean_name = clean_parameter_name(parameter_info["name"], device_info["device_name"])

    discovery_payload = {
        "name": clean_name,
        "object_id": f"myuplink_{device_info['id']}_{parameter_info['id']}",
        "unique_id": f"myuplink_{device_info['id']}_{parameter_info['id']}",
        "state_topic": state_topic,
        "availability_topic": availability_topic,
        "availability_mode": "latest",
        "payload_available": "online",
        "payload_not_available": "offline",
        "enabled_by_default": True,
        "origin": {
            "name": "myUplink2mqtt",
            "sw": "1.0.0",
            "url": "https://github.com/j-b-n/myUplink2mqtt",
        },
        "device": {
            "identifiers": [f"myuplink_{device_info['id']}"],
            "device_name": device_info["device_name"],
            "manufacturer": device_info["manufacturer"],
            "model": device_info["model"],
        },
    }

    # Add serial number if available
    if device_info.get("serial"):
        discovery_payload["device"]["serial_number"] = device_info["serial"]

    # Check if parameter has enumValues for select entity
    if has_enum_values(parameter_info):
        _add_enum_configuration(discovery_payload, parameter_info, state_topic)
    else:
        # Add unit for sensor platforms (not binary sensors or enums)
        value_type = parameter_info.get("value_type", "string")
        original_unit = parameter_info.get("unit", "")
        unit = normalize_unit(original_unit)
        is_binary = value_type == "bool" or (value_type == "int" and not unit)

        if not is_binary and unit:
            discovery_payload["unit_of_measurement"] = unit

        # Add device class if available
        if device_class:
            discovery_payload["device_class"] = device_class

        # Add value template for unit conversions
#        if original_unit == "l/m" and unit == "l/hr":
#            # Convert liters per minute to liters per hour (multiply by 60)
#            discovery_payload["value_template"] = "{{ (value | float(0) * 60) | round(2) }}"

        # Add state class for numeric sensors
        if not is_binary and unit:
            if unit in ["kWh", "Wh"]:
                discovery_payload["state_class"] = "total_increasing"
            else:
                discovery_payload["state_class"] = "measurement"

    # Add entity category if specified
    if parameter_info.get("category"):
        discovery_payload["entity_category"] = parameter_info["category"]

    return discovery_payload


def publish_ha_discovery(
    mqtt_client, device_info, parameter_info, system_id, discovery_prefix=None
):
    """Publish Home Assistant MQTT discovery configuration.

    Determines the appropriate Home Assistant component based on parameter type:
    - "select" for parameters with enumValues (options list)
    - "binary_sensor" for boolean or single-value integer parameters
    - "sensor" for numeric and string parameters

    Args:
        mqtt_client: MQTT client instance.
        device_info (dict): Device information with keys: id, name, manufacturer, model,
                           serial (optional).
        parameter_info (dict): Parameter information with keys: id, name, value, unit,
                              value_type, enum_values (optional).
        system_id (str): System ID for topic structure.
        discovery_prefix (str, optional): Home Assistant discovery prefix (default: from env).

    Returns:
        bool: True if published successfully, False otherwise.

    """
    try:
        # Use provided discovery prefix or fall back to environment variable
        prefix = discovery_prefix if discovery_prefix else HA_DISCOVERY_PREFIX

        # Determine component type
        # Priority: enum > binary_sensor > text (for string values) > sensor
        if has_enum_values(parameter_info):
            component = "select"
        else:
            value_type = parameter_info.get("value_type", "string")
            unit = parameter_info.get("unit", "")
            is_binary = value_type == "bool" or (value_type == "int" and not unit)

            # Use "text" component for string values with no unit (like dates)
            if value_type == "string" and not unit:
                component = "text"
            elif is_binary:
                component = "binary_sensor"
            else:
                component = "sensor"

        # Create unique object ID
        unique_id = f"myuplink_{device_info['id']}_{parameter_info['id']}"

        # Discovery topic
        discovery_topic = f"{prefix}/{component}/{unique_id}/config"

        # State topic
        state_topic = f"{MQTT_BASE_TOPIC}/{system_id}/{parameter_info['id']}/value"

        # Availability topic
        availability_topic = f"{MQTT_BASE_TOPIC}/{system_id}/available"

        # Build and publish discovery payload
        discovery_payload = build_discovery_payload(
            device_info, parameter_info, state_topic, availability_topic
        )

        # Log the discovery payload for debugging
        logger.debug(f"Discovery payload for {unique_id}: {json.dumps(discovery_payload)}")

        mqtt_client.publish(discovery_topic, json.dumps(discovery_payload), qos=1, retain=True)
        return True
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"Failed to publish discovery for {parameter_info.get('id', 'unknown')}: {e}")
        return False
