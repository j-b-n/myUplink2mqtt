"""Demo script to fetch water flow sensor history from Domoticz.

This script demonstrates how to:
1. Connect to Domoticz server
2. Find the "Flow, hot water (BF4)" sensor
3. Retrieve its historical data
4. Display the data in a readable format

The script helps debug water flow sensor values and trends.

Usage:
    python demo_water_flow_history.py

Configuration:
    Domoticz Server: 10.0.0.2:80 (can be overridden with environment variables)

Environment Variables:
    DOMOTICZ_HOST: Domoticz server IP/hostname (default: 10.0.0.2)
    DOMOTICZ_PORT: Domoticz server port (default: 80)
    DOMOTICZ_USERNAME: Optional HTTP Basic Auth username
    DOMOTICZ_PASSWORD: Optional HTTP Basic Auth password

For more information, see docs/DOMOTICZ_JSON_UTIL.md
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from myuplink2mqtt.utils.domoticz_json_util import (
    create_domoticz_client,
    DomoticzClient,
)

# Configure logging
logger = logging.getLogger(__name__)

# Domoticz API Configuration defaults
DOMOTICZ_HOST = os.getenv("DOMOTICZ_HOST", "10.0.0.2")
DOMOTICZ_PORT = int(os.getenv("DOMOTICZ_PORT", "80"))
DOMOTICZ_USERNAME = os.getenv("DOMOTICZ_USERNAME")
DOMOTICZ_PASSWORD = os.getenv("DOMOTICZ_PASSWORD")

# Water flow sensor name to search for
WATER_FLOW_SENSOR_NAME = "Flow, hot water (BF4)"


def setup_logging(debug_mode=False, silent_mode=False):
    """Configure logging with appropriate level and format.

    Args:
        debug_mode (bool): Enable debug-level logging.
        silent_mode (bool): Suppress all logging output.
    """
    if silent_mode:
        log_level = logging.CRITICAL + 1  # Suppress all logging
    elif debug_mode:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def find_water_flow_sensor(
    client: DomoticzClient, sensor_name: str = WATER_FLOW_SENSOR_NAME
) -> Optional[Dict[str, Any]]:
    """Find water flow sensor by name.

    Args:
        client: DomoticzClient instance.
        sensor_name: Name of the sensor to find.

    Returns:
        Optional[Dict]: Device details or None if not found.
    """
    print(f"\n📍 Searching for sensor: '{sensor_name}'...")

    device = client.get_device_by_name(sensor_name)
    if device:
        print(f"✓ Found sensor!")
        print(f"  Device ID: {device.get('idx')}")
        print(f"  Name: {device.get('Name')}")
        print(f"  Type: {device.get('Type')}")
        print(f"  SubType: {device.get('SubType')}")
        print(f"  Status: {device.get('Status')}")
        print(f"  Last Update: {device.get('LastUpdate')}")
        print(f"  Hardware: {device.get('HardwareName')}")
        return device

    print(f"✗ Sensor '{sensor_name}' not found")
    print("\nAvailable devices:")
    devices = client.get_devices()
    if devices:
        for idx, device in enumerate(devices, 1):
            print(
                f"  {idx}. {device.get('Name')} (ID: {device.get('idx')}, "
                f"Type: {device.get('Type')})"
            )
    return None


def fetch_device_history(
    client: DomoticzClient, device_id: int, sensor_type: str = "Percentage",
    range_type: str = "day", method: int = 1
) -> Optional[Dict[str, Any]]:
    """Fetch historical data points for a waterflow device.

    The graph endpoint with sensor=Percentage returns detailed data points
    with timestamps and flow meter values.

    Args:
        client: DomoticzClient instance.
        device_id: Device ID in Domoticz.
        sensor_type: Type of sensor (Percentage for flow data).
        range_type: Time range for data (day, month, year).
        method: Graph method (1 for detailed points).

    Returns:
        Optional[Dict]: Historical data or None if fetch failed.
    """
    print(f"\n📊 Fetching historical data points for device {device_id}...")
    print(f"   Sensor Type: {sensor_type}")
    print(f"   Range: {range_type}")
    print(f"   Method: {method}")

    # Try different endpoints for waterflow data points
    endpoints_to_try = [
        # Percentage sensor with method=1 for detailed points
        f"/json.htm?type=command&param=graph&sensor={sensor_type}&idx={device_id}&range={range_type}&method={method}",
        # Alternative ranges
        f"/json.htm?type=command&param=graph&sensor=Percentage&idx={device_id}&range=month&method=1",
        f"/json.htm?type=command&param=graph&sensor=Percentage&idx={device_id}&range=year&method=1",
        # Try counter endpoint for comparison
        f"/json.htm?type=command&param=graph&sensor=counter&idx={device_id}&range={range_type}",
    ]

    for endpoint in endpoints_to_try:
        try:
            logger.debug(f"Trying endpoint: {endpoint}")
            response = client._make_request(endpoint)

            if response and response.get("status") not in ("ERR", "ERROR"):
                print(f"✓ Successfully fetched data from:")
                print(f"   {endpoint}")
                return response
            elif response:
                logger.debug(f"Endpoint returned error status: {response.get('status')}")

        except Exception as e:
            logger.debug(f"Error with endpoint {endpoint}: {e}")

    print(f"✗ Failed to fetch historical data with standard endpoints")
    return None


def display_sensor_details(device: Dict[str, Any]):
    """Display detailed sensor information.

    Args:
        device: Device details dictionary.
    """
    print("\n" + "=" * 60)
    print("SENSOR DETAILS")
    print("=" * 60)

    details = {
        "Device ID": device.get("idx"),
        "Name": device.get("Name"),
        "Type": device.get("Type"),
        "SubType": device.get("SubType"),
        "Hardware": device.get("HardwareName"),
        "Status": device.get("Status"),
        "LastUpdate": device.get("LastUpdate"),
        "Unit": device.get("Unit", "N/A"),
        "Description": device.get("Description", "N/A"),
        "Favorite": device.get("Favorite", 0),
        "Hidden": device.get("Hidden", 0),
        "DeviceID": device.get("DeviceID", "N/A"),
        "ID": device.get("ID", "N/A"),
    }

    for key, value in details.items():
        print(f"  {key:.<30} {value}")


def display_history_data(history_data: Dict[str, Any]):
    """Display historical data points in a readable format.

    Args:
        history_data: Historical data from Domoticz.
    """
    print("\n" + "=" * 60)
    print("HISTORICAL DATA POINTS")
    print("=" * 60)

    # Check for data points in result array
    if "result" in history_data and isinstance(history_data["result"], list):
        results = history_data["result"]
        print(f"\n📈 Found {len(results)} data point(s)")

        if results:
            print("\n" + "-" * 60)
            print(f"{'Date/Time':<20} {'Flow (l/min)':<15} {'Index':<5}")
            print("-" * 60)

            # Display all points
            for idx, entry in enumerate(results, 1):
                timestamp = entry.get("d", "N/A")
                value = entry.get("v", "N/A")
                print(f"{timestamp:<20} {value:<15} #{idx}")

            # Summary statistics
            if len(results) > 1:
                print("\n" + "-" * 60)
                print("STATISTICS:")
                print("-" * 60)

                # Extract numeric values
                values = []
                for entry in results:
                    try:
                        val = float(entry.get("v", 0))
                        values.append(val)
                    except (ValueError, TypeError):
                        pass

                if values:
                    min_val = min(values)
                    max_val = max(values)
                    avg_val = sum(values) / len(values)

                    print(f"Data Points: {len(values)}")
                    print(f"Min Flow: {min_val:.4f} l/min")
                    print(f"Max Flow: {max_val:.4f} l/min")
                    print(f"Avg Flow: {avg_val:.4f} l/min")
                    print(f"Total (if cumulative): {sum(values):.4f}")

    # Check for counter data (alternative format)
    elif "CostWater" in history_data:
        # This is counter data
        print("\n� COUNTER DATA FORMAT (Domoticz Total):")
        print("-" * 60)
        print(f"Water Cost Total.......... {history_data.get('CostWater', 'N/A')}")
        print(f"Gas Cost Total............ {history_data.get('CostGas', 'N/A')}")
        print(f"Energy Cost Total......... {history_data.get('CostEnergy', 'N/A')}")
        print()
        print("Data Dividers:")
        print(f"  Divider (water)......... {history_data.get('DividerWater', 'N/A')}")
        print(f"  Divider (energy)....... {history_data.get('DividerEnergy', 'N/A')}")
        print()
        print(f"Title..................... {history_data.get('title', 'N/A')}")

    # Fallback: print entire response for debugging
    else:
        print("\nRaw Response:")
        print(json.dumps(history_data, indent=2))


def list_all_flow_sensors(client: DomoticzClient):
    """List all devices with 'flow' in their name (flow sensors).

    Args:
        client: DomoticzClient instance.
    """
    print("\n" + "=" * 60)
    print("SEARCHING FOR FLOW SENSORS")
    print("=" * 60)

    devices = client.get_devices()
    if not devices:
        print("No devices found")
        return

    flow_sensors = [
        d for d in devices if "flow" in d.get("Name", "").lower()
    ]

    if flow_sensors:
        print(f"\n✓ Found {len(flow_sensors)} flow sensor(s):\n")
        for sensor in flow_sensors:
            print(f"  ID: {sensor.get('idx'):>3} | Name: {sensor.get('Name')}")
            print(
                f"       Type: {sensor.get('Type')}, "
                f"SubType: {sensor.get('SubType')}"
            )
            print(f"       Status: {sensor.get('Status')}")
            print(f"       Last Update: {sensor.get('LastUpdate')}")
            print()
    else:
        print("\n✗ No flow sensors found")
        print("\nAll devices in system:")
        for device in devices:
            print(f"  ID: {device.get('idx'):>3} | {device.get('Name')}")


def debug_sensor_response(
    client: DomoticzClient, device_id: int
) -> Optional[Dict[str, Any]]:
    """Debug sensor by fetching raw response in multiple formats.

    Args:
        client: DomoticzClient instance.
        device_id: Device ID to debug.

    Returns:
        Optional[Dict]: Response data or None if failed.
    """
    print("\n" + "=" * 60)
    print("DEBUG: TESTING DIFFERENT ENDPOINTS")
    print("=" * 60)

    endpoints = [
        f"/json.htm?type=command&param=graph&idx={device_id}&range=day",
        f"/json.htm?type=command&param=getdevices&idx={device_id}",
        f"/json.htm?type=command&param=getdevices&rid={device_id}",
    ]

    results = {}
    for endpoint in endpoints:
        print(f"\n🔍 Testing endpoint: {endpoint}")
        try:
            response = client._make_request(endpoint)
            if response:
                print(f"✓ Response received")
                results[endpoint] = response
                # Print first 500 chars of response
                print(f"   Preview: {str(response)[:200]}...")
            else:
                print(f"✗ No response (None)")
        except Exception as e:
            print(f"✗ Error: {e}")

    return results if results else None


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Fetch water flow sensor history from Domoticz",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default server (10.0.0.2:80)
  python demo_water_flow_history.py

  # Connect to specific Domoticz server
  python demo_water_flow_history.py --domoticz-host 192.168.1.100 --domoticz-port 8080

  # With authentication
  python demo_water_flow_history.py --domoticz-host 192.168.1.100 --domoticz-username admin --domoticz-password secret

  # Debug mode
  python demo_water_flow_history.py --debug
        """,
    )

    parser.add_argument(
        "--domoticz-host",
        default=DOMOTICZ_HOST,
        help=f"Domoticz server IP/hostname (default: {DOMOTICZ_HOST})",
    )
    parser.add_argument(
        "--domoticz-port",
        type=int,
        default=DOMOTICZ_PORT,
        help=f"Domoticz server port (default: {DOMOTICZ_PORT})",
    )
    parser.add_argument(
        "--domoticz-username",
        default=DOMOTICZ_USERNAME,
        help="HTTP Basic Auth username (optional)",
    )
    parser.add_argument(
        "--domoticz-password",
        default=DOMOTICZ_PASSWORD,
        help="HTTP Basic Auth password (optional)",
    )
    parser.add_argument(
        "--list-sensors",
        action="store_true",
        help="List all flow sensors and exit",
    )
    parser.add_argument(
        "--sensor-name",
        default=WATER_FLOW_SENSOR_NAME,
        help=f"Sensor name to search for (default: {WATER_FLOW_SENSOR_NAME})",
    )
    parser.add_argument(
        "--device-id",
        type=int,
        help="Direct device ID (skip sensor name search)",
    )
    parser.add_argument(
        "--sensor-type",
        default="Percentage",
        help="Sensor type for graph endpoint (default: Percentage for flow data)",
    )
    parser.add_argument(
        "--range",
        default="day",
        choices=["day", "month", "year"],
        help="Time range for historical data (default: day)",
    )
    parser.add_argument(
        "--method",
        type=int,
        default=1,
        help="Graph method for retrieving data points (default: 1)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        help="Suppress all logging",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(debug_mode=args.debug, silent_mode=args.silent)

    print("\n" + "=" * 60)
    print("DOMOTICZ WATER FLOW SENSOR HISTORY DEBUGGER")
    print("=" * 60)
    print(f"Server: {args.domoticz_host}:{args.domoticz_port}")

    # Create client
    client = create_domoticz_client(
        args.domoticz_host,
        args.domoticz_port,
        use_https=False,
        username=args.domoticz_username,
        password=args.domoticz_password,
    )

    if not client:
        print("\n✗ Failed to connect to Domoticz server")
        print(f"  Please check:")
        print(f"  - Server is running at {args.domoticz_host}:{args.domoticz_port}")
        print(f"  - Firewall allows access")
        print(f"  - Credentials are correct (if required)")
        return 1

    print("✓ Connected to Domoticz server\n")

    # List all sensors if requested
    if args.list_sensors:
        list_all_flow_sensors(client)
        return 0

    # Get device
    device = None
    if args.device_id:
        print(f"📍 Fetching device {args.device_id}...")
        device = client.get_device(args.device_id)
        if not device:
            print(f"✗ Device {args.device_id} not found")
            return 1
    else:
        device = find_water_flow_sensor(client, args.sensor_name)

    if not device:
        print("\n💡 Tip: Use --list-sensors to see all available sensors")
        return 1

    # Display sensor details
    display_sensor_details(device)

    # Fetch historical data
    device_id = device.get("idx")
    history_data = fetch_device_history(
        client, device_id, sensor_type=args.sensor_type, range_type=args.range,
        method=args.method
    )

    if history_data:
        display_history_data(history_data)
    else:
        print("\n💡 Trying debug endpoints...")
        debug_results = debug_sensor_response(client, device_id)
        if debug_results:
            print("\n📝 Debug Results:")
            for endpoint, response in debug_results.items():
                print(f"\n{endpoint}:")
                print(json.dumps(response, indent=2)[:500])

    print("\n" + "=" * 60)
    print("✓ Debug complete")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
