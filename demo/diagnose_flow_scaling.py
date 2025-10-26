#!/usr/bin/env python3
"""Diagnostic script to identify water flow scaling issue.

Checks:
1. Domoticz device settings (dividers, scaling)
2. MQTT topic activity
3. Auto-discovery configuration
4. Device properties
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from myuplink2mqtt.utils.domoticz_json_util import create_domoticz_client


def check_device_settings(host="10.0.0.2", port=80, device_id=9185):
    """Check device settings and dividers."""
    print("\n" + "=" * 80)
    print("DOMOTICZ DEVICE SETTINGS CHECK")
    print("=" * 80)

    try:
        client = create_domoticz_client(host=host, port=port)
        print(f"✓ Connected to {host}:{port}")

        # Get device details
        endpoint = f"/json.htm?type=command&param=getdevices&idx={device_id}"
        response = client._make_request(endpoint)

        if not response or response.get("status") != "OK":
            print(f"✗ Failed to get device: {response}")
            return None

        devices = response.get("result", [])
        if not devices:
            print(f"✗ Device {device_id} not found")
            return None

        device = devices[0]
        print(f"\n✓ Found device: {device.get('Name')}")
        print(f"  Device ID: {device.get('idx')}")
        print(f"  Type: {device.get('Type')} / {device.get('SubType')}")
        print(f"  Hardware: {device.get('Hardware')}")

        # Check for scaling fields
        print("\n📊 SCALING FIELDS:")
        print("-" * 80)

        scaling_fields = {
            "DividerWater": "Water Divider",
            "DividerRain": "Rain Divider",
            "DividerEnergy": "Energy Divider",
            "DividerGas": "Gas Divider",
            "Counter": "Counter Value",
            "CostWater": "Water Cost",
            "CostRain": "Rain Cost",
            "CostEnergy": "Energy Cost",
            "CostGas": "Gas Cost",
        }

        for field, description in scaling_fields.items():
            value = device.get(field)
            if value is not None:
                print(f"  {description:20} ({field:15}): {value}")

        # Check signal properties
        print("\n📡 SIGNAL PROPERTIES:")
        print("-" * 80)

        signal_fields = {
            "LastUpdate": "Last Update",
            "LastLevel": "Last Level",
            "DeviceID": "Device ID (myUplink)",
            "ID": "Unique ID",
            "SignalLevel": "Signal Level",
            "BatteryLevel": "Battery Level",
        }

        for field, description in signal_fields.items():
            value = device.get(field)
            if value is not None:
                print(f"  {description:20} ({field:15}): {value}")

        # Check if this is a waterflow sensor
        sub_type = device.get("SubType", "").lower()
        is_waterflow = "water" in sub_type or "flow" in sub_type
        print(f"\n✓ Is Waterflow Sensor: {'Yes' if is_waterflow else 'No'}")

        # Estimate scaling issue
        divider = device.get("DividerWater")
        if divider:
            print(f"\n⚠️  Device has DividerWater: {divider}")
            print(f"   If myUplink sends 1.0, Domoticz will show: {1.0 / divider}")
            print(f"   If myUplink sends 11.3, Domoticz will show: {11.3 / divider}")

        return device

    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def check_mqtt_payload():
    """Check MQTT topic payload."""
    print("\n" + "=" * 80)
    print("MQTT PAYLOAD CHECK")
    print("=" * 80)
    print("\nTo monitor MQTT messages in real-time, run:")
    print("  mosquitto_sub -h 10.0.0.2 -t 'myuplink/#' -v | grep -i flow")
    print("\nLook for:")
    print("  - Actual flow values (should match myUplink CSV)")
    print("  - Timestamp format")
    print("  - Message structure")


def check_auto_discovery_config():
    """Check auto-discovery configuration."""
    print("\n" + "=" * 80)
    print("AUTO-DISCOVERY CONFIGURATION CHECK")
    print("=" * 80)

    try:
        # Try to read auto_discovery_utils.py
        auto_disc_file = Path(__file__).parent.parent / "myuplink2mqtt" / "utils" / "auto_discovery_utils.py"

        if not auto_disc_file.exists():
            print(f"⚠️  File not found: {auto_disc_file}")
            return

        with open(auto_disc_file, "r") as f:
            content = f.read()

        # Search for waterflow/flow config
        if "60156" in content or "flow" in content.lower():
            print("✓ Found flow-related configuration in auto_discovery_utils.py")

            # Find value_template references
            if "value_template" in content:
                print("\n⚠️  Found value_template usage")
                print("   This might contain scaling/division operations")

            # Look for divider references
            if "divider" in content.lower() or "/ 1000" in content or "* 1000" in content:
                print("⚠️  Found potential scaling operations")
                print("   Check for value_template with division or multiplication")

        # Look for specific patterns
        patterns = {
            "| float / 1000": "Divide by 1000",
            "| float / 100": "Divide by 100",
            "| float / 10": "Divide by 10",
            "| float * 1000": "Multiply by 1000",
            "| float * 100": "Multiply by 100",
        }

        for pattern, description in patterns.items():
            if pattern in content:
                print(f"⚠️  Found: {description}")

    except Exception as e:
        print(f"✗ Error: {e}")


def calculate_probable_divider():
    """Calculate what divider would explain the difference."""
    print("\n" + "=" * 80)
    print("PROBABLE DIVIDER CALCULATION")
    print("=" * 80)

    myuplink_values = [3.1, 4.5, 9.2, 11.3, 9.1, 8.1]
    domoticz_max = 0.19

    myuplink_max = max(myuplink_values)

    probable_divider = myuplink_max / domoticz_max

    print(f"\nmyUplink max value: {myuplink_max} l/min")
    print(f"Domoticz max value: {domoticz_max} l/min")
    print(f"\nProbable divider: {probable_divider:.1f}")
    print(f"\nIf DividerWater = {int(probable_divider)}")
    print(f"  myUplink 11.3 → Domoticz {11.3 / int(probable_divider):.3f}")
    print(f"  myUplink 9.2 → Domoticz {9.2 / int(probable_divider):.3f}")
    print(f"  myUplink 3.1 → Domoticz {3.1 / int(probable_divider):.3f}")

    # Check common dividers
    print(f"\n📊 TESTING COMMON DIVIDERS:")
    print("   Divider    myUplink 11.3 → Domoticz    myUplink 3.1 → Domoticz")
    print("   " + "-" * 60)

    for divider in [10, 50, 60, 100, 1000]:
        result_113 = 11.3 / divider
        result_31 = 3.1 / divider
        marker = "✓ MATCH!" if abs(result_113 - domoticz_max) < 0.01 else ""
        print(f"   {divider:>6}     {result_113:>8.4f}                    {result_31:>8.4f}   {marker}")


def main():
    """Run all diagnostics."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "WATER FLOW SCALING ISSUE - DIAGNOSTICS" + " " * 25 + "║")
    print("╚" + "=" * 78 + "╝")

    # Check device settings
    device = check_device_settings()

    # Check MQTT
    check_mqtt_payload()

    # Check auto-discovery
    check_auto_discovery_config()

    # Calculate probable divider
    calculate_probable_divider()

    # Summary
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("""
1. Check Domoticz device settings:
   http://10.0.0.2/device.html?idx=9185
   Look for: DividerWater or scaling settings

2. Monitor MQTT in real-time:
   mosquitto_sub -h 10.0.0.2 -t 'myuplink/#' -v

3. Compare MQTT values with myUplink CSV:
   - Check if MQTT shows 11.3 (myUplink) or 0.19 (scaled)
   - If 11.3: Problem is in Domoticz storage/display
   - If 0.19: Problem is in myUplink→MQTT conversion

4. Check auto-discovery config:
   - Review auto_discovery_utils.py for value_template
   - Look for any division/multiplication operations

5. Once root cause identified:
   - Update the corresponding component
   - Re-run compare_waterflow_data.py to verify fix
    """)


if __name__ == "__main__":
    main()
