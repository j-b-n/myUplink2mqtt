"""Tests for myuplink_utils module.

Comprehensive test suite for OAuth authentication, token management,
and myUplink API operations using mock data and sessions.
"""

import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from myuplink2mqtt.utils.myuplink_utils import (
    check_oauth_prerequisites,
    create_oauth_session,
    format_parameter_value,
    get_device_brands,
    get_device_details,
    get_device_points,
    get_manufacturer,
    get_parameter_display_name,
    get_systems,
    load_config,
    load_oauth_token,
    token_saver,
)

# ============================================================================
# Tests for Configuration Loading
# ============================================================================


class TestLoadConfig:
    """Test suite for load_config function."""

    def test_load_config_from_file(self, tmp_path, mock_config):
        """Test loading configuration from file.

        Args:
            tmp_path: pytest temporary directory.
            mock_config: Mock config data fixture.
        """
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(mock_config))

        with patch("myuplink2mqtt.utils.myuplink_utils.CONFIG_FILENAME", str(config_file)):
            client_id, client_secret = load_config()

        assert client_id == mock_config["client_id"]
        assert client_secret == mock_config["client_secret"]

    def test_load_config_from_env_variables(self, mock_config):
        """Test loading configuration from environment variables.

        Args:
            mock_config: Mock config data fixture.
        """
        env_vars = {
            "MYUPLINK_CLIENT_ID": "env_client_id",
            "MYUPLINK_CLIENT_SECRET": "env_client_secret",
        }

        with patch.dict("os.environ", env_vars, clear=False), patch(
            "myuplink2mqtt.utils.myuplink_utils.CONFIG_FILENAME", "/nonexistent/config.json"
        ):
            client_id, client_secret = load_config()

        assert client_id == "env_client_id"
        assert client_secret == "env_client_secret"

    def test_load_config_env_overrides_file(self, tmp_path, mock_config):
        """Test that environment variables override file configuration.

        Args:
            tmp_path: pytest temporary directory.
            mock_config: Mock config data fixture.
        """
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(mock_config))

        env_vars = {
            "MYUPLINK_CLIENT_ID": "env_override_id",
            "MYUPLINK_CLIENT_SECRET": "env_override_secret",
        }

        with patch(
            "myuplink2mqtt.utils.myuplink_utils.CONFIG_FILENAME", str(config_file)
        ), patch.dict("os.environ", env_vars, clear=False):
            client_id, client_secret = load_config()

        assert client_id == "env_override_id"
        assert client_secret == "env_override_secret"

    def test_load_config_returns_none_when_not_found(self):
        """Test that None is returned when configuration is not found."""
        with patch(
            "myuplink2mqtt.utils.myuplink_utils.CONFIG_FILENAME", "/nonexistent/path.json"
        ), patch.dict("os.environ", {}, clear=True):
            client_id, client_secret = load_config()

        assert client_id is None
        assert client_secret is None

    def test_load_config_handles_invalid_json(self, tmp_path):
        """Test handling of invalid JSON in config file.

        Args:
            tmp_path: pytest temporary directory.
        """
        config_file = tmp_path / "config.json"
        config_file.write_text("{ invalid json }")

        with patch(
            "myuplink2mqtt.utils.myuplink_utils.CONFIG_FILENAME", str(config_file)
        ), patch.dict("os.environ", {}, clear=True):
            client_id, client_secret = load_config()

        assert client_id is None
        assert client_secret is None


# ============================================================================
# Tests for Token Management
# ============================================================================


