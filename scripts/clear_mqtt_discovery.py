#!/usr/bin/env python3
"""Clear all myUplink MQTT topics including discovery configs and data values.

This utility removes all retained MQTT messages for myUplink devices including:
- Home Assistant discovery configurations (scans for ALL existing topics)
- Data value topics (myuplink/{system_id}/{parameter_id}/value)
- Availability topics (myuplink/{system_id}/available)

Uses the same configuration pattern as the main myUplink2mqtt project.
"""

import os
import sys
import time
from collections import defaultdict
from pathlib import Path

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import utilities from the module
from myuplink2mqtt.utils.myuplink_utils import (
    check_oauth_prerequisites,
    create_oauth_session,
)

# MQTT Configuration (matches myUplink2mqtt.py)
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "10.0.0.2")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_CLIENT_ID = "myuplink_discovery_cleanup"
MQTT_BASE_TOPIC = os.getenv("MQTT_BASE_TOPIC", "myuplink")

# Home Assistant Discovery Configuration
HA_DISCOVERY_PREFIX = os.getenv("HA_DISCOVERY_PREFIX", "homeassistant")

# HTTP status code for successful requests
HTTP_STATUS_OK = 200

# Global storage for discovered topics
DISCOVERED_TOPICS = defaultdict(list)
DISCOVERY_COMPLETE = False


def on_message(client, userdata, message):
    """Store topic for clearing when a message is received."""
    _ = (client, userdata)  # Unused
    topic = message.topic
    # Store topics that match our patterns
    if "myuplink" in topic.lower():
        DISCOVERED_TOPICS["all"].append(topic)
        print(f"  Found topic: {topic}")


def on_subscribe(client, userdata, mid, reason_code_list, properties):
    """Handle subscription complete event."""
    _ = (client, userdata, mid, reason_code_list, properties)  # Unused
    print("Subscription complete, scanning for topics...")


def on_connect(client, userdata, connect_flags, reason_code, properties):
    """Handle MQTT client connection event."""
    _ = (client, userdata, connect_flags, properties)  # Unused but required by callback signature
    print(f"Connected to MQTT broker with return code {reason_code}")


def setup_mqtt_client():
    """Set up and connect MQTT client.

    Returns:
        mqtt.Client: Connected MQTT client instance.

    """
    client = mqtt.Client(CallbackAPIVersion.VERSION2, MQTT_CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_subscribe = on_subscribe

    # Set username/password if provided
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)
    client.loop_start()
    return client


def scan_for_existing_topics(mqtt_client):
    """Scan MQTT broker for existing myUplink-related topics.

    Args:
        mqtt_client: MQTT client instance.

    Returns:
        list: List of discovered topic paths.

    """
    print("Scanning for existing myUplink topics...")

    # Subscribe to all discovery topics and data topics
    # Use proper MQTT wildcards: + for single level, # for multi-level
    mqtt_client.subscribe(f"{HA_DISCOVERY_PREFIX}/+/+/config")
    mqtt_client.subscribe(f"{MQTT_BASE_TOPIC}/#")

    # Wait for messages to arrive
    print("Waiting 3 seconds for topic discovery...")
    time.sleep(3)

    topics = list(set(DISCOVERED_TOPICS["all"]))  # Remove duplicates
    print(f"Found {len(topics)} existing topics")
    return topics


def clear_device_discovery(mqtt_client, myuplink, system_id, device_id):
    """Clear all MQTT topics for a single device.

    This clears:
    - Home Assistant discovery configurations (both sensor and binary_sensor)
    - Data value topics (myuplink/{system_id}/{parameter_id}/value)

    Args:
        mqtt_client: MQTT client instance.
        myuplink: OAuth2 session for myUplink API.
        system_id: System ID the device belongs to.
        device_id: Device ID to clear topics for.

    Returns:
        int: Number of topics cleared.

    """
    response = myuplink.get(f"https://api.myuplink.com/v2/devices/{device_id}/points")
    if response.status_code != HTTP_STATUS_OK:
        print(f"Warning: Could not get points for device {device_id}")
        return 0

    cleared = 0
    for data_point in response.json():
        parameter_id = data_point["parameterId"]

        # Clear discovery configs for BOTH sensor and binary_sensor platforms
        # (in case the parameter type changed)
        for platform in ["sensor", "binary_sensor"]:
            unique_id = f"myuplink_{device_id}_{parameter_id}"
            discovery_topic = f"{HA_DISCOVERY_PREFIX}/{platform}/{unique_id}/config"

            if mqtt_client.publish(discovery_topic, "", retain=True).rc == 0:
                cleared += 1
                print(f"  Cleared discovery: {discovery_topic}")

        # Clear data value topic
        value_topic = f"{MQTT_BASE_TOPIC}/{system_id}/{parameter_id}/value"

        if mqtt_client.publish(value_topic, "", retain=True).rc == 0:
            cleared += 1
            print(f"  Cleared value: {value_topic}")

        time.sleep(0.01)

    return cleared


def main():
    """Clear all MQTT discovery configurations."""
    # Check prerequisites
    can_proceed, error_message = check_oauth_prerequisites()
    if not can_proceed:
        print(f"Error: {error_message}")
        sys.exit(1)

    # Setup connections
    mqtt_client = setup_mqtt_client()
    myuplink = create_oauth_session()

    # First, scan for ALL existing topics
    existing_topics = scan_for_existing_topics(mqtt_client)

    # Get systems and devices
    response = myuplink.get("https://api.myuplink.com/v2/systems/me")
    if response.status_code != HTTP_STATUS_OK:
        print(f"HTTP Status: {response.status_code}")
        print(response.text)
        raise SystemExit("API call not successful")

    print("\nClearing all myUplink MQTT topics...")
    total_cleared = 0

    # Clear all discovered existing topics first
    print(f"\nClearing {len(existing_topics)} discovered topics...")
    for topic in existing_topics:
        if mqtt_client.publish(topic, "", retain=True).rc == 0:
            total_cleared += 1
            print(f"  Cleared: {topic}")
        time.sleep(0.01)

    # Then clear topics for current devices/parameters
    print("\nClearing current device topics...")
    for system in response.json()["systems"]:
        system_id = system["systemId"]
        print(f"Processing system: {system_id}")

        for device in system["devices"]:
            device_id = device["id"]
            print(f"  Processing device: {device_id}")
            total_cleared += clear_device_discovery(mqtt_client, myuplink, system_id, device_id)

        # Clear system availability topic
        availability_topic = f"{MQTT_BASE_TOPIC}/{system_id}/available"
        mqtt_client.publish(availability_topic, "", retain=True)
        print(f"  Cleared availability: {availability_topic}")
        total_cleared += 1

    # Cleanup
    time.sleep(1)
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

    print(f"\nDone! Cleared {total_cleared} MQTT topics.")
    print("Now run myUplink2mqtt.py to recreate them with the new settings.")


if __name__ == "__main__":
    main()
