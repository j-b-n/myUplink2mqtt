"""Pytest configuration and fixtures for myUplink2mqtt tests.

This module provides mock data and fixtures for testing myUplink utilities
with realistic API responses and MQTT server behavior.
"""

import json
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ============================================================================
# Mock myUplink API Response Data
# ============================================================================


@pytest.fixture
def mock_oauth_token():
    """Return mock OAuth token data.

    Returns:
        dict: Mock OAuth token matching myUplink API format.
    """
    return {
        "access_token": "mock_access_token_12345",
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": "mock_refresh_token_12345",
        "scope": "READSYSTEM",
        "expires_at": 1234567890.0,
    }


@pytest.fixture
def mock_config():
    """Return mock OAuth configuration.

    Returns:
        dict: Mock client credentials.
    """
    return {"client_id": "test_client_id_12345", "client_secret": "test_client_secret_abcde"}


@pytest.fixture
def temp_config_files(tmp_path, mock_oauth_token, mock_config):
    """Create temporary config and token files for testing.

    Args:
        tmp_path: pytest's temporary directory fixture.
        mock_oauth_token: Mock token data fixture.
        mock_config: Mock config data fixture.

    Yields:
        tuple: (config_file_path, token_file_path)
    """
    config_file = tmp_path / "config.json"
    token_file = tmp_path / "token.json"

    config_file.write_text(json.dumps(mock_config))
    token_file.write_text(json.dumps(mock_oauth_token))

    yield str(config_file), str(token_file)


@pytest.fixture
def mock_systems_response():
    """Return mock response for /v2/systems/me API endpoint.

    Returns:
        list: Mock systems data with devices.
    """
    return [
        {
            "systemId": "system-123",
            "name": "My Home System",
            "devices": [
                {
                    "id": "device-001",
                    "deviceType": "HEAT_PUMP",
                    "connectionStatus": "ONLINE",
                    "activationDate": "2023-01-15",
                },
                {
                    "id": "device-002",
                    "deviceType": "INDOOR_UNIT",
                    "connectionStatus": "ONLINE",
                    "activationDate": "2023-01-15",
                },
            ],
        },
        {
            "systemId": "system-456",
            "name": "Cabin System",
            "devices": [
                {
                    "id": "device-003",
                    "deviceType": "HEAT_PUMP",
                    "connectionStatus": "OFFLINE",
                    "activationDate": "2023-06-01",
                }
            ],
        },
    ]


@pytest.fixture
def mock_device_details_nibe():
    """Return mock device details for a Nibe heat pump.

    Returns:
        dict: Mock device details response.
    """
    return {
        "id": "device-001",
        "product": {"name": "Nibe F1155", "brand": "Nibe", "productSeries": "F-series"},
        "connectionStatus": "ONLINE",
        "lastStatusUpdateTime": "2025-10-19T14:30:00Z",
        "firmwareVersion": "6.125",
        "serialNumber": "ABC123456",
    }


@pytest.fixture
def mock_device_details_ivt():
    """Return mock device details for an IVT heat pump.

    Returns:
        dict: Mock device details response.
    """
    return {
        "id": "device-002",
        "product": {"name": "IVT GEO 6", "brand": "IVT", "productSeries": "GEO-series"},
        "connectionStatus": "ONLINE",
        "lastStatusUpdateTime": "2025-10-19T14:30:00Z",
        "firmwareVersion": "5.50",
        "serialNumber": "XYZ789012",
    }


@pytest.fixture
def mock_device_points_response():
    """Return mock response for /v2/devices/{id}/points API endpoint.

    Returns:
        dict: Mock device points data.
    """
    return {
        "points": [
            {
                "parameterId": 40004,
                "parameterName": "Actual room temperature",
                "parameterUnit": "°C",
                "value": 21.5,
                "timestamp": "2025-10-19T14:30:00Z",
            },
            {
                "parameterId": 40012,
                "parameterName": "BT21 Outdoor temperature",
                "parameterUnit": "°C",
                "value": 8.2,
                "timestamp": "2025-10-19T14:30:00Z",
            },
            {
                "parameterId": 40940,
                "parameterName": "Hot water storage",
                "parameterUnit": "°C",
                "value": 52.3,
                "timestamp": "2025-10-19T14:30:00Z",
            },
            {
                "parameterId": 43009,
                "parameterName": "Heating status",
                "parameterUnit": "",
                "value": "ON",
                "timestamp": "2025-10-19T14:30:00Z",
            },
            {
                "parameterId": 60720,
                "parameterName": "Text not found: id[60720], fw[noem-h], lang[en-US]",
                "parameterUnit": "",
                "value": 2023,
                "timestamp": "2025-10-19T14:30:00Z",
            },
        ]
    }


@pytest.fixture
def mock_device_points_with_label_cleanup():
    """Return mock device points with label cleanup scenarios.

    Returns:
        dict: Mock device points with special characters and formatting.
    """
    return {
        "points": [
            {
                "parameterId": 40001,
                "parameterName": "SAK (SAK Operating mode)",
                "parameterUnit": "",
                "value": "Manual",
                "timestamp": "2025-10-19T14:30:00Z",
            },
            {
                "parameterId": 40002,
                "parameterName": "Hot water (Ratio hot water defrost)",
                "parameterUnit": "",
                "value": 0.5,
                "timestamp": "2025-10-19T14:30:00Z",
            },
            {
                "parameterId": 40003,
                "parameterName": "Temperature\u00ad sensor",
                "parameterUnit": "°C",
                "value": 20.5,
                "timestamp": "2025-10-19T14:30:00Z",
            },
        ]
    }