class TestTokenSaver:
    """Test suite for token_saver function."""

    def test_token_saver_writes_file(self, tmp_path, mock_oauth_token):
        """Test that token_saver writes token to file.

        Args:
            tmp_path: pytest temporary directory.
            mock_oauth_token: Mock OAuth token fixture.
        """
        token_file = tmp_path / "token.json"

        with patch("myuplink2mqtt.utils.myuplink_utils.TOKEN_FILENAME", str(token_file)):
            token_saver(mock_oauth_token)

        # Verify file was written
        assert token_file.exists()

        # Verify content
        saved_token = json.loads(token_file.read_text())
        assert saved_token == mock_oauth_token

    def test_token_saver_overwrites_existing(self, tmp_path, mock_oauth_token):
        """Test that token_saver overwrites existing token file.

        Args:
            tmp_path: pytest temporary directory.
            mock_oauth_token: Mock OAuth token fixture.
        """
        token_file = tmp_path / "token.json"
        old_token = {"access_token": "old_token"}
        token_file.write_text(json.dumps(old_token))

        with patch("myuplink2mqtt.utils.myuplink_utils.TOKEN_FILENAME", str(token_file)):
            token_saver(mock_oauth_token)

        saved_token = json.loads(token_file.read_text())
        assert saved_token == mock_oauth_token


class TestLoadOauthToken:
    """Test suite for load_oauth_token function."""

    def test_load_oauth_token_success(self, tmp_path, mock_oauth_token):
        """Test successful loading of OAuth token.

        Args:
            tmp_path: pytest temporary directory.
            mock_oauth_token: Mock OAuth token fixture.
        """
        token_file = tmp_path / "token.json"
        token_file.write_text(json.dumps(mock_oauth_token))

        with patch("myuplink2mqtt.utils.myuplink_utils.TOKEN_FILENAME", str(token_file)):
            token = load_oauth_token()

        assert token == mock_oauth_token

    def test_load_oauth_token_file_not_found(self):
        """Test that FileNotFoundError is raised when token file missing."""
        with patch("myuplink2mqtt.utils.myuplink_utils.TOKEN_FILENAME", "/nonexistent/token.json"):
            with pytest.raises(FileNotFoundError):
                load_oauth_token()

    def test_load_oauth_token_invalid_json(self, tmp_path):
        """Test that JSONDecodeError is raised for invalid JSON.

        Args:
            tmp_path: pytest temporary directory.
        """
        token_file = tmp_path / "token.json"
        token_file.write_text("{ invalid json }")

        with patch("myuplink2mqtt.utils.myuplink_utils.TOKEN_FILENAME", str(token_file)):
            with pytest.raises(json.JSONDecodeError):
                load_oauth_token()


# ============================================================================
# Tests for OAuth Prerequisites
# ============================================================================


class TestCheckOauthPrerequisites:
    """Test suite for check_oauth_prerequisites function."""

    def test_prerequisites_met(self, patch_config_paths):
        """Test successful prerequisite check.

        Args:
            patch_config_paths: Config path patching fixture.
        """
        can_proceed, error = check_oauth_prerequisites()

        assert can_proceed is True
        assert error is None

    def test_prerequisites_missing_credentials(self):
        """Test prerequisite check fails with missing credentials."""
        with patch(
            "myuplink2mqtt.utils.myuplink_utils.load_config", return_value=(None, None)
        ), patch.dict("os.environ", {}, clear=True):
            can_proceed, error = check_oauth_prerequisites()

        assert can_proceed is False
        assert error is not None
        assert "Client credentials not found" in error

    def test_prerequisites_missing_token_file(self, tmp_path, mock_config):
        """Test prerequisite check fails with missing token file.

        Args:
            tmp_path: pytest temporary directory.
            mock_config: Mock config data fixture.
        """
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(mock_config))

        with patch("myuplink2mqtt.utils.myuplink_utils.CONFIG_FILENAME", str(config_file)), patch(
            "myuplink2mqtt.utils.myuplink_utils.TOKEN_FILENAME", "/nonexistent/token.json"
        ):
            can_proceed, error = check_oauth_prerequisites()

        assert can_proceed is False
        assert error is not None
        assert "OAuth token file not found" in error


# ============================================================================
# Tests for OAuth Session Creation
# ============================================================================


