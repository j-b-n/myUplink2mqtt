"""Reusable utilities for myUplink API authentication and operations.

This module provides shared functionality for interacting with the myUplink API,
including OAuth authentication, token management, and device operations.
Follows the MarshFlattsFarm pattern for token storage.
"""

import json
import logging
import os
import re
from json import dump, load
from os import path

import aiohttp
from myuplink import Auth, MyUplinkAPI
from requests_oauthlib import OAuth2Session

# Logger initialization
logger = logging.getLogger(__name__)

# HTTP status code for successful requests
HTTP_STATUS_OK = 200

# myUplink API base URL
MYUPLINK_API_BASE = "https://api.myuplink.com"

# Token file location (following MarshFlattsFarm pattern)
HOME_DIR = path.expanduser("~")
TOKEN_FILENAME = HOME_DIR + "/.myUplink_API_Token.json"

# Config file for client credentials
CONFIG_FILENAME = HOME_DIR + "/.myUplink_API_Config.json"


def token_saver(token):
    """Save the OAuth token to file when it's refreshed.

    Args:
        token (dict): The OAuth token dictionary to save.

    """
    with open(TOKEN_FILENAME, "w", encoding="utf-8") as token_file:
        dump(token, token_file)
    logger.info("Token refreshed and saved to file")


def load_config():
    """Load client configuration from file or environment variables.

    Configuration is loaded in the following order:
    1. Config file at ~/.myUplink_API_Config.json
    2. Environment variables: MYUPLINK_CLIENT_ID and MYUPLINK_CLIENT_SECRET

    Returns:
        tuple: (client_id, client_secret) or (None, None) if not found or error.

    """
    config = {}

    # Try to load from config file first
    if path.exists(CONFIG_FILENAME):
        try:
            with open(CONFIG_FILENAME, encoding="utf-8") as config_file:
                config = load(config_file)
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Could not parse config file {CONFIG_FILENAME}: {e}")
            return None, None

    # Override with environment variables if set
    client_id = os.getenv("MYUPLINK_CLIENT_ID") or config.get("client_id")
    client_secret = os.getenv("MYUPLINK_CLIENT_SECRET") or config.get("client_secret")

    return client_id, client_secret


def check_oauth_prerequisites():
    """Check if OAuth prerequisites are met.

    Verifies that both client credentials and OAuth token are available.

    Returns:
        tuple: (can_proceed: bool, error_message: str or None)
            - can_proceed: True if all prerequisites are met
            - error_message: Descriptive error message if prerequisites are not met

    """
    # Check for client credentials
    client_id, client_secret = load_config()

    if not client_id or not client_secret:
        error_msg = (
            "Client credentials not found. Please either:\n"
            "1. Set environment variables: MYUPLINK_CLIENT_ID and "
            "MYUPLINK_CLIENT_SECRET\n"
            "2. Or create a config file ~/.myUplink_API_Config.json with:\n"
            '   {"client_id": "your_client_id", '
            '"client_secret": "your_client_secret"}'
        )
        return False, error_msg

    # Check for token file
    if not path.exists(TOKEN_FILENAME):
        error_msg = (
            f"OAuth token file not found: {TOKEN_FILENAME}\n"
            "Please obtain an OAuth token using request_token.py and save it to "
            "~/.myUplink_API_Token.json"
        )
        return False, error_msg

    return True, None


async def test_api_availability():
    """Test API availability by pinging the myUplink API.

    Returns:
        bool: True if API is available and responding, False otherwise.

    """
    async with aiohttp.ClientSession() as session:
        # For ping, we don't need authentication
        auth = Auth(session, MYUPLINK_API_BASE, "")
        api = MyUplinkAPI(auth)

        try:
            ping_result = await api.async_ping()
            logger.debug(f"API Ping successful: {ping_result}")
            return ping_result
        except (OSError, aiohttp.ClientError) as e:
            logger.error(f"API Ping failed: {e}")
            return False


def load_oauth_token():
    """Load OAuth token from JSON file.

    Returns:
        dict: The OAuth token dictionary.

    Raises:
        FileNotFoundError: If token file does not exist.
        json.JSONDecodeError: If token file is not valid JSON.

    """
    if not path.exists(TOKEN_FILENAME):
        raise FileNotFoundError(f"Token file not found: {TOKEN_FILENAME}")

    with open(TOKEN_FILENAME, encoding="utf-8") as token_file:
        token = load(token_file)
    return token


