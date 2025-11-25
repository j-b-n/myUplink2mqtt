"""Demo script for querying Domoticz via JSON API.

This script demonstrates how to fetch information from a Domoticz server
using the JSON API, including:
- Server status and information
- Device lists and details
- Device states and properties
- Scene information
- Device filtering and searching

Usage:
    python demo_domoticz_json.py --domoticz-host 192.168.1.100

Example with authentication:
    python demo_domoticz_json.py \\
        --domoticz-host 192.168.1.100 \\
        --domoticz-port 8080 \\
        --domoticz-username admin \\
        --domoticz-password password

For more information, see docs/DOMOTICZ_JSON_UTIL.md
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from myuplink2mqtt.utils.domoticz_json_util import (
    create_domoticz_client,
)

# Configure logging
logger = logging.getLogger(__name__)

# Domoticz API Configuration defaults
DOMOTICZ_HOST = os.getenv("DOMOTICZ_HOST")
DOMOTICZ_PORT = int(os.getenv("DOMOTICZ_PORT", "8080"))
DOMOTICZ_USERNAME = os.getenv("DOMOTICZ_USERNAME")
DOMOTICZ_PASSWORD = os.getenv("DOMOTICZ_PASSWORD")


def setup_logging(debug_mode=False, silent_mode=False):
    """Configure logging with appropriate level and format.

    Args:
        debug_mode (bool): Enable debug level logging.
        silent_mode (bool): Enable silent mode (WARNING level only).

    """
    if silent_mode:
        log_level = logging.WARNING
    elif debug_mode:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)

    logger.setLevel(log_level)


def parse_arguments():
    """Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.

    """
    parser = argparse.ArgumentParser(
        description="Domoticz JSON API Demo - Query Domoticz server information"
    )

    parser.add_argument(
        "--domoticz-host",
        metavar="HOST",
        default=DOMOTICZ_HOST,
        help="Domoticz host/IP (env: DOMOTICZ_HOST)",
    )

    parser.add_argument(
        "--domoticz-port",
        type=int,
        default=DOMOTICZ_PORT,
        metavar="PORT",
        help="Domoticz port (default: 8080, env: DOMOTICZ_PORT)",
    )

    parser.add_argument(
        "--domoticz-username",
        metavar="USERNAME",
        default=DOMOTICZ_USERNAME,
        help="Domoticz HTTP Basic Auth username (env: DOMOTICZ_USERNAME)",
    )

    parser.add_argument(
        "--domoticz-password",
        metavar="PASSWORD",
        default=DOMOTICZ_PASSWORD,
        help="Domoticz HTTP Basic Auth password (env: DOMOTICZ_PASSWORD)",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all information (status, devices, scenes)",
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Show server status only",
    )

    parser.add_argument(
        "--devices",
        action="store_true",
        help="Show all devices",
    )

    parser.add_argument(
        "--device",
        type=int,
        metavar="ID",
        help="Show details for specific device ID",
    )

    parser.add_argument(
        "--device-name",
        metavar="NAME",
        help="Find and show device by name",
    )

    parser.add_argument(
        "--mqtt-devices",
        action="store_true",
        help="Show MQTT-based devices only",
    )

    parser.add_argument(
        "--scenes",
        action="store_true",
        help="Show all scenes",
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    parser.add_argument(
        "-s",
        "--silent",
        action="store_true",
        help="Silent mode - errors only",
    )

    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    return parser.parse_args()


def show_banner():
    """Display application banner."""
    banner = [
        "",
        "=" * 80,
        "Domoticz JSON API Query Tool",
        "=" * 80,
        "",
    ]

    for line in banner:
        logger.info(line)


def show_server_status(client):
    """Show Domoticz server status.

    Args:
        client: DomoticzClient instance.

    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 SERVER STATUS")
    logger.info("=" * 80)
    logger.info("")

    status = client.get_status()
    if not status:
        logger.error("Failed to get server status")
        return

    logger.info(f"Server Time: {status.get('ServerTime', 'N/A')}")
    logger.info(f"Status: {status.get('status', 'N/A')}")

    # Get version information
    version = client.get_version()
    if version:
        logger.info(f"Version: {version.get('version', 'N/A')}")
        if "build" in version:
            logger.info(f"Build: {version.get('build', 'N/A')}")

    logger.info("")