class TestCreateOauthSession:
    """Test suite for create_oauth_session function."""

    def test_create_oauth_session_success(self, patch_config_paths):
        """Test successful OAuth session creation.

        Args:
            patch_config_paths: Config path patching fixture.
        """
        with patch("myuplink2mqtt.utils.myuplink_utils.OAuth2Session") as mock_oauth2:
            session = create_oauth_session()

        assert session is not None
        mock_oauth2.assert_called_once()

    def test_create_oauth_session_missing_credentials(self):
        """Test OAuth session creation fails without credentials."""
        with patch("myuplink2mqtt.utils.myuplink_utils.load_config", return_value=(None, None)):
            with pytest.raises(ValueError):
                create_oauth_session()

    def test_create_oauth_session_missing_token(self, tmp_path, mock_config):
        """Test OAuth session creation fails without token file.

        Args:
            tmp_path: pytest temporary directory.
            mock_config: Mock config data fixture.
        """
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(mock_config))

        with patch("myuplink2mqtt.utils.myuplink_utils.CONFIG_FILENAME", str(config_file)), patch(
            "myuplink2mqtt.utils.myuplink_utils.TOKEN_FILENAME", "/nonexistent/token.json"
        ):
            with pytest.raises(FileNotFoundError):
                create_oauth_session()


# ============================================================================
# Tests for Systems API
# ============================================================================


class TestGetSystems:
    """Test suite for get_systems function."""

    def test_get_systems_success(self, mock_oauth_session, mock_systems_response):
        """Test successful systems retrieval.

        Args:
            mock_oauth_session: Mock OAuth session fixture.
            mock_systems_response: Mock systems response fixture.
        """
        systems = get_systems(mock_oauth_session)

        assert systems is not None
        assert len(systems) == 2
        assert systems[0]["name"] == "My Home System"
        assert systems[1]["name"] == "Cabin System"

    def test_get_systems_returns_devices(self, mock_oauth_session):
        """Test that systems include device information.

        Args:
            mock_oauth_session: Mock OAuth session fixture.
        """
        systems = get_systems(mock_oauth_session)

        assert systems[0]["devices"] is not None
        assert len(systems[0]["devices"]) == 2
        assert systems[0]["devices"][0]["id"] == "device-001"

    def test_get_systems_api_error(self, mock_oauth_session_with_errors):
        """Test systems retrieval handles API errors.

        Args:
            mock_oauth_session_with_errors: Mock session with errors fixture.
        """
        systems = get_systems(mock_oauth_session_with_errors)

        assert systems is None

    def test_get_systems_handles_exception(self):
        """Test systems retrieval handles exceptions."""
        mock_session = MagicMock()
        mock_session.get.side_effect = ValueError("Connection error")

        systems = get_systems(mock_session)

        assert systems is None


# ============================================================================
# Tests for Device Details API
# ============================================================================


class TestGetDeviceDetails:
    """Test suite for get_device_details function."""

    def test_get_device_details_nibe(self, mock_oauth_session, mock_device_details_nibe):
        """Test retrieving Nibe device details.

        Args:
            mock_oauth_session: Mock OAuth session fixture.
            mock_device_details_nibe: Mock Nibe device details fixture.
        """
        details = get_device_details(mock_oauth_session, "device-001")

        assert details is not None
        assert details["product"]["name"] == "Nibe F1155"
        assert details["product"]["brand"] == "Nibe"

    def test_get_device_details_ivt(self, mock_oauth_session, mock_device_details_ivt):
        """Test retrieving IVT device details.

        Args:
            mock_oauth_session: Mock OAuth session fixture.
            mock_device_details_ivt: Mock IVT device details fixture.
        """
        details = get_device_details(mock_oauth_session, "device-002")

        assert details is not None
        assert details["product"]["name"] == "IVT GEO 6"
        assert details["product"]["brand"] == "IVT"

    def test_get_device_details_api_error(self, mock_oauth_session_with_errors):
        """Test device details retrieval handles API errors.

        Args:
            mock_oauth_session_with_errors: Mock session with errors fixture.
        """
        details = get_device_details(mock_oauth_session_with_errors, "device-001")

        assert details is None

    def test_get_device_details_handles_exception(self):
        """Test device details retrieval handles exceptions."""
        mock_session = MagicMock()
        mock_session.get.side_effect = OSError("Connection error")

        details = get_device_details(mock_session, "device-001")

        assert details is None


