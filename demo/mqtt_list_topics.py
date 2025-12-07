"""Helper script to list all available MQTT topics from myUplink2mqtt.

This script connects to the MQTT broker and displays all topics being published,
useful for finding the unique_id of a specific parameter.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Logger initialization
logger = logging.getLogger(__name__)

# Track discovered topics
discovered_topics = {}
topic_count = {"current": 0}


def increment_topic_count():
    """Increment topic count.

    Returns:
        int: Updated count.
    """
    topic_count["current"] += 1
    return topic_count["current"]


def process_discovery_message(msg):
    """Process a discovery configuration message.

    Args:
        msg: MQTT message object.
    """
    try:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)

        unique_id = data.get("unique_id", "Unknown")
        name = data.get("name", "Unknown")
        entity_category = data.get("entity_category", "standard")

        if unique_id not in discovered_topics:
            discovered_topics[unique_id] = {
                "name": name,
                "category": entity_category,
                "topic": msg.topic,
            }
            count = increment_topic_count()
            logger.info("[%d] %s (unique_id: %s)", count, name, unique_id)
    except json.JSONDecodeError:
        pass


class MQTTTopicCollector:
    """Collects MQTT topics from broker."""

    def __init__(self, config):
        """Initialize collector.

        Args:
            config (dict): Configuration dictionary with keys:
                - broker_host, broker_port, username,
                - discovery_prefix, base_topic
        """
        self.broker_host = config["broker_host"]
        self.broker_port = config["broker_port"]
        self.username = config["username"]
        self.discovery_prefix = config["discovery_prefix"]
        self.base_topic = config["base_topic"]

    def on_connect(self, _client, _userdata, _flags, reason_code, _properties):
        """Handle MQTT connection.

        Args:
            _client: MQTT client (unused).
            _userdata: User data (unused).
            _flags: Connection flags (unused).
            reason_code: Connection result code.
            _properties: Connection properties (unused).
        """
        if reason_code.value == 0:
            auth_msg = " (authenticated)" if self.username else ""
            logger.info(
                "Connected to MQTT broker at %s:%d%s", self.broker_host, self.broker_port, auth_msg
            )
            logger.info("Subscribing to all myUplink topics...")
        else:
            logger.error("Failed MQTT connect, rc: %d", reason_code.value)

    def on_message(self, _client, _userdata, msg):
        """Handle incoming MQTT messages.

        Args:
            _client: MQTT client (unused).
            _userdata: User data (unused).
            msg: MQTT message.
        """
        if "config" in msg.topic:
            process_discovery_message(msg)


def configure_mqtt_client(client, collector):
    """Configure MQTT client with callbacks.

    Args:
        client: MQTT client instance.
        collector: MQTTTopicCollector instance.
    """
    client.on_connect = collector.on_connect
    client.on_message = collector.on_message


def list_mqtt_topics(duration=10):
    """Collect and display all MQTT topics for a specified duration.

    Args:
        duration (int): How long to listen for topics in seconds.

    Returns:
        dict: Dictionary of discovered topics.
    """
    broker_host = "10.0.0.2"
    broker_port = 1883

    username = os.getenv("MQTT_USERNAME")
    password = os.getenv("MQTT_PASSWORD")

    discovery_prefix = os.getenv("HA_DISCOVERY_PREFIX", "homeassistant")
    base_topic = os.getenv("MQTT_BASE_TOPIC", "myuplink")

    start_time = time.time()

    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)

    if username:
        client.username_pw_set(username, password)

    config = {
        "broker_host": broker_host,
        "broker_port": broker_port,
        "username": username,
        "discovery_prefix": discovery_prefix,
        "base_topic": base_topic,
    }
    collector = MQTTTopicCollector(config)
    configure_mqtt_client(client, collector)

    try:
        logger.info("Listening for MQTT topics for %d seconds...", duration)
        client.connect(broker_host, broker_port, 60)
        client.loop_start()

        # Subscribe to topics
        client.subscribe(f"{discovery_prefix}/#", qos=1)
        client.subscribe(f"{base_topic}/#", qos=1)

        while time.time() - start_time < duration:
            time.sleep(0.1)

        client.loop_stop()
        client.disconnect()

    except (OSError, ValueError, KeyError) as e:
        logger.error("Error: %s", e)

    return discovered_topics


def main():
    """Main function."""
    logger.info("=" * 70)
    logger.info("MQTT Topics Discovery")
    logger.info("=" * 70)
    logger.info("")

    topics = list_mqtt_topics(duration=10)

    if not topics:
        logger.error("No topics found. Make sure myUplink2mqtt is running!")
        return

    separator = "=" * 70
    logger.info("")
    logger.info("%s", separator)
    logger.info("Found %d parameter(s)", len(topics))
    logger.info("%s", separator)
    logger.info("")

    logger.info("To retrieve discovery and state for a specific parameter, run:")
    logger.info("  python tests/test_mqtt_discovery.py <unique_id>")
    logger.info("")

    if topics:
        first_unique_id = next(iter(topics.keys()))
        logger.info("Example:")
        logger.info("  python tests/test_mqtt_discovery.py %s", first_unique_id)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    main()
