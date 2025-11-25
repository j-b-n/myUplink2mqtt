"""Domoticz JSON API utilities for device management and validation.

This module provides utilities for interacting with Domoticz via its JSON API.
It includes functions for:
- Authenticating to Domoticz
- Retrieving device lists
- Validating discovered devices
- Getting device details
- Updating device status

Reference: https://wiki.domoticz.com/Domoticz_API/JSON_URL%27s
"""

import json
import logging
from typing import Any, Dict, List, Optional

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

# HTTP status code for successful requests
HTTP_STATUS_OK = 200
HTTP_STATUS_CREATED = 201
HTTP_STATUS_NO_CONTENT = 204

# Domoticz JSON API endpoints
DOMOTICZ_API_STATUS = "/json.htm?type=command&param=getStatus"
DOMOTICZ_API_SERVER_TIME = "/json.htm?type=command&param=getServerTime"
DOMOTICZ_API_VERSION = "/json.htm?type=command&param=getversion"
DOMOTICZ_API_DEVICES = "/json.htm?type=command&param=getdevices&filter=all&used=true"
DOMOTICZ_API_DEVICE = "/json.htm?type=command&param=getdevices&idx={rid}"
DOMOTICZ_API_DEVICES_HIDDEN = "/json.htm?type=command&param=getdevices&used=true&displayhidden=1"
DOMOTICZ_API_DEVICES_FAVORITES = (
    "/json.htm?type=command&param=getdevices&used=true&filter=all&favorite=1"
)
DOMOTICZ_API_DEVICE_UPDATE = "/json.htm?type=command&param=udevice"
DOMOTICZ_API_SCENE = "/json.htm?type=command&param=getscenes"
DOMOTICZ_API_HARDWARE = "/json.htm?type=command&param=gethardware"
DOMOTICZ_API_USERS = "/json.htm?type=command&param=getusers"
DOMOTICZ_API_SETTINGS = "/json.htm?type=command&param=getsettings"
DOMOTICZ_API_CAMERAS = "/json.htm?type=command&param=getcameras"
DOMOTICZ_API_SWITCH_LIGHT = "/json.htm?type=command&param=switchlight"