# ============================================================================
# Tests for Device Points API
# ============================================================================


class TestGetDevicePoints:
    """Test suite for get_device_points function."""

    def test_get_device_points_all(self, mock_oauth_session, mock_device_points_response):
        """Test retrieving all device points.

        Args:
            mock_oauth_session: Mock OAuth session fixture.
            mock_device_points_response: Mock points response fixture.
        """
        points = get_device_points(mock_oauth_session, "device-001")

        assert points is not None
        assert len(points["points"]) == 5

    def test_get_device_points_specific_parameters(self, mock_oauth_session):
        """Test retrieving specific device points by parameter ID.

        Args:
            mock_oauth_session: Mock OAuth session fixture.
        """
        parameters = ["40004", "40012"]
        points = get_device_points(mock_oauth_session, "device-001", parameters=parameters)

        assert points is not None

    def test_get_device_points_with_language(self, mock_oauth_session):
        """Test retrieving device points with specific language.

        Args:
            mock_oauth_session: Mock OAuth session fixture.
        """
        points = get_device_points(mock_oauth_session, "device-001", language="sv-SE")

        assert points is not None

    def test_get_device_points_api_error(self, mock_oauth_session_with_errors):
        """Test device points retrieval handles API errors.

        Args:
            mock_oauth_session_with_errors: Mock session with errors fixture.
        """
        points = get_device_points(mock_oauth_session_with_errors, "device-001")

        assert points is None

    def test_get_device_points_handles_exception(self):
        """Test device points retrieval handles exceptions."""
        mock_session = MagicMock()
        mock_session.get.side_effect = KeyError("Invalid response format")

        points = get_device_points(mock_session, "device-001")

        assert points is None


# ============================================================================
# Tests for Device Brands
# ============================================================================


class TestGetDeviceBrands:
    """Test suite for get_device_brands function."""

    def test_get_device_brands_multiple_devices(self, mock_oauth_session):
        """Test retrieving brands for multiple devices.

        Args:
            mock_oauth_session: Mock OAuth session fixture.
        """
        devices = [{"id": "device-001"}, {"id": "device-002"}]
        brands = get_device_brands(mock_oauth_session, devices)

        assert len(brands) == 2
        assert "Nibe" in brands[0]
        assert "IVT" in brands[1]

    def test_get_device_brands_api_error_handling(self):
        """Test device brands handles API errors gracefully."""
        mock_session = MagicMock()
        response = Mock()
        response.status_code = 500
        mock_session.get.return_value = response

        devices = [{"id": "device-001"}]
        brands = get_device_brands(mock_session, devices)

        assert len(brands) == 1
        assert "API error" in brands[0]

    def test_get_device_brands_exception_handling(self):
        """Test device brands handles exceptions gracefully."""
        mock_session = MagicMock()
        mock_session.get.side_effect = ValueError("Connection error")

        devices = [{"id": "device-001"}]
        brands = get_device_brands(mock_session, devices)

        assert len(brands) == 1
        assert "error" in brands[0].lower()


# ============================================================================
# Tests for Manufacturer Extraction
# ============================================================================


class TestGetManufacturer:
    """Test suite for get_manufacturer function."""

    def test_get_manufacturer_from_nibe_device(self, mock_device_details_nibe):
        """Test extracting manufacturer from Nibe device.

        Args:
            mock_device_details_nibe: Mock Nibe device details fixture.
        """
        manufacturer = get_manufacturer(mock_device_details_nibe)

        assert manufacturer == "Nibe"

    def test_get_manufacturer_from_ivt_device(self, mock_device_details_ivt):
        """Test extracting manufacturer from IVT device.

        Args:
            mock_device_details_ivt: Mock IVT device details fixture.
        """
        manufacturer = get_manufacturer(mock_device_details_ivt)

        assert manufacturer == "IVT"

    def test_get_manufacturer_single_word_product(self):
        """Test manufacturer extraction from single-word product name."""
        device = {"product": {"name": "Unknown", "brand": "Unknown"}}
        manufacturer = get_manufacturer(device)

        assert manufacturer == "Unknown"

    def test_get_manufacturer_missing_product(self):
        """Test manufacturer extraction handles missing product info."""
        device = {}
        manufacturer = get_manufacturer(device)

        assert manufacturer == "Unknown"

    def test_get_manufacturer_none_input(self):
        """Test manufacturer extraction handles None input."""
        manufacturer = get_manufacturer(None)

        assert manufacturer == "Unknown"