def create_oauth_session():
    """Create OAuth2Session with token refresh capability.

    Returns:
        OAuth2Session: An OAuth2 session object configured for myUplink API.

    Raises:
        FileNotFoundError: If token file is not found.
        json.JSONDecodeError: If token or config file is invalid JSON.
        ValueError: If client credentials are not available.

    """
    client_id, client_secret = load_config()

    if not client_id or not client_secret:
        raise ValueError("Client credentials not found. Cannot create OAuth session.")

    token = load_oauth_token()
    token_url = f"{MYUPLINK_API_BASE}/oauth/token"

    # Specify the list of extra arguments to include when refreshing a Token
    extra_args = {"client_id": client_id, "client_secret": client_secret}

    # Instantiate an OAuth2Session object that will automatically refresh tokens
    myuplink = OAuth2Session(
        client_id=client_id,
        token=token,
        auto_refresh_url=token_url,
        auto_refresh_kwargs=extra_args,
        token_updater=token_saver,
    )

    return myuplink


def get_device_brands(myuplink, devices):
    """Get brand information for a list of devices.

    Extracts manufacturer and model information from device product data.

    Args:
        myuplink (OAuth2Session): Authenticated OAuth2 session.
        devices (list): List of device info dictionaries from API response.

    Returns:
        list: List of brand strings (e.g., ["Nibe F1155", "IVT GEO"]).

    """
    brands = []
    for device_info in devices:
        device_id = device_info["id"]
        try:
            # Get detailed device information
            device_response = myuplink.get(f"{MYUPLINK_API_BASE}/v2/devices/{device_id}")
            if device_response.status_code != HTTP_STATUS_OK:
                brands.append(f"Device {device_id} (API error)")
                continue

            device_data = device_response.json()
            product_name = device_data["product"]["name"]

            # Extract manufacturer from product name (simple approach)
            # Most myUplink devices follow patterns like "Nibe F1155"
            # or "Jäspi Tehowatti Air"
            if " " in product_name:
                parts = product_name.split(" ", 1)
                manufacturer = parts[0]
                model = parts[1]
                brands.append(f"{manufacturer} {model}")
            else:
                brands.append(product_name)

        except (OSError, ValueError, KeyError) as e:
            brands.append(f"Device {device_id} (error: {e!s})")

    return brands


def get_manufacturer(device_details):
    """Extract manufacturer name from device details.

    Args:
        device_details (dict): Device details dictionary from API response.

    Returns:
        str: Manufacturer name or "Unknown" if unable to determine.

    """
    try:
        if not device_details or "product" not in device_details:
            return "Unknown"

        product_name = device_details["product"]["name"]

        # Extract manufacturer from product name (simple approach)
        # Most myUplink devices follow patterns like "Nibe F1155"
        # or "Jäspi Tehowatti Air"
        if " " in product_name:
            manufacturer = product_name.split(" ", 1)[0]
            return manufacturer

        return product_name

    except (KeyError, TypeError):
        return "Unknown"


def get_systems(myuplink):
    """Retrieve systems assigned to the authorized user.

    Args:
        myuplink (OAuth2Session): Authenticated OAuth2 session.

    Returns:
        list: List of system dictionaries or None if request failed.

    """
    try:
        response = myuplink.get(f"{MYUPLINK_API_BASE}/v2/systems/me")

        if response.status_code != HTTP_STATUS_OK:
            logger.error(f"Failed to get systems. HTTP Status: {response.status_code}")
            logger.error(response.text)
            return None

        data = response.json()
        return data.get("systems", [])

    except (OSError, ValueError, KeyError) as e:
        logger.error(f"Error retrieving systems: {e}")
        return None


def get_device_details(myuplink, device_id):
    """Retrieve detailed information for a specific device.

    Args:
        myuplink (OAuth2Session): Authenticated OAuth2 session.
        device_id (str): The device ID.

    Returns:
        dict: Device details dictionary or None if request failed.

    """
    try:
        response = myuplink.get(f"{MYUPLINK_API_BASE}/v2/devices/{device_id}")

        if response.status_code != HTTP_STATUS_OK:
            logger.error(f"Failed to get device details. HTTP Status: {response.status_code}")
            return None

        return response.json()

    except (OSError, ValueError, KeyError) as e:
        logger.error(f"Error retrieving device details for {device_id}: {e}")
        return None