class DomoticzClient:
    """Client for interacting with Domoticz JSON API.

    Attributes:
        host (str): Domoticz host or IP address.
        port (int): Domoticz port (default 8080).
        use_https (bool): Whether to use HTTPS (default False).
        username (str): Optional HTTP Basic Auth username.
        password (str): Optional HTTP Basic Auth password.

    """

    def __init__(
        self,
        host: str,
        port: int = 8080,
        use_https: bool = False,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Initialize Domoticz client.

        Args:
            host: Domoticz host or IP address.
            port: Domoticz port (default 8080).
            use_https: Whether to use HTTPS (default False).
            username: Optional HTTP Basic Auth username.
            password: Optional HTTP Basic Auth password.

        """
        self.host = host
        self.port = port
        self.use_https = use_https
        self.username = username
        self.password = password
        self.base_url = self._build_base_url()
        self.auth = self._build_auth()

    def _build_base_url(self) -> str:
        """Build base URL for Domoticz API.

        Returns:
            str: Base URL for API endpoints.

        """
        protocol = "https" if self.use_https else "http"
        return f"{protocol}://{self.host}:{self.port}"

    def _build_auth(self) -> Optional[HTTPBasicAuth]:
        """Build HTTP Basic Auth if credentials provided.

        Returns:
            Optional[HTTPBasicAuth]: Auth object or None if no credentials.

        """
        if self.username and self.password:
            return HTTPBasicAuth(self.username, self.password)
        return None

    def _make_request(
        self, endpoint: str, method: str = "GET", data: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request to Domoticz API.

        Args:
            endpoint: API endpoint path.
            method: HTTP method (GET, POST, etc.).
            data: Optional data dict for POST requests.

        Returns:
            Optional[Dict]: JSON response or None if error.

        """
        url = f"{self.base_url}{endpoint}"

        try:
            if method.upper() == "GET":
                response = requests.get(url, auth=self.auth, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, auth=self.auth, timeout=10)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None

            if response.status_code not in (
                HTTP_STATUS_OK,
                HTTP_STATUS_CREATED,
                HTTP_STATUS_NO_CONTENT,
            ):
                logger.error(f"API Error: Status {response.status_code} - {response.text}")
                return None

            # No content responses return empty dict
            if response.status_code == HTTP_STATUS_NO_CONTENT:
                return {}

            return response.json()

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to Domoticz: {e}")
            return None
        except requests.exceptions.Timeout:
            logger.error("Request timeout to Domoticz API")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Domoticz: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get Domoticz server status.

        Returns:
            Optional[Dict]: Status info or None if error.

        """
        # Try getServerTime first (more reliable)
        response = self._make_request(DOMOTICZ_API_SERVER_TIME)
        if response and "ServerTime" in response:
            return response

        # Fall back to getStatus if getServerTime fails
        response = self._make_request(DOMOTICZ_API_STATUS)
        if response and "status" in response:
            return response

        logger.error("Failed to get Domoticz status")
        return None

    def get_version(self) -> Optional[Dict[str, Any]]:
        """Get Domoticz version information.

        Returns:
            Optional[Dict]: Version info or None if error.

        """
        response = self._make_request(DOMOTICZ_API_VERSION)
        if response and ("version" in response or "status" in response):
            return response
        logger.warning("Failed to get Domoticz version")
        return None

    def get_devices(self) -> Optional[List[Dict[str, Any]]]:
        """Get list of all active Domoticz devices.

        Returns:
            Optional[List]: List of device dicts or None if error.

        """
        response = self._make_request(DOMOTICZ_API_DEVICES)
        if response and "result" in response:
            return response["result"]
        logger.warning("No devices found or error retrieving devices")
        return None

    def get_device(self, device_id: int) -> Optional[Dict[str, Any]]:
        """Get details for specific device by ID.

        Args:
            device_id: Device ID in Domoticz.

        Returns:
            Optional[Dict]: Device details or None if error.

        """
        endpoint = DOMOTICZ_API_DEVICE.format(rid=device_id)
        response = self._make_request(endpoint)
        if response and "result" in response and len(response["result"]) > 0:
            return response["result"][0]
        logger.warning(f"Device {device_id} not found")
        return None

    def get_device_by_name(self, device_name: str) -> Optional[Dict[str, Any]]:
        """Find device by name.

        Args:
            device_name: Name of the device to find.

        Returns:
            Optional[Dict]: Device details or None if not found.

        """
        devices = self.get_devices()
        if not devices:
            return None

        for device in devices:
            if device.get("Name") == device_name:
                return device

        logger.warning(f"Device '{device_name}' not found")
        return None

    def find_devices_by_mqtt_id(self, mqtt_id: str) -> List[Dict[str, Any]]:
        """Find devices by MQTT device ID.

        Args:
            mqtt_id: MQTT device ID to search for.

        Returns:
            List: Matching devices (may be empty).

        """
        devices = self.get_devices()
        if not devices:
            return []

        matching = []
        for device in devices:
            # Check HardwareName or Description for MQTT indicator
            hw_name = device.get("HardwareName", "").lower()
            description = device.get("Description", "").lower()

            if "mqtt" in hw_name or "mqtt" in description:
                # Check if name matches MQTT ID pattern
                if mqtt_id in device.get("Name", ""):
                    matching.append(device)

        return matching

    def validate_discovery_devices(self, discovery_prefix: str) -> Dict[str, Any]:
        """Validate all MQTT-discovered devices.

        Args:
            discovery_prefix: MQTT discovery prefix (e.g., "domoticz").

        Returns:
            Dict with validation results including:
                - total_devices: Number of devices found
                - mqtt_devices: Number of MQTT-based devices
                - devices: List of device details
                - errors: Any validation errors

        """
        result = {
            "total_devices": 0,
            "mqtt_devices": 0,
            "mqtt_auto_discovery_devices": 0,
            "unique_auto_discovery_ids": 0,
            "devices": [],
            "errors": [],
        }

        devices = self.get_devices()
        if not devices:
            result["errors"].append("No devices found in Domoticz")
            return result

        result["total_devices"] = len(devices)

        # Track unique auto-discovery device IDs
        unique_ids = set()

        for device in devices:
            hw_name = device.get("HardwareName", "")
            device_name = device.get("Name", "")
            device_id = device.get("ID", "")

            # Check if it's an MQTT device
            if "MQTT" in hw_name:
                result["mqtt_devices"] += 1

                # Check if it was auto-discovered by looking for discovery_prefix in unique_id (ID field)
                if discovery_prefix in device_id:
                    result["mqtt_auto_discovery_devices"] += 1
                    unique_ids.add(device_id)
                    result["devices"].append(
                        {
                            "id": device.get("idx"),
                            "name": device_name,
                            "type": device.get("Type"),
                            "subtype": device.get("SubType"),
                            "status": device.get("Status"),
                            "last_update": device.get("LastUpdate"),
                            "hardware": hw_name,
                        }
                    )

        result["unique_auto_discovery_ids"] = len(unique_ids)
        return result

    def get_device_state(self, device_id: int) -> Optional[str]:
        """Get current state/status of a device.

        Args:
            device_id: Device ID in Domoticz.

        Returns:
            Optional[str]: Device status or None if error.

        """
        device = self.get_device(device_id)
        if device:
            return device.get("Status")
        return None

    def set_device_state(
        self, device_id: int, state: str, brightness: Optional[int] = None
    ) -> bool:
        """Set device state/status.

        Args:
            device_id: Device ID in Domoticz.
            state: State to set (e.g., "On", "Off").
            brightness: Optional brightness level (0-100 for dimmers).

        Returns:
            bool: True if successful, False otherwise.

        """
        endpoint = "/json.htm?type=command&param=switchlight"
        data_dict = {"idx": device_id, "switchcmd": state}

        if brightness is not None:
            data_dict["level"] = brightness

        # Convert to query string format for Domoticz
        params = "&".join(f"{k}={v}" for k, v in data_dict.items())
        endpoint = f"/json.htm?type=command&param=switchlight&{params}"

        response = self._make_request(endpoint)
        if response and response.get("status") == "OK":
            logger.info(f"Device {device_id} state set to {state}")
            return True

        logger.error(f"Failed to set device {device_id} state")
        return False

    def get_scenes(self) -> Optional[List[Dict[str, Any]]]:
        """Get list of all scenes.

        Returns:
            Optional[List]: List of scene dicts or None if error.

        """
        response = self._make_request(DOMOTICZ_API_SCENE)
        if response and "result" in response:
            return response["result"]
        logger.warning("No scenes found or error retrieving scenes")
        return None

    def verify_connection(self) -> bool:
        """Verify connection to Domoticz server.

        Returns:
            bool: True if connection successful, False otherwise.

        """
        status = self.get_status()
        return status is not None


def create_domoticz_client(
    host: str,
    port: int = 8080,
    use_https: bool = False,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> Optional[DomoticzClient]:
    """Create and verify Domoticz client.

    Args:
        host: Domoticz host or IP address.
        port: Domoticz port (default 8080).
        use_https: Whether to use HTTPS.
        username: Optional HTTP Basic Auth username.
        password: Optional HTTP Basic Auth password.

    Returns:
        Optional[DomoticzClient]: Client instance or None if connection failed.

    """
    client = DomoticzClient(host, port, use_https, username, password)

    if not client.verify_connection():
        logger.error(f"Failed to connect to Domoticz at {host}:{port}")
        return None

    logger.info(f"Connected to Domoticz at {host}:{port}")
    return client