# ============================================================================
# Tests for Parameter Value Formatting
# ============================================================================


class TestFormatParameterValue:
    """Test suite for format_parameter_value function."""

    def test_format_temperature_value(self):
        """Test temperature value formatting."""
        point = {"value": 21.5, "parameterName": "Room temperature"}
        formatted = format_parameter_value(point)

        assert formatted == "21.5 °C"

    def test_format_temperature_with_bt_prefix(self):
        """Test temperature formatting with BT prefix."""
        point = {"value": 8.2, "parameterName": "BT21 Outdoor temperature"}
        formatted = format_parameter_value(point)

        assert formatted == "8.2 °C"

    def test_format_humidity_value(self):
        """Test humidity value formatting."""
        point = {"value": 65.0, "parameterName": "Humidity"}
        formatted = format_parameter_value(point)

        assert formatted == "65.0 rh%"

    def test_format_flow_value(self):
        """Test flow value formatting."""
        point = {"value": 12.5, "parameterName": "Flow rate"}
        formatted = format_parameter_value(point)

        assert formatted == "12.5 l/m"

    def test_format_installation_date(self):
        """Test installation date formatting (integer, no decimals)."""
        point = {"value": 2023.0, "parameterName": "Installation year"}
        formatted = format_parameter_value(point)

        assert formatted == "2023"

    def test_format_generic_value(self):
        """Test generic value formatting."""
        point = {"value": "ON", "parameterName": "Heating status"}
        formatted = format_parameter_value(point)

        assert formatted == "ON"

    def test_format_with_display_name_override(self):
        """Test formatting with display name override."""
        point = {"value": 21.5, "parameterName": "Generic name"}
        formatted = format_parameter_value(point, display_name="BT Temperature")

        assert formatted == "21.5 °C"


# ============================================================================
# Tests for Parameter Display Name
# ============================================================================


class TestGetParameterDisplayName:
    """Test suite for get_parameter_display_name function."""

    def test_get_display_name_normal_parameter(self):
        """Test display name extraction for normal parameter."""
        point = {"parameterName": "Actual room temperature"}
        display_name = get_parameter_display_name(point)

        assert display_name == "Actual room temperature"

    def test_get_display_name_installation_year(self):
        """Test display name extraction for installation year."""
        point = {"parameterName": "Text not found: id[60720], fw[noem-h], lang[en-US]"}
        display_name = get_parameter_display_name(point)

        assert display_name == "Installation year"

    def test_get_display_name_installation_month(self):
        """Test display name extraction for installation month."""
        point = {"parameterName": "Text not found: id[60719], fw[noem-h], lang[en-US]"}
        display_name = get_parameter_display_name(point)

        assert display_name == "Installation month"

    def test_get_display_name_installation_day(self):
        """Test display name extraction for installation day."""
        point = {"parameterName": "Text not found: id[60704], fw[noem-h], lang[en-US]"}
        display_name = get_parameter_display_name(point)

        assert display_name == "Installation day"

    def test_get_display_name_unmapped_id(self):
        """Test display name for unmapped parameter ID."""
        point = {"parameterName": "Text not found: id[99999], fw[noem-h], lang[en-US]"}
        display_name = get_parameter_display_name(point)

        assert "No Label (99999)" == display_name

    def test_get_display_name_sak_device(self):
        """Test display name extraction for SAK device parameter."""
        point = {"parameterName": "SAK (SAK Operating mode)"}
        display_name = get_parameter_display_name(point)

        assert display_name == "Operating mode"

    def test_get_display_name_device_prefix(self):
        """Test display name extraction removes device prefix when it repeats."""
        # The function only removes device prefix when it's single word and repeats
        # e.g., "SAK (SAK Operating mode)" -> "Operating mode"
        # For "Hot water (Ratio hot water defrost)", it keeps the parenthesized content
        # because "Hot" doesn't match the full prefix "Hot water"
        point = {"parameterName": "SAK (SAK Operating mode)"}
        display_name = get_parameter_display_name(point)

        assert display_name == "Operating mode"

    def test_get_display_name_soft_hyphen_cleanup(self):
        """Test display name removes soft hyphens."""
        point = {"parameterName": "Temperature\u00adsensor"}
        display_name = get_parameter_display_name(point)

        assert display_name == "Temperaturesensor"

    def test_get_display_name_whitespace_handling(self):
        """Test display name handles extra whitespace."""
        point = {"parameterName": "  Spaced  Parameter  "}
        display_name = get_parameter_display_name(point)

        # Should be trimmed
        assert display_name.strip() == display_name

    def test_get_display_name_text_not_found_extraction_error(self):
        """Test display name handles malformed Text not found format."""
        point = {"parameterName": "Text not found: id[60720"}
        display_name = get_parameter_display_name(point)

        # Should handle gracefully without crashing
        assert isinstance(display_name, str)