def get_device_points(myuplink, device_id, parameters=None, language="en-US"):
    """Retrieve data points for a specific device.

    Args:
        myuplink (OAuth2Session): Authenticated OAuth2 session.
        device_id (str): The device ID.
        parameters (list, optional): List of specific parameter IDs to retrieve.
                                    If None, retrieves all available points.
        language (str): Language code for parameter labels (default: 'en-US').

    Returns:
        list: List of point dictionaries or None if request failed.

    """
    try:
        url = f"{MYUPLINK_API_BASE}/v2/devices/{device_id}/points"

        query_params = []
        if parameters:
            query_params.append(f"parameters={','.join(parameters)}")
        if language:
            query_params.append(f"language={language}")

        if query_params:
            url += "?" + "&".join(query_params)

        response = myuplink.get(url)

        if response.status_code != HTTP_STATUS_OK:
            logger.error(f"Failed to get device points. HTTP Status: {response.status_code}")
            return None

        return response.json()

    except (OSError, ValueError, KeyError) as e:
        logger.error(f"Error retrieving device points for {device_id}: {e}")
        return None


def format_parameter_value(point, display_name=None):
    """Format parameter value with appropriate units based on parameter name.

    Args:
        point (dict): Parameter point dictionary containing 'parameterName' and 'value'.
        display_name (str, optional): Display name to use for formatting logic.
                                    If None, uses point['parameterName'].

    Returns:
        str: Formatted value string with appropriate units.

    """
    value = point["value"]
    parameter_name = display_name if display_name is not None else point["parameterName"]

    # Add units based on parameter name patterns
    if "temp" in parameter_name.lower() or "BT" in parameter_name:
        return f"{value} °C"
    if "humid" in parameter_name.lower():
        return f"{value} rh%"
    if "flow" in parameter_name.lower():
        return f"{value} l/m"

    # Format installation date values as integers (no decimals)
    if "Installation" in parameter_name:
        return str(int(value))

    return str(value)


def get_parameter_display_name(point):
    """Get the display name for a parameter, handling 'Text not found' cases.

    Maps parameter IDs from "Text not found: id[XXXXX]" messages to human-readable names.

    Args:
        point (dict): Parameter point dictionary containing 'parameterName'.

    Returns:
        str: Display name for the parameter.

    """
    parameter_name = point["parameterName"]

    # Clean up soft hyphens and trim whitespace
    parameter_name = parameter_name.replace("\u00ad", "").strip()

    # Clean up device name prefix pattern like "SAK (..." -> extract content in parens
    # Pattern: "WORD (" where WORD is 1+ word characters
    # This handles both "SAK (SAK Operating mode)" and "SAK (Ratio hot water [...])"
    match = re.match(r"^(\w+)\s*\((.+)\)$", parameter_name)
    if match:
        # Extract the content inside parentheses
        inner_content = match.group(2)

        # Check if inner content starts with the same device name pattern
        # e.g., "SAK (SAK Operating mode)" -> extract just "Operating mode"
        device_name = match.group(1)
        inner_pattern = re.match(r"^" + re.escape(device_name) + r"\s+(.+)$", inner_content)
        if inner_pattern:
            # Device name is repeated, extract content after it
            parameter_name = inner_pattern.group(1)
        else:
            # Device name is not repeated, use content as-is
            parameter_name = inner_content
    # Extract parameter ID from "Text not found: id[XXXXX]" format
    parameter_id = ""
    if parameter_name.startswith("Text not found: id["):
        try:
            # Extract ID from format: "Text not found: id[60720], fw[noem-h], lang[en-US]"
            id_start = parameter_name.find("id[") + 3
            id_end = parameter_name.find("]", id_start)
            parameter_id = parameter_name[id_start:id_end]
        except (ValueError, IndexError):
            parameter_id = ""

    # Map known parameter IDs to proper names
    parameter_id_mapping = {
        "60720": "Installation year",
        "60719": "Installation month",
        "60704": "Installation day",
    }

    # If we found a parameter ID and have a mapping, use it
    if parameter_id and parameter_id in parameter_id_mapping:
        return parameter_id_mapping[parameter_id]

    # For unmapped "Text not found" parameters, show "No Label (<ID>)"
    if parameter_id:
        return f"No Label ({parameter_id})"

    return parameter_name