@pytest.fixture
def mock_api(
    mock_systems_response,
    mock_device_details_nibe,
    mock_device_details_ivt,
    mock_device_points_response,
):
    """Return an AsyncMock MyUplinkAPI client with realistic side effects."""

    api = AsyncMock()
    api.async_get_systems.return_value = [
        SimpleNamespace(raw=system) for system in mock_systems_response
    ]

    async def get_device_json(device_id):
        if device_id == "device-001":
            return mock_device_details_nibe
        if device_id == "device-002":
            return mock_device_details_ivt
        raise KeyError("Device not found")

    async def get_device_points(device_id, language="en-US", points=None):
        _ = language
        _ = points
        if device_id in {"device-001", "device-002"}:
            return mock_device_points_response["points"]
        raise KeyError("Device not found")

    api.async_get_device_json.side_effect = get_device_json
    api.async_get_device_points_json.side_effect = get_device_points

    return api


@pytest.fixture
def mock_api_with_errors():
    """Return an AsyncMock MyUplinkAPI client that raises errors."""

    api = AsyncMock()
    api.async_get_systems.side_effect = ValueError("Invalid token")
    api.async_get_device_json.side_effect = ValueError("Device error")
    api.async_get_device_points_json.side_effect = ValueError("Points error")
    return api


# ============================================================================
# Mock MQTT Broker/Client
# ============================================================================


@pytest.fixture
def mock_mqtt_client():
    """Return a mock paho-mqtt client.

    Returns:
        Mock: Mock MQTT client with connect, publish, and disconnect methods.
    """
    mock_client = MagicMock()
    mock_client.connect.return_value = 0
    mock_client.publish.return_value = MagicMock(rc=0)
    mock_client.disconnect.return_value = 0
    mock_client.is_connected.return_value = True

    # Track published messages for assertions
    mock_client.published_messages = []

    def track_publish(topic, payload, *args, **kwargs):
        """Track published messages."""
        mock_client.published_messages.append({"topic": topic, "payload": payload})
        return MagicMock(rc=0)

    mock_client.publish.side_effect = track_publish
    return mock_client


class MockMQTTBroker:
    """Simple in-memory MQTT broker for testing.

    This broker tracks published messages and can be queried for testing
    without needing an actual MQTT server.
    """

    def __init__(self):
        """Initialize the mock broker with empty message store."""
        self.messages = {}
        self.connections = []
        self.subscriptions = {}

    def publish(self, topic, payload, qos=0, retain=False):
        """Simulate publishing a message.

        Args:
            topic (str): MQTT topic.
            payload (str): Message payload.
            qos (int): Quality of Service level.
            retain (bool): Retain flag.

        Returns:
            dict: Result with 'rc' (return code) as 0 for success.
        """
        if topic not in self.messages:
            self.messages[topic] = []

        self.messages[topic].append(
            {"payload": payload, "qos": qos, "retain": retain, "timestamp": None}
        )
        return {"rc": 0}

    def subscribe(self, topic):
        """Simulate subscribing to a topic.

        Args:
            topic (str): MQTT topic or topic filter.
        """
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        self.subscriptions[topic].append({})

    def get_messages(self, topic):
        """Get all messages published to a topic.

        Args:
            topic (str): MQTT topic.

        Returns:
            list: List of message dictionaries for the topic.
        """
        return self.messages.get(topic, [])

    def get_all_messages(self):
        """Get all published messages.

        Returns:
            dict: Dictionary mapping topics to lists of messages.
        """
        return self.messages

    def clear(self):
        """Clear all stored messages."""
        self.messages = {}
        self.subscriptions = {}


@pytest.fixture
def mock_mqtt_broker():
    """Return a MockMQTTBroker instance.

    Returns:
        MockMQTTBroker: In-memory MQTT broker for testing.
    """
    return MockMQTTBroker()


# ============================================================================
# Patching Fixtures for Utilities
# ============================================================================


@pytest.fixture
def patch_config_paths(tmp_path, mock_oauth_token, mock_config):
    """Patch configuration file paths to use temporary files.

    Args:
        tmp_path: pytest's temporary directory fixture.
        mock_oauth_token: Mock token data fixture.
        mock_config: Mock config data fixture.

    Yields:
        tuple: (config_path, token_path) for reference in tests.
    """
    config_file = tmp_path / "config.json"
    token_file = tmp_path / "token.json"

    config_file.write_text(json.dumps(mock_config))
    token_file.write_text(json.dumps(mock_oauth_token))

    config_path = str(config_file)
    token_path = str(token_file)

    # Patch the module-level paths
    with patch("myuplink2mqtt.utils.myuplink_utils.CONFIG_FILENAME", config_path), patch(
        "myuplink2mqtt.utils.myuplink_utils.TOKEN_FILENAME", token_path
    ):
        yield config_path, token_path


@pytest.fixture
def patch_env_credentials():
    """Patch environment variables with test credentials.

    Yields:
        dict: Environment variable patch context.
    """
    env_vars = {
        "MYUPLINK_CLIENT_ID": "test_client_id_env",
        "MYUPLINK_CLIENT_SECRET": "test_client_secret_env",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


# ============================================================================
# Async Test Support
# ============================================================================


@pytest.fixture
def event_loop():
    """Create an event loop for async tests.

    Yields:
        asyncio.AbstractEventLoop: Event loop for async test execution.
    """
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()