# ============================================================================
# Tests for Exception Handling Edge Cases
# ============================================================================


class TestGetDeviceBrandsExceptionHandling:
    """Test suite for exception handling in get_device_brands."""

    def test_get_device_brands_keyerror_handling(self):
        """Test device brands handles KeyError from API response."""
        mock_session = MagicMock()
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"invalid": "structure"}
        mock_session.get.return_value = response

        devices = [{"id": "device-001"}]
        brands = get_device_brands(mock_session, devices)

        assert len(brands) == 1
        assert "error" in brands[0].lower()

    def test_get_device_brands_oserror_handling(self):
        """Test device brands handles OSError."""
        mock_session = MagicMock()
        mock_session.get.side_effect = OSError("Connection refused")

        devices = [{"id": "device-001"}]
        brands = get_device_brands(mock_session, devices)

        assert len(brands) == 1
        assert "error" in brands[0].lower()

    def test_get_device_brands_valueerror_handling(self):
        """Test device brands handles ValueError from device_data access."""
        mock_session = MagicMock()
        response = Mock()
        response.status_code = 200
        # This will trigger when trying to access device_data['product']['name']
        response.json.return_value = {"invalid": "structure"}
        mock_session.get.return_value = response

        devices = [{"id": "device-001"}]
        brands = get_device_brands(mock_session, devices)

        # Should catch KeyError and append error message
        assert len(brands) == 1
        assert "error" in brands[0].lower()

    def test_get_device_brands_json_parse_error(self):
        """Test device brands handles JSON parsing errors."""
        mock_session = MagicMock()
        response = Mock()
        response.status_code = 200
        response.json.side_effect = ValueError("Invalid JSON response")
        mock_session.get.return_value = response

        devices = [{"id": "device-001"}]
        brands = get_device_brands(mock_session, devices)

        # Should catch ValueError and append error message
        assert len(brands) == 1
        assert "error" in brands[0].lower()

    def test_get_device_brands_single_word_product(self):
        """Test device brands with single-word product name."""
        mock_session = MagicMock()
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "product": {
                "name": "SingleWord"  # No space in name
            }
        }
        mock_session.get.return_value = response

        devices = [{"id": "device-001"}]
        brands = get_device_brands(mock_session, devices)

        # Should append single word product name as-is
        assert len(brands) == 1
        assert brands[0] == "SingleWord"


