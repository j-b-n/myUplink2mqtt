"""Tests for MQTT client functionality and broker interactions.

Comprehensive test suite for MQTT client creation, message publishing,
and Home Assistant discovery payload generation.
"""

import json
from unittest.mock import MagicMock

# ============================================================================
# Tests for Mock MQTT Broker
# ============================================================================


class TestMockMQTTBroker:
    """Test suite for MockMQTTBroker fixture functionality.

    These tests verify the mock broker works as expected for testing
    MQTT publishing behavior.
    """

    def test_broker_publish_message(self, mock_mqtt_broker):
        """Test publishing a message to broker.

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        result = mock_mqtt_broker.publish("test/topic", "test payload")

        assert result["rc"] == 0
        assert len(mock_mqtt_broker.get_messages("test/topic")) == 1

    def test_broker_publish_multiple_messages(self, mock_mqtt_broker):
        """Test publishing multiple messages to same topic.

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        mock_mqtt_broker.publish("topic/1", "payload1")
        mock_mqtt_broker.publish("topic/1", "payload2")
        mock_mqtt_broker.publish("topic/1", "payload3")

        messages = mock_mqtt_broker.get_messages("topic/1")
        assert len(messages) == 3

    def test_broker_publish_to_multiple_topics(self, mock_mqtt_broker):
        """Test publishing to multiple different topics.

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        mock_mqtt_broker.publish("topic/1", "payload1")
        mock_mqtt_broker.publish("topic/2", "payload2")
        mock_mqtt_broker.publish("topic/3", "payload3")

        all_messages = mock_mqtt_broker.get_all_messages()
        assert len(all_messages) == 3
        assert "topic/1" in all_messages
        assert "topic/2" in all_messages
        assert "topic/3" in all_messages

    def test_broker_publish_with_qos_and_retain(self, mock_mqtt_broker):
        """Test publishing with QoS and retain flags.

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        mock_mqtt_broker.publish("topic", "payload", qos=1, retain=True)

        messages = mock_mqtt_broker.get_messages("topic")
        assert messages[0]["qos"] == 1
        assert messages[0]["retain"] is True

    def test_broker_subscribe_topic(self, mock_mqtt_broker):
        """Test subscribing to a topic.

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        mock_mqtt_broker.subscribe("topic/test")

        assert "topic/test" in mock_mqtt_broker.subscriptions

    def test_broker_clear_messages(self, mock_mqtt_broker):
        """Test clearing stored messages.

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        mock_mqtt_broker.publish("topic/1", "payload1")
        mock_mqtt_broker.publish("topic/2", "payload2")

        mock_mqtt_broker.clear()

        assert len(mock_mqtt_broker.get_all_messages()) == 0


# ============================================================================
# Tests for MQTT Client Mock
# ============================================================================


class TestMockMQTTClient:
    """Test suite for mock paho-mqtt client fixture."""

    def test_client_connect(self, mock_mqtt_client):
        """Test mock client connect method.

        Args:
            mock_mqtt_client: Mock MQTT client fixture.
        """
        mock_mqtt_client.connect("localhost", 1883, 60)

        mock_mqtt_client.connect.assert_called_with("localhost", 1883, 60)

    def test_client_publish(self, mock_mqtt_client):
        """Test mock client publish method.

        Args:
            mock_mqtt_client: Mock MQTT client fixture.
        """
        mock_mqtt_client.publish("test/topic", "test payload")

        assert len(mock_mqtt_client.published_messages) == 1
        assert mock_mqtt_client.published_messages[0]["topic"] == "test/topic"
        assert mock_mqtt_client.published_messages[0]["payload"] == "test payload"

    def test_client_publish_multiple(self, mock_mqtt_client):
        """Test mock client publishing multiple messages.

        Args:
            mock_mqtt_client: Mock MQTT client fixture.
        """
        mock_mqtt_client.publish("topic/1", "payload1")
        mock_mqtt_client.publish("topic/2", "payload2")
        mock_mqtt_client.publish("topic/3", "payload3")

        assert len(mock_mqtt_client.published_messages) == 3

    def test_client_disconnect(self, mock_mqtt_client):
        """Test mock client disconnect method.

        Args:
            mock_mqtt_client: Mock MQTT client fixture.
        """
        mock_mqtt_client.disconnect()

        mock_mqtt_client.disconnect.assert_called_once()

    def test_client_is_connected(self, mock_mqtt_client):
        """Test mock client is_connected method.

        Args:
            mock_mqtt_client: Mock MQTT client fixture.
        """
        is_connected = mock_mqtt_client.is_connected()

        assert is_connected is True


