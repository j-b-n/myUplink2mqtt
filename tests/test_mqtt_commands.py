"""Tests for writable-point MQTT command handling."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from myuplink2mqtt import main
from myuplink2mqtt.utils import auto_discovery_utils


def test_parse_enum_command_uses_api_value():
    point = {
        "writable": True,
        "value": "1",
        "enumValues": [
            {"value": "1", "text": "Auto"},
            {"value": "2", "text": "Manual"},
        ],
    }

    assert main.parse_write_command(point, "manual") == "2"


def test_float_enum_state_matches_decimal_api_value():
    client = MagicMock()

    main.publish_sensor_state(
        client,
        "system-1",
        "40007",
        0.3,
        [{"value": "0.3", "text": "Low"}],
    )

    client.publish.assert_called_once_with(
        "myuplink/system-1/40007/value",
        "Low",
        qos=1,
        retain=True,
    )


def test_parse_number_command_rejects_values_outside_api_bounds():
    point = {
        "writable": True,
        "value": 20.0,
        "parameterUnit": "°C",
        "minValue": 5,
        "maxValue": 30,
        "stepValue": 0.5,
    }

    assert main.parse_write_command(point, "25.5") == "25.5"
    assert main.parse_write_command(point, "25.2") is None
    assert main.parse_write_command(point, "31") is None
    assert main.parse_write_command(point, "nan") is None


def test_parse_switch_command_converts_to_api_value():
    bool_point = {"value": True, "parameterUnit": ""}
    integer_point = {"value": 0, "parameterUnit": ""}

    assert main.parse_write_command(bool_point, "OFF") == "false"
    assert main.parse_write_command(integer_point, "ON") == "1"


def test_mqtt_command_writes_only_the_discovered_writable_point():
    key = ("system-1", "device-1", "40004")
    main.WRITABLE_POINTS[key] = {
        "writable": True,
        "value": 20,
        "parameterUnit": "°C",
        "minValue": 5,
        "maxValue": 30,
    }
    message = SimpleNamespace(
        topic="myuplink/system-1/device-1/40004/set",
        payload=b"24",
        retain=False,
    )
    client = MagicMock()
    session = MagicMock()

    try:
        with patch.object(main, "set_device_point", return_value=True) as write:
            main.on_mqtt_message(client, session, message)

        write.assert_called_once_with(session, "device-1", "40004", "24")
    finally:
        main.WRITABLE_POINTS.pop(key, None)


def test_process_data_points_registers_writable_point_and_normalizes_switch_state(
    monkeypatch,
):
    monkeypatch.setattr(main, "PUBLISH_TO_MQTT", True)
    point = {
        "parameterId": "40005",
        "parameterName": "Enable heating",
        "parameterUnit": "",
        "value": False,
        "writable": True,
    }
    client = MagicMock()
    key = ("system-1", "device-1", "40005")

    try:
        main.process_data_points(
            client,
            {"id": "device-1", "name": "Heat pump"},
            "system-1",
            [point],
            False,
        )

        client.publish.assert_called_once_with(
            "myuplink/system-1/40005/value",
            "OFF",
            qos=1,
            retain=True,
        )
        assert main.WRITABLE_POINTS[key] is point
    finally:
        main.WRITABLE_POINTS.pop(key, None)


def test_retained_mqtt_command_is_ignored():
    key = ("system-1", "device-1", "40004")
    main.WRITABLE_POINTS[key] = {"writable": True, "value": 20}
    message = SimpleNamespace(
        topic="myuplink/system-1/device-1/40004/set",
        payload=b"24",
        retain=True,
    )

    try:
        with patch.object(main, "set_device_point") as write:
            main.on_mqtt_message(MagicMock(), MagicMock(), message)

        write.assert_not_called()
    finally:
        main.WRITABLE_POINTS.pop(key, None)


def test_mqtt_connect_subscribes_to_commands_and_home_assistant_status(monkeypatch):
    monkeypatch.setattr(main, "MQTT_CONNECTED", False)
    client = MagicMock()
    client.subscribe.return_value = (0, 1)

    main.on_mqtt_connect(client, None, None, SimpleNamespace(value=0), None)

    assert client.subscribe.call_args_list[0].args[0] == "myuplink/+/+/+/set"
    assert client.subscribe.call_args_list[1].args[0] == (f"{main.HA_DISCOVERY_PREFIX}/status")


def test_home_assistant_birth_replays_discovery():
    auto_discovery_utils._DISCOVERY_MESSAGES.clear()
    topic = "test-prefix/sensor/test_replay/config"
    payload = '{"unique_id": "test_replay"}'
    auto_discovery_utils._DISCOVERY_MESSAGES[topic] = payload
    message = SimpleNamespace(
        topic=f"{main.HA_DISCOVERY_PREFIX}/status",
        payload=b"online",
        retain=False,
    )
    client = MagicMock()

    main.on_mqtt_message(client, None, message)

    client.publish.assert_called_once_with(topic, payload, qos=1, retain=True)
    auto_discovery_utils._DISCOVERY_MESSAGES.pop(topic, None)


def test_poll_cycle_publishes_system_alarm_entity(monkeypatch):
    monkeypatch.setattr(main, "PUBLISH_TO_MQTT", True)
    monkeypatch.setattr(
        main,
        "get_systems",
        lambda _session: [
            {
                "systemId": "system-1",
                "name": "Home",
                "hasAlarm": True,
                "devices": [],
            }
        ],
    )
    client = MagicMock()

    main.process_poll_cycle(MagicMock(), client, 1)

    publications = [call.args for call in client.publish.call_args_list]
    assert any(call[0] == "myuplink/system-1/alarm" and call[1] == "ON" for call in publications)
    discovery = next(
        call[1]
        for call in publications
        if call[0] == "homeassistant/binary_sensor/myuplink_system_system-1_alarm/config"
    )
    assert '"device_class": "problem"' in discovery


def test_device_poll_publishes_connection_and_read_only_firmware(monkeypatch):
    monkeypatch.setattr(main, "PUBLISH_TO_MQTT", True)
    monkeypatch.setattr(
        main,
        "get_device_details",
        lambda _session, _device: {
            "product": {"name": "Nibe F-series"},
            "connectionState": "Connected",
            "firmware": {
                "currentFwVersion": "1.0",
                "desiredFwVersion": "2.0",
            },
        },
    )
    monkeypatch.setattr(main, "get_device_points", lambda _session, _device: [])
    monkeypatch.setattr(main, "extract_installation_date_values", lambda _points: (None,) * 6)
    monkeypatch.setattr(main, "process_installation_date_parameter", lambda *args: (0, 0))
    monkeypatch.setattr(main, "process_data_points", lambda *args: (0, 0))
    client = MagicMock()

    main.process_device(MagicMock(), client, "system-1", "device-1", True)

    publications = [call.args for call in client.publish.call_args_list]
    assert any(
        call[0] == "myuplink/system-1/device-1/connection" and call[1] == "ON"
        for call in publications
    )
    firmware_state = next(
        call[1] for call in publications if call[0] == "myuplink/system-1/device-1/firmware"
    )
    assert firmware_state == '{"installed_version": "1.0", "latest_version": "2.0"}'
    firmware_config = next(
        call[1]
        for call in publications
        if call[0] == "homeassistant/update/myuplink_device-1_firmware/config"
    )
    assert '"command_topic"' not in firmware_config
