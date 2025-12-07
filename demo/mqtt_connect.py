"""Test MQTT connectivity to the broker.

This test verifies that we can connect to the MQTT broker at 10.0.0.2:1883.
Supports optional authentication via MQTT_USERNAME and MQTT_PASSWORD environment variables.
"""

import asyncio
import logging
import os
import time

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

# Logger initialization
logger = logging.getLogger(__name__)


def test_mqtt_connectivity():
    """Test connection to MQTT broker.

    Returns:
        bool: True if connection successful, False otherwise.
    """
    broker_host = "10.0.0.2"
    broker_port = 1883

    # Get authentication credentials from environment variables
    username = os.getenv("MQTT_USERNAME")
    password = os.getenv("MQTT_PASSWORD")

    connected = False
    disconnected = False

    def on_connect(client, userdata, flags, reason_code, properties):  # pylint: disable=unused-argument
        nonlocal connected
        if reason_code.value == 0:
            connected = True
            auth_msg = " (authenticated)" if username else ""
            msg = f"Connected to MQTT broker at {broker_host}:{broker_port}{auth_msg}"
            logger.info(msg)
        else:
            err_msg = f"Failed MQTT connect to {broker_host}:{broker_port}, rc: {reason_code.value}"
            logger.error(err_msg)

    def on_disconnect(client, userdata, flags, reason_code, properties):  # pylint: disable=unused-argument
        nonlocal disconnected
        disconnected = True

    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)

    # Set username and password if provided
    if username:
        client.username_pw_set(username, password)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    try:
        client.connect(broker_host, broker_port, 60)
        client.loop_start()
        # Wait a bit for connection
        time.sleep(2)
        client.loop_stop()
        client.disconnect()
        return connected
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"Failed to connect to MQTT broker at {broker_host}:{broker_port}: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("Testing MQTT connectivity...")
    # Run the synchronous test in a thread
    loop = asyncio.get_event_loop()
    success = await loop.run_in_executor(None, test_mqtt_connectivity)
    if success:
        logger.info("MQTT test passed.")
    else:
        logger.error("MQTT test failed.")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    asyncio.run(main())