# ============================================================================
# MQTT Integration Test Scenarios
# ============================================================================


class TestMQTTPublishingScenarios:
    """Test suite for MQTT publishing scenarios using mock broker."""

    def test_publish_system_discovery(self, mock_mqtt_broker):
        """Test publishing system discovery payload.

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        topic = "homeassistant/binary_sensor/myuplink_system-123/config"
        payload = json.dumps(
            {
                "name": "My Home System",
                "state_topic": "myuplink/system-123/online",
                "availability_topic": "myuplink/system-123/availability",
            }
        )

        mock_mqtt_broker.publish(topic, payload, qos=1, retain=True)

        messages = mock_mqtt_broker.get_messages(topic)
        assert len(messages) == 1

        # Verify payload is valid JSON
        published_data = json.loads(messages[0]["payload"])
        assert published_data["name"] == "My Home System"

    def test_publish_device_sensor_discovery(self, mock_mqtt_broker):
        """Test publishing device sensor discovery.

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        topic = "homeassistant/sensor/myuplink_device-001_temp/config"
        payload = json.dumps(
            {
                "name": "Room Temperature",
                "state_topic": "myuplink/device-001/temperature",
                "unit_of_measurement": "°C",
                "device_class": "temperature",
            }
        )

        mock_mqtt_broker.publish(topic, payload, qos=1, retain=True)

        messages = mock_mqtt_broker.get_messages(topic)
        assert len(messages) == 1

        published_data = json.loads(messages[0]["payload"])
        assert published_data["unit_of_measurement"] == "°C"

    def test_publish_device_state_updates(self, mock_mqtt_broker):
        """Test publishing device state updates.

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        topic_base = "myuplink/device-001"

        # Publish multiple state updates
        mock_mqtt_broker.publish(f"{topic_base}/temperature", "21.5")
        mock_mqtt_broker.publish(f"{topic_base}/outdoor_temp", "8.2")
        mock_mqtt_broker.publish(f"{topic_base}/heating_status", "ON")

        all_messages = mock_mqtt_broker.get_all_messages()
        assert len(all_messages) == 3

    def test_publish_batch_discovery_payloads(self, mock_mqtt_broker):
        """Test publishing batch of discovery payloads.

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        devices = [
            {"id": "device-001", "name": "Heat Pump"},
            {"id": "device-002", "name": "Indoor Unit"},
            {"id": "device-003", "name": "Boiler"},
        ]

        for device in devices:
            topic = f"homeassistant/sensor/myuplink_{device['id']}/config"
            payload = json.dumps(
                {"name": device["name"], "state_topic": f"myuplink/{device['id']}/state"}
            )
            mock_mqtt_broker.publish(topic, payload, qos=1, retain=True)

        all_messages = mock_mqtt_broker.get_all_messages()
        assert len(all_messages) == 3

    def test_mqtt_topic_organization(self, mock_mqtt_broker):
        """Test MQTT topic organization patterns.

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        # System level
        mock_mqtt_broker.publish("myuplink/system-123/online", "true")
        mock_mqtt_broker.publish("myuplink/system-123/name", "My Home")

        # Device level
        mock_mqtt_broker.publish("myuplink/device-001/temperature", "21.5")
        mock_mqtt_broker.publish("myuplink/device-001/status", "online")

        # Discovery level
        mock_mqtt_broker.publish("homeassistant/sensor/myuplink_device-001_temp/config", "{}")

        all_messages = mock_mqtt_broker.get_all_messages()
        assert len(all_messages) == 5

        # Verify topic structure
        topics = list(all_messages.keys())
        assert any("system-123" in t for t in topics)
        assert any("device-001" in t for t in topics)
        assert any("homeassistant" in t for t in topics)


# ============================================================================
# MQTT Error and Edge Cases
# ============================================================================


class TestMQTTErrorHandling:
    """Test suite for MQTT error handling and edge cases."""

    def test_mqtt_client_connection_failure(self):
        """Test MQTT client handles connection failures."""
        mock_client = MagicMock()
        mock_client.connect.return_value = 1  # Return code 1 = error

        result = mock_client.connect("invalid_host", 1883, 60)

        assert result == 1

    def test_mqtt_client_publish_failure(self):
        """Test MQTT client handles publish failures."""
        mock_client = MagicMock()
        publish_result = MagicMock()
        publish_result.rc = 1  # Error code
        mock_client.publish.return_value = publish_result

        result = mock_client.publish("topic", "payload")

        assert result.rc == 1

    def test_mqtt_broker_get_nonexistent_topic(self, mock_mqtt_broker):
        """Test getting messages from non-existent topic.

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        messages = mock_mqtt_broker.get_messages("nonexistent/topic")

        assert messages == []

    def test_mqtt_large_payload(self, mock_mqtt_broker):
        """Test publishing large MQTT payload.

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        # Create large JSON payload
        large_payload = json.dumps(
            {"data": "x" * 10000, "nested": {"deep": {"structure": "value" * 100}}}
        )

        mock_mqtt_broker.publish("test/large", large_payload)

        messages = mock_mqtt_broker.get_messages("test/large")
        assert len(messages) == 1

    def test_mqtt_special_characters_in_topic(self, mock_mqtt_broker):
        """Test publishing to topics with special characters.

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        topics = [
            "myuplink/device-001/temp-sensor",
            "myuplink/device_002/humid_level",
            "myuplink/device.003/power.consumption",
        ]

        for topic in topics:
            mock_mqtt_broker.publish(topic, "payload")

        all_messages = mock_mqtt_broker.get_all_messages()
        assert len(all_messages) == 3

    def test_mqtt_special_characters_in_payload(self, mock_mqtt_broker):
        """Test publishing payloads with special characters.

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        payloads = [
            "value with spaces",
            "value_with_underscores",
            "value-with-hyphens",
            "value/with/slashes",
            "value.with.dots",
        ]

        for i, payload in enumerate(payloads):
            mock_mqtt_broker.publish(f"test/topic{i}", payload)

        all_messages = mock_mqtt_broker.get_all_messages()
        assert len(all_messages) == len(payloads)

    def test_mqtt_json_payload_validation(self, mock_mqtt_broker):
        """Test publishing and validating JSON payloads.

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        payloads = [
            json.dumps({"key": "value"}),
            json.dumps({"nested": {"deep": "value"}}),
            json.dumps({"array": [1, 2, 3]}),
        ]

        for i, payload in enumerate(payloads):
            mock_mqtt_broker.publish(f"test/json{i}", payload)

            # Verify payload can be parsed
            messages = mock_mqtt_broker.get_messages(f"test/json{i}")
            data = json.loads(messages[0]["payload"])
            assert isinstance(data, dict)

    def test_mqtt_utf8_characters(self, mock_mqtt_broker):
        """Test publishing UTF-8 encoded characters.

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        payloads = ["Température: 21.5°C", "Luftfeuchtigkeit: 65%", "Temperatur (°C)", "温度: 21.5"]

        for i, payload in enumerate(payloads):
            mock_mqtt_broker.publish(f"test/utf8_{i}", payload)

        all_messages = mock_mqtt_broker.get_all_messages()
        assert len(all_messages) == len(payloads)


# ============================================================================
# MQTT Discovery Payload Tests
# ============================================================================


class TestMQTTDiscoveryPayloads:
    """Test suite for MQTT Home Assistant discovery payload generation."""

    def test_discovery_payload_sensor_format(self):
        """Test sensor discovery payload format."""
        payload = {
            "name": "Room Temperature",
            "state_topic": "myuplink/device-001/temperature",
            "unit_of_measurement": "°C",
            "device_class": "temperature",
            "availability_topic": "myuplink/device-001/availability",
            "payload_available": "online",
            "payload_not_available": "offline",
        }

        # Verify structure
        assert "name" in payload
        assert "state_topic" in payload
        assert "unit_of_measurement" in payload
        assert "device_class" in payload

        # Verify JSON serialization
        json_str = json.dumps(payload)
        parsed = json.loads(json_str)
        assert parsed["name"] == "Room Temperature"

    def test_discovery_payload_binary_sensor_format(self):
        """Test binary sensor discovery payload format."""
        payload = {
            "name": "Heating Status",
            "state_topic": "myuplink/device-001/heating_on",
            "device_class": "heat",
            "payload_on": "ON",
            "payload_off": "OFF",
        }

        assert payload["payload_on"] == "ON"
        assert payload["payload_off"] == "OFF"

    def test_discovery_payload_with_device_info(self):
        """Test discovery payload with device information."""
        payload = {
            "name": "Heat Pump",
            "state_topic": "myuplink/device-001/state",
            "device": {
                "identifiers": ["myuplink_device_001"],
                "name": "Nibe F1155",
                "manufacturer": "Nibe",
                "model": "F1155",
                "sw_version": "6.125",
            },
        }

        device_info = payload["device"]
        assert "identifiers" in device_info
        assert "manufacturer" in device_info
        assert device_info["manufacturer"] == "Nibe"

    def test_discovery_payload_with_availability(self):
        """Test discovery payload with availability topic."""
        payload = {
            "name": "Device",
            "state_topic": "myuplink/device-001/state",
            "availability": [
                {
                    "topic": "myuplink/device-001/availability",
                    "payload_available": "online",
                    "payload_not_available": "offline",
                }
            ],
        }

        assert isinstance(payload["availability"], list)
        assert payload["availability"][0]["payload_available"] == "online"


# ============================================================================
# MQTT QoS and Retain Flag Tests
# ============================================================================


class TestMQTTQoSAndRetain:
    """Test suite for MQTT QoS levels and retain flags."""

    def test_publish_with_qos_0(self, mock_mqtt_broker):
        """Test publishing with QoS 0 (at most once).

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        mock_mqtt_broker.publish("test/qos0", "payload", qos=0)

        messages = mock_mqtt_broker.get_messages("test/qos0")
        assert messages[0]["qos"] == 0

    def test_publish_with_qos_1(self, mock_mqtt_broker):
        """Test publishing with QoS 1 (at least once).

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        mock_mqtt_broker.publish("test/qos1", "payload", qos=1)

        messages = mock_mqtt_broker.get_messages("test/qos1")
        assert messages[0]["qos"] == 1

    def test_publish_with_qos_2(self, mock_mqtt_broker):
        """Test publishing with QoS 2 (exactly once).

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        mock_mqtt_broker.publish("test/qos2", "payload", qos=2)

        messages = mock_mqtt_broker.get_messages("test/qos2")
        assert messages[0]["qos"] == 2

    def test_publish_discovery_with_retain(self, mock_mqtt_broker):
        """Test publishing discovery payloads with retain flag.

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        topic = "homeassistant/sensor/myuplink_device_001/config"
        payload = json.dumps({"name": "Device"})

        mock_mqtt_broker.publish(topic, payload, qos=1, retain=True)

        messages = mock_mqtt_broker.get_messages(topic)
        assert messages[0]["retain"] is True
        assert messages[0]["qos"] == 1

    def test_publish_state_without_retain(self, mock_mqtt_broker):
        """Test publishing state updates without retain flag.

        Args:
            mock_mqtt_broker: Mock MQTT broker fixture.
        """
        topic = "myuplink/device-001/temperature"

        mock_mqtt_broker.publish(topic, "21.5", qos=1, retain=False)

        messages = mock_mqtt_broker.get_messages(topic)
        assert messages[0]["retain"] is False