class TestGetManufacturerExceptionHandling:
    """Test suite for exception handling in get_manufacturer."""

    def test_get_manufacturer_keyerror_handling(self):
        """Test manufacturer extraction handles KeyError."""
        # Malformed device_details structure
        device = {"invalid": "structure"}
        manufacturer = get_manufacturer(device)

        assert manufacturer == "Unknown"

    def test_get_manufacturer_typeerror_handling(self):
        """Test manufacturer extraction handles TypeError."""
        # Pass non-dict type
        device = "not a dict"
        manufacturer = get_manufacturer(device)

        assert manufacturer == "Unknown"

    def test_get_manufacturer_nested_typeerror(self):
        """Test manufacturer extraction handles nested TypeError."""
        # Device with None product
        device = {"product": None}
        manufacturer = get_manufacturer(device)

        assert manufacturer == "Unknown"


class TestGetParameterDisplayNameExceptionHandling:
    """Test suite for exception handling in get_parameter_display_name."""

    def test_get_display_name_index_error_handling(self):
        """Test display name handles IndexError in ID extraction."""
        point = {"parameterName": "Text not found: id[], fw[noem-h]"}
        display_name = get_parameter_display_name(point)

        # Should handle gracefully
        assert isinstance(display_name, str)

    def test_get_display_name_malformed_id_format(self):
        """Test display name handles malformed ID format."""
        point = {"parameterName": "Text not found: id[notanumber]"}
        display_name = get_parameter_display_name(point)

        assert "No Label (notanumber)" == display_name

    def test_get_display_name_nested_parentheses(self):
        """Test display name handles nested parentheses."""
        point = {"parameterName": "Device (Name (Nested) Mode)"}
        display_name = get_parameter_display_name(point)

        # Should extract content in parentheses
        assert isinstance(display_name, str)
        assert "Device" not in display_name or display_name == "Device (Name (Nested) Mode)"

    def test_get_display_name_text_not_found_no_closing_bracket(self):
        """Test display name handles Text not found with missing closing bracket."""
        point = {"parameterName": "Text not found: id[60720"}
        display_name = get_parameter_display_name(point)

        # Should handle gracefully - id_end will be -1, causing empty string
        assert isinstance(display_name, str)


# ============================================================================
# Tests for API Availability (Async)
# ============================================================================


class TestApiAvailability:
    """Test suite for test_api_availability function."""

    @pytest.mark.asyncio
    async def test_api_availability_success(self):
        """Test successful API ping."""

        from myuplink2mqtt.utils.myuplink_utils import test_api_availability

        with patch(
            "myuplink2mqtt.utils.myuplink_utils.aiohttp.ClientSession"
        ) as mock_session_class:
            with patch("myuplink2mqtt.utils.myuplink_utils.Auth"):
                with patch("myuplink2mqtt.utils.myuplink_utils.MyUplinkAPI") as mock_api_class:
                    # Mock the async context manager
                    mock_session = AsyncMock()
                    mock_session_class.return_value.__aenter__.return_value = mock_session
                    mock_session_class.return_value.__aexit__.return_value = None

                    # Mock the async_ping to return True
                    mock_api = AsyncMock()
                    mock_api.async_ping = AsyncMock(return_value=True)
                    mock_api_class.return_value = mock_api

                    # Call the function
                    result = await test_api_availability()

                    # Verify result
                    assert result is True

    @pytest.mark.asyncio
    async def test_api_availability_connection_error(self):
        """Test API ping handles connection errors."""
        import aiohttp

        from myuplink2mqtt.utils.myuplink_utils import test_api_availability

        with patch(
            "myuplink2mqtt.utils.myuplink_utils.aiohttp.ClientSession"
        ) as mock_session_class:
            with patch("myuplink2mqtt.utils.myuplink_utils.Auth"):
                with patch("myuplink2mqtt.utils.myuplink_utils.MyUplinkAPI") as mock_api_class:
                    # Mock the async context manager
                    mock_session = AsyncMock()
                    mock_session_class.return_value.__aenter__.return_value = mock_session
                    mock_session_class.return_value.__aexit__.return_value = None

                    # Mock the async_ping to raise an error
                    mock_api = AsyncMock()
                    mock_api.async_ping = AsyncMock(
                        side_effect=aiohttp.ClientError("Connection failed")
                    )
                    mock_api_class.return_value = mock_api

                    # Call the function
                    result = await test_api_availability()

                    # Should return False on error
                    assert result is False
