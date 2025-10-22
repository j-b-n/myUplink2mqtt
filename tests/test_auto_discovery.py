"""Tests for auto-discovery utilities module.

Tests the auto-discovery functionality for Home Assistant MQTT integration,
including payload generation, device class mapping, and parameter handling.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add project root to path before importing local modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from myuplink2mqtt.utils.auto_discovery_utils import (  # pylint: disable=wrong-import-position
    build_discovery_payload,
    clean_parameter_name,
    determine_device_class,
    determine_entity_category,
    determine_value_type,
    get_parameter_id_to_device_class_mapping,
    get_unit_to_device_class_mapping,
    normalize_unit,
    publish_ha_discovery,
)


class TestNormalizeUnit:
    """Test unit normalization functionality."""

    def test_normalize_relative_humidity(self):
        """Test normalization of relative humidity units."""
        assert normalize_unit("rh%") == "%"

    def test_normalize_standard_unit(self):
        """Test that standard units are returned unchanged."""
        assert normalize_unit("°C") == "°C"
        assert normalize_unit("kW") == "kW"
        assert normalize_unit("A") == "A"

    def test_normalize_empty_unit(self):
        """Test normalization of empty string."""
        assert normalize_unit("") == ""

    def test_normalize_unknown_unit(self):
        """Test that unknown units are returned unchanged."""
        assert normalize_unit("unknown_unit") == "unknown_unit"


class TestGetUnitToDeviceClassMapping:
    """Test unit to device class mapping."""

    def test_temperature_mappings(self):
        """Test temperature unit mappings."""
        mapping = get_unit_to_device_class_mapping()
        assert mapping["°C"] == "temperature"
        assert mapping["C"] == "temperature"
        assert mapping["°F"] == "temperature"
        assert mapping["F"] == "temperature"

    def test_energy_mappings(self):
        """Test energy unit mappings."""
        mapping = get_unit_to_device_class_mapping()
        assert mapping["kWh"] == "energy"
        assert mapping["Wh"] == "energy"

    def test_power_mappings(self):
        """Test power unit mappings."""
        mapping = get_unit_to_device_class_mapping()
        assert mapping["kW"] == "power"
        assert mapping["W"] == "power"

    def test_mapping_is_dict(self):
        """Test that the mapping is a dictionary."""
        mapping = get_unit_to_device_class_mapping()
        assert isinstance(mapping, dict)
        assert len(mapping) > 0


class TestGetParameterIdToDeviceClassMapping:
    """Test parameter ID to device class mapping."""

    def test_alarm_mapping(self):
        """Test alarm parameter mapping."""
        mapping = get_parameter_id_to_device_class_mapping()
        assert mapping["43161"] == "binary_sensor"

    def test_humidity_mapping(self):
        """Test humidity parameter mapping."""
        mapping = get_parameter_id_to_device_class_mapping()
        assert mapping["60433"] == "humidity"

    def test_mapping_is_dict(self):
        """Test that the mapping is a dictionary."""
        mapping = get_parameter_id_to_device_class_mapping()
        assert isinstance(mapping, dict)


class TestDetermineDeviceClass:
    """Test device class determination."""

    def test_device_class_by_parameter_id(self):
        """Test device class determination by parameter ID priority."""
        # Parameter ID '43161' should map to 'binary_sensor'
        device_class = determine_device_class("°C", "43161")
        assert device_class == "binary_sensor"

    def test_device_class_by_unit(self):
        """Test device class determination by unit."""
        assert determine_device_class("°C", "12345") == "temperature"
        assert determine_device_class("kW", "12345") == "power"
        assert determine_device_class("A", "12345") == "current"

    def test_device_class_none_when_not_found(self):
        """Test that None is returned when no device class matches."""
        device_class = determine_device_class("unknown_unit", "99999")
        assert device_class is None

    def test_device_class_humidity_unit(self):
        """Test humidity device class from unit."""
        device_class = determine_device_class("rh%", "12345")
        assert device_class == "humidity"


class TestDetermineValueType:
    """Test value type determination."""

    def test_bool_type(self):
        """Test boolean value type detection."""
        assert determine_value_type(True) == "bool"
        assert determine_value_type(False) == "bool"

    def test_int_type(self):
        """Test integer value type detection."""
        assert determine_value_type(42) == "int"
        assert determine_value_type(0) == "int"
        assert determine_value_type(-5) == "int"

    def test_float_type(self):
        """Test float value type detection."""
        assert determine_value_type(3.14) == "float"
        assert determine_value_type(0.0) == "float"

    def test_string_type(self):
        """Test string value type detection."""
        assert determine_value_type("hello") == "string"
        assert determine_value_type("") == "string"

    def test_none_type(self):
        """Test None value type detection."""
        assert determine_value_type(None) == "string"


class TestDetermineEntityCategory:
    """Test entity category determination."""

    def test_diagnostic_by_id(self):
        """Test diagnostic category assignment by parameter ID."""
        # Parameter ID '43161' is in diagnostic list
        category = determine_entity_category("43161", "Some parameter")
        assert category == "diagnostic"

        # Parameter ID '43437' is in diagnostic list
        category = determine_entity_category("43437", "Some parameter")
        assert category == "diagnostic"

    def test_diagnostic_by_keyword(self):
        """Test diagnostic category assignment by parameter name keywords."""
        keywords = ["accumulated", "total", "starts", "runtime", "hours", "alarm", "error"]
        for keyword in keywords:
            category = determine_entity_category("12345", f"Parameter {keyword} name")
            assert category == "diagnostic", f"Failed for keyword: {keyword}"

    def test_diagnostic_case_insensitive(self):
        """Test that keyword matching is case insensitive."""
        category = determine_entity_category("12345", "Parameter ACCUMULATED Time")
        assert category == "diagnostic"

    def test_none_for_regular_parameter(self):
        """Test that None is returned for regular parameters."""
        category = determine_entity_category("12345", "Regular sensor value")
        assert category is None


class TestCleanParameterName:
    """Test parameter name cleaning."""

    def test_clean_name_with_prefix(self):
        """Test removing device name prefix."""
        result = clean_parameter_name("SAK (Set automatically)", "SAK")
        assert result == "Set automatically"

    def test_clean_name_without_prefix(self):
        """Test parameter name without prefix is unchanged."""
        result = clean_parameter_name("Regular parameter", "SAK")
        assert result == "Regular parameter"

    def test_clean_name_with_nested_parentheses(self):
        """Test cleaning with nested parentheses."""
        result = clean_parameter_name("Device (Param (nested))", "Device")
        assert result == "Param (nested)"

    def test_clean_name_no_closing_paren(self):
        """Test handling of malformed names without closing parenthesis."""
        result = clean_parameter_name("Device (Param without close", "Device")
        assert result == "Device (Param without close"

    def test_clean_name_empty_string(self):
        """Test cleaning empty parameter name."""
        result = clean_parameter_name("", "SAK")
        assert result == ""

    def test_clean_name_only_device_name(self):
        """Test parameter that is just the device name."""
        result = clean_parameter_name("SAK ()", "SAK")
        assert result == ""


class TestBuildDiscoveryPayload:
    """Test discovery payload generation."""

    def get_sample_device_info(self):
        """Return sample device information."""
        return {
            "id": "device123",
            "device_name": "SAK",
            "manufacturer": "IVT",
            "model": "GT",
            "serial": "ABC123",
        }

    def get_sample_parameter_info(self):
        """Return sample parameter information."""
        return {
            "id": "40004",
            "name": "SAK (Set automatically)",
            "value": 21.5,
            "unit": "°C",
            "value_type": "float",
        }

    def test_payload_has_required_fields(self):
        """Test that payload contains all required fields."""
        device_info = self.get_sample_device_info()
        parameter_info = self.get_sample_parameter_info()
        state_topic = "myuplink/sys1/40004/value"
        availability_topic = "myuplink/sys1/available"

        payload = build_discovery_payload(
            device_info, parameter_info, state_topic, availability_topic
        )

        # Check required fields exist
        assert "name" in payload
        assert "unique_id" in payload
        assert "state_topic" in payload
        assert "availability_topic" in payload
        assert "device" in payload
        assert "origin" in payload

    def test_payload_device_class_for_temperature(self):
        """Test payload includes device class for temperature."""
        device_info = self.get_sample_device_info()
        parameter_info = self.get_sample_parameter_info()
        state_topic = "myuplink/sys1/40004/value"
        availability_topic = "myuplink/sys1/available"

        payload = build_discovery_payload(
            device_info, parameter_info, state_topic, availability_topic
        )

        assert payload["device_class"] == "temperature"
        assert payload["unit_of_measurement"] == "°C"

    def test_payload_state_class_measurement(self):
        """Test payload includes state class for measurement."""
        device_info = self.get_sample_device_info()
        parameter_info = self.get_sample_parameter_info()
        state_topic = "myuplink/sys1/40004/value"
        availability_topic = "myuplink/sys1/available"

        payload = build_discovery_payload(
            device_info, parameter_info, state_topic, availability_topic
        )

        assert payload["state_class"] == "measurement"

    def test_payload_state_class_total_increasing_for_energy(self):
        """Test payload has total_increasing state class for energy."""
        device_info = self.get_sample_device_info()
        parameter_info = self.get_sample_parameter_info()
        parameter_info["unit"] = "kWh"
        state_topic = "myuplink/sys1/40004/value"
        availability_topic = "myuplink/sys1/available"

        payload = build_discovery_payload(
            device_info, parameter_info, state_topic, availability_topic
        )

        assert payload["state_class"] == "total_increasing"

    def test_payload_binary_sensor_detection(self):
        """Test that bool values create binary sensor payloads."""
        device_info = self.get_sample_device_info()
        parameter_info = self.get_sample_parameter_info()
        parameter_info["value_type"] = "bool"
        parameter_info["unit"] = ""
        state_topic = "myuplink/sys1/40004/value"
        availability_topic = "myuplink/sys1/available"

        payload = build_discovery_payload(
            device_info, parameter_info, state_topic, availability_topic
        )

        # Binary sensors should not have unit_of_measurement
        assert "unit_of_measurement" not in payload

    def test_payload_entity_category(self):
        """Test that entity category is included when provided."""
        device_info = self.get_sample_device_info()
        parameter_info = self.get_sample_parameter_info()
        parameter_info["category"] = "diagnostic"
        state_topic = "myuplink/sys1/40004/value"
        availability_topic = "myuplink/sys1/available"

        payload = build_discovery_payload(
            device_info, parameter_info, state_topic, availability_topic
        )

        assert payload["entity_category"] == "diagnostic"

    def test_payload_serial_number(self):
        """Test that serial number is included in device info."""
        device_info = self.get_sample_device_info()
        parameter_info = self.get_sample_parameter_info()
        state_topic = "myuplink/sys1/40004/value"
        availability_topic = "myuplink/sys1/available"

        payload = build_discovery_payload(
            device_info, parameter_info, state_topic, availability_topic
        )

        assert payload["device"]["serial_number"] == "ABC123"

    def test_payload_no_serial_number_when_empty(self):
        """Test that serial number is not included when empty."""
        device_info = self.get_sample_device_info()
        device_info["serial"] = ""
        parameter_info = self.get_sample_parameter_info()
        state_topic = "myuplink/sys1/40004/value"
        availability_topic = "myuplink/sys1/available"

        payload = build_discovery_payload(
            device_info, parameter_info, state_topic, availability_topic
        )

        assert "serial_number" not in payload["device"]

    def test_payload_cleaned_parameter_name(self):
        """Test that parameter name is cleaned in payload."""
        device_info = self.get_sample_device_info()
        parameter_info = self.get_sample_parameter_info()
        state_topic = "myuplink/sys1/40004/value"
        availability_topic = "myuplink/sys1/available"

        payload = build_discovery_payload(
            device_info, parameter_info, state_topic, availability_topic
        )

        # Name should be cleaned (device prefix removed)
        assert payload["name"] == "Set automatically"

    def test_payload_origin_info(self):
        """Test that origin information is included."""
        device_info = self.get_sample_device_info()
        parameter_info = self.get_sample_parameter_info()
        state_topic = "myuplink/sys1/40004/value"
        availability_topic = "myuplink/sys1/available"

        payload = build_discovery_payload(
            device_info, parameter_info, state_topic, availability_topic
        )

        assert payload["origin"]["name"] == "myUplink2mqtt"
        assert "sw" in payload["origin"]
        assert "url" in payload["origin"]

    def test_payload_availability_config(self):
        """Test that availability configuration is correct."""
        device_info = self.get_sample_device_info()
        parameter_info = self.get_sample_parameter_info()
        state_topic = "myuplink/sys1/40004/value"
        availability_topic = "myuplink/sys1/available"

        payload = build_discovery_payload(
            device_info, parameter_info, state_topic, availability_topic
        )

        assert payload["availability_mode"] == "latest"
        assert payload["payload_available"] == "online"
        assert payload["payload_not_available"] == "offline"


class TestPublishHaDiscovery:
    """Test Home Assistant discovery publishing."""

    def get_sample_device_info(self):
        """Return sample device information."""
        return {
            "id": "device123",
            "device_name": "SAK",
            "manufacturer": "IVT",
            "model": "GT",
        }

    def get_sample_parameter_info(self):
        """Return sample parameter information."""
        return {
            "id": "40004",
            "name": "Temperature",
            "value": 21.5,
            "unit": "°C",
            "value_type": "float",
        }

    def test_publish_returns_true_on_success(self):
        """Test that publish returns True on success."""
        mock_client = MagicMock()
        device_info = self.get_sample_device_info()
        parameter_info = self.get_sample_parameter_info()

        result = publish_ha_discovery(mock_client, device_info, parameter_info, "system1")

        assert result is True
        mock_client.publish.assert_called_once()

    def test_publish_called_with_correct_topic(self):
        """Test that publish is called with correct discovery topic."""
        mock_client = MagicMock()
        device_info = self.get_sample_device_info()
        parameter_info = self.get_sample_parameter_info()

        publish_ha_discovery(mock_client, device_info, parameter_info, "system1")

        call_args = mock_client.publish.call_args
        topic = call_args[0][0]
        # Topic should start with homeassistant/sensor/ for non-binary sensor
        assert "homeassistant/sensor/" in topic
        assert "myuplink_device123_40004/config" in topic

    def test_publish_called_with_json_payload(self):
        """Test that publish is called with valid JSON payload."""
        mock_client = MagicMock()
        device_info = self.get_sample_device_info()
        parameter_info = self.get_sample_parameter_info()

        publish_ha_discovery(mock_client, device_info, parameter_info, "system1")

        call_args = mock_client.publish.call_args
        payload_str = call_args[0][1]
        # Should be valid JSON
        payload = json.loads(payload_str)
        assert isinstance(payload, dict)
        assert "name" in payload
        assert "state_topic" in payload

    def test_publish_with_qos_and_retain(self):
        """Test that publish is called with correct QoS and retain."""
        mock_client = MagicMock()
        device_info = self.get_sample_device_info()
        parameter_info = self.get_sample_parameter_info()

        publish_ha_discovery(mock_client, device_info, parameter_info, "system1")

        call_args = mock_client.publish.call_args
        # Check keyword arguments
        assert call_args[1]["qos"] == 1
        assert call_args[1]["retain"] is True

    def test_publish_returns_false_on_error(self):
        """Test that publish returns False on error."""
        mock_client = MagicMock()
        mock_client.publish.side_effect = Exception("MQTT error")
        device_info = self.get_sample_device_info()
        parameter_info = self.get_sample_parameter_info()

        result = publish_ha_discovery(mock_client, device_info, parameter_info, "system1")

        assert result is False

    def test_publish_binary_sensor_topic(self):
        """Test that binary sensor uses correct topic."""
        mock_client = MagicMock()
        device_info = self.get_sample_device_info()
        parameter_info = self.get_sample_parameter_info()
        parameter_info["value_type"] = "bool"
        parameter_info["unit"] = ""

        publish_ha_discovery(mock_client, device_info, parameter_info, "system1")

        call_args = mock_client.publish.call_args
        topic = call_args[0][0]
        # Topic should use binary_sensor component
        assert "homeassistant/binary_sensor/" in topic

    def test_publish_handles_missing_parameter_fields(self):
        """Test that publish handles missing optional fields gracefully."""
        mock_client = MagicMock()
        device_info = self.get_sample_device_info()
        parameter_info = {
            "id": "40004",
            "name": "Temperature",
            "value": 21.5,
            # Missing 'unit' and 'value_type'
        }

        # Should not raise an exception
        result = publish_ha_discovery(mock_client, device_info, parameter_info, "system1")

        # Should still publish successfully with defaults
        assert result is True
        mock_client.publish.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