def show_devices(client, json_output=False):
    """Show all devices.

    Args:
        client: DomoticzClient instance.
        json_output: Output as JSON if True.

    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("📱 ALL DEVICES")
    logger.info("=" * 80)
    logger.info("")

    devices = client.get_devices()
    if not devices:
        logger.info("No devices found")
        return

    if json_output:
        logger.info(json.dumps(devices, indent=2))
        return

    logger.info(f"Total Devices: {len(devices)}\n")

    for idx, device in enumerate(devices, 1):
        logger.info(f"{idx}. {device.get('Name', 'Unknown')}")
        logger.info(f"   ID: {device.get('idx')}")
        logger.info(f"   Type: {device.get('Type')} / {device.get('SubType')}")
        logger.info(f"   Status: {device.get('Status')}")
        logger.info(f"   Hardware: {device.get('HardwareName')}")
        logger.info(f"   Last Update: {device.get('LastUpdate')}")
        logger.info("")


def show_device_details(client, device_id, json_output=False):
    """Show details for a specific device.

    Args:
        client: DomoticzClient instance.
        device_id: Device ID to query.
        json_output: Output as JSON if True.

    """
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"📱 DEVICE #{device_id}")
    logger.info("=" * 80)
    logger.info("")

    device = client.get_device(device_id)
    if not device:
        logger.warning(f"Device {device_id} not found")
        return

    if json_output:
        logger.info(json.dumps(device, indent=2))
        return

    logger.info(f"Name: {device.get('Name')}")
    logger.info(f"ID: {device.get('idx')}")
    logger.info(f"Type: {device.get('Type')}")
    logger.info(f"SubType: {device.get('SubType')}")
    logger.info(f"Status: {device.get('Status')}")
    logger.info(f"Hardware: {device.get('HardwareName')}")
    logger.info(f"Description: {device.get('Description', 'N/A')}")
    logger.info(f"Last Update: {device.get('LastUpdate')}")
    logger.info(f"Protected: {device.get('Protected')}")
    logger.info("")


def show_device_by_name(client, device_name, json_output=False):
    """Show device by name.

    Args:
        client: DomoticzClient instance.
        device_name: Device name to search for.
        json_output: Output as JSON if True.

    """
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"🔍 SEARCH: {device_name}")
    logger.info("=" * 80)
    logger.info("")

    device = client.get_device_by_name(device_name)
    if not device:
        logger.warning(f"Device '{device_name}' not found")
        return

    if json_output:
        logger.info(json.dumps(device, indent=2))
        return

    logger.info(f"Name: {device.get('Name')}")
    logger.info(f"ID: {device.get('idx')}")
    logger.info(f"Type: {device.get('Type')}")
    logger.info(f"SubType: {device.get('SubType')}")
    logger.info(f"Status: {device.get('Status')}")
    logger.info(f"Hardware: {device.get('HardwareName')}")
    logger.info(f"Last Update: {device.get('LastUpdate')}")
    logger.info("")


def show_mqtt_devices(client, json_output=False):
    """Show MQTT-based devices.

    Args:
        client: DomoticzClient instance.
        json_output: Output as JSON if True.

    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("🌐 MQTT-BASED DEVICES")
    logger.info("=" * 80)
    logger.info("")

    devices = client.get_devices()
    if not devices:
        logger.info("No devices found")
        return

    mqtt_devices = [d for d in devices if "MQTT" in d.get("HardwareName", "")]

    if not mqtt_devices:
        logger.info("No MQTT-based devices found")
        return

    if json_output:
        logger.info(json.dumps(mqtt_devices, indent=2))
        return

    logger.info(f"Total MQTT Devices: {len(mqtt_devices)}\n")

    for idx, device in enumerate(mqtt_devices, 1):
        logger.info(f"{idx}. {device.get('Name')}")
        logger.info(f"   ID: {device.get('idx')}")
        logger.info(f"   Type: {device.get('Type')} / {device.get('SubType')}")
        logger.info(f"   Status: {device.get('Status')}")
        logger.info(f"   Last Update: {device.get('LastUpdate')}")
        logger.info("")


def show_scenes(client, json_output=False):
    """Show all scenes.

    Args:
        client: DomoticzClient instance.
        json_output: Output as JSON if True.

    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("🎬 SCENES")
    logger.info("=" * 80)
    logger.info("")

    scenes = client.get_scenes()
    if not scenes:
        logger.info("No scenes found")
        return

    if json_output:
        logger.info(json.dumps(scenes, indent=2))
        return

    logger.info(f"Total Scenes: {len(scenes)}\n")

    for idx, scene in enumerate(scenes, 1):
        logger.info(f"{idx}. {scene.get('Name')}")
        logger.info(f"   ID: {scene.get('idx')}")
        logger.info(f"   Activate: {scene.get('Activate')}")
        logger.info("")


def execute_queries(client, args):
    """Execute queries based on command-line arguments.

    Args:
        client: DomoticzClient instance.
        args: Parsed command-line arguments.

    """
    # Determine what to show
    show_something = False

    if args.all:
        show_server_status(client)
        show_devices(client, args.json)
        show_scenes(client, args.json)
        show_something = True

    if args.status:
        show_server_status(client)
        show_something = True

    if args.devices:
        show_devices(client, args.json)
        show_something = True

    if args.device:
        show_device_details(client, args.device, args.json)
        show_something = True

    if args.device_name:
        show_device_by_name(client, args.device_name, args.json)
        show_something = True

    if args.mqtt_devices:
        show_mqtt_devices(client, args.json)
        show_something = True

    if args.scenes:
        show_scenes(client, args.json)
        show_something = True

    # If nothing specified, show default view
    if not show_something:
        show_server_status(client)
        show_devices(client, args.json)
        show_scenes(client, args.json)


def main():
    """Main entry point."""
    args = parse_arguments()

    # Setup logging
    setup_logging(debug_mode=args.debug, silent_mode=args.silent)

    # Validate required argument
    if not args.domoticz_host:
        logger.error("Domoticz host is required (--domoticz-host or DOMOTICZ_HOST)")
        sys.exit(1)

    # Show banner
    show_banner()

    # Create client
    logger.info(f"Connecting to Domoticz at {args.domoticz_host}:{args.domoticz_port}...")

    client = create_domoticz_client(
        args.domoticz_host,
        args.domoticz_port,
        False,
        args.domoticz_username,
        args.domoticz_password,
    )

    if client is None:
        logger.error(f"Failed to connect to Domoticz at {args.domoticz_host}:{args.domoticz_port}")
        sys.exit(1)

    logger.info("✓ Connected to Domoticz\n")

    try:
        # Execute queries
        execute_queries(client, args)

        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ Query completed successfully")
        logger.info("=" * 80)
        logger.info("")

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
