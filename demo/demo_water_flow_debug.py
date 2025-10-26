"""Enhanced debug script for water flow sensor analysis and troubleshooting.

This script provides in-depth debugging capabilities for water flow sensors,
including:
- Real-time MQTT data monitoring
- Domoticz counter history analysis
- Data consistency checks
- Trend analysis
- Error diagnostics

Usage:
    python demo_water_flow_debug.py

For detailed help:
    python demo_water_flow_debug.py --help
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from myuplink2mqtt.utils.domoticz_json_util import (
    create_domoticz_client,
    DomoticzClient,
)

logger = logging.getLogger(__name__)

# Configuration defaults
DOMOTICZ_HOST = os.getenv("DOMOTICZ_HOST", "10.0.0.2")
DOMOTICZ_PORT = int(os.getenv("DOMOTICZ_PORT", "80"))
DOMOTICZ_USERNAME = os.getenv("DOMOTICZ_USERNAME")
DOMOTICZ_PASSWORD = os.getenv("DOMOTICZ_PASSWORD")

MQTT_BROKER = os.getenv("MQTT_HOST", "10.0.0.2")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

WATER_FLOW_SENSOR_NAME = "Flow, hot water (BF4)"


def setup_logging(debug_mode=False):
    """Configure logging."""
    log_level = logging.DEBUG if debug_mode else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def get_domoticz_analysis(
    client: DomoticzClient, device_id: int
) -> Optional[Dict[str, Any]]:
    """Perform comprehensive Domoticz analysis for a device.

    Args:
        client: DomoticzClient instance.
        device_id: Device ID to analyze.

    Returns:
        Dict with analysis results.
    """
    print("\n" + "=" * 70)
    print("DOMOTICZ ANALYSIS")
    print("=" * 70)

    analysis = {
        "device_details": None,
        "counter_data_day": None,
        "counter_data_month": None,
        "counter_data_year": None,
        "status": "OK",
        "errors": [],
    }

    # Get device details
    device = client.get_device(device_id)
    if not device:
        analysis["status"] = "ERROR"
        analysis["errors"].append(f"Device {device_id} not found")
        print(f"✗ Device not found")
        return analysis

    analysis["device_details"] = device
    print(f"✓ Device Found: {device.get('Name')}")
    print(f"  ID: {device.get('idx')}")
    print(f"  Type: {device.get('Type')} / {device.get('SubType')}")
    print(f"  Status: {device.get('Status')}")
    print(f"  Last Update: {device.get('LastUpdate')}")

    # Check if data is being updated
    try:
        from datetime import datetime, timedelta

        last_update_str = device.get("LastUpdate")
        if last_update_str:
            last_update = datetime.strptime(last_update_str, "%Y-%m-%d %H:%M:%S")
            time_diff = datetime.now() - last_update
            print(f"  Data Age: {time_diff.total_seconds() / 60:.1f} minutes")

            if time_diff.total_seconds() > 3600:  # Older than 1 hour
                analysis["errors"].append(
                    f"Data is stale: last update was {time_diff.total_seconds() / 60:.0f} minutes ago"
                )
                print(f"  ⚠️  WARNING: Data is older than 1 hour")
            elif time_diff.total_seconds() > 600:  # Older than 10 minutes
                print(f"  ⚠️  Note: Data is {time_diff.total_seconds() / 60:.0f} minutes old")
    except Exception as e:
        logger.debug(f"Could not parse timestamp: {e}")

    # Get flow data for different ranges (using Percentage endpoint for actual data points)
    print("\n📊 Fetching Flow Data Points...")
    for range_type in ["day", "month", "year"]:
        try:
            endpoint = f"/json.htm?type=command&param=graph&sensor=Percentage&idx={device_id}&range={range_type}&method=1"
            response = client._make_request(endpoint)

            if response and response.get("status") == "OK" and "result" in response:
                result_data = response.get("result", [])
                analysis[f"flow_data_{range_type}"] = result_data
                
                if result_data:
                    # Calculate statistics from flow data
                    flow_values = [float(point.get("v", 0)) for point in result_data]
                    min_flow = min(flow_values) if flow_values else 0
                    max_flow = max(flow_values) if flow_values else 0
                    avg_flow = sum(flow_values) / len(flow_values) if flow_values else 0
                    total_flow = sum(flow_values)
                    
                    print(f"  ✓ {range_type.upper():>6} data: {len(result_data)} points | Min={min_flow:.2f} Max={max_flow:.2f} Avg={avg_flow:.4f} Total={total_flow:.2f} l/min")
                else:
                    print(f"  ✗ {range_type.upper():>6} data: No data points")
            else:
                status = response.get("status", "Unknown") if response else "No response"
                analysis["errors"].append(f"Failed to get {range_type} data: {status}")
                print(f"  ✗ {range_type.upper():>6} data: Error")

        except Exception as e:
            analysis["errors"].append(f"Exception fetching {range_type}: {e}")
            print(f"  ✗ {range_type.upper():>6} data: Exception - {e}")

    return analysis


def calculate_flow_rates(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate flow statistics from flow data points.

    Args:
        analysis: Analysis data from Domoticz with flow_data_* keys.

    Returns:
        Dict with flow rate statistics.
    """
    print("\n" + "=" * 70)
    print("FLOW RATE ANALYSIS")
    print("=" * 70)

    flows = {
        "daily_stats": None,
        "monthly_stats": None,
        "yearly_stats": None,
    }

    # Process daily flow data
    day_data = analysis.get("flow_data_day", [])
    if day_data:
        flow_values = [float(point.get("v", 0)) for point in day_data]
        if flow_values:
            min_flow = min(flow_values)
            max_flow = max(flow_values)
            avg_flow = sum(flow_values) / len(flow_values)
            total_flow = sum(flow_values)
            
            flows["daily_stats"] = {
                "points": len(flow_values),
                "min": min_flow,
                "max": max_flow,
                "avg": avg_flow,
                "total": total_flow,
            }
            
            print(f"\nDaily Flow (today):")
            print(f"  Data Points: {len(flow_values)}")
            print(f"  Min Flow: {min_flow:.4f} l/min")
            print(f"  Max Flow: {max_flow:.4f} l/min")
            print(f"  Average Flow: {avg_flow:.4f} l/min")
            print(f"  Total: {total_flow:.2f} l (cumulative)")

    # Process monthly flow data
    month_data = analysis.get("flow_data_month", [])
    if month_data and len(month_data) > 0:
        flow_values = [float(point.get("v", 0)) for point in month_data]
        if flow_values:
            min_flow = min(flow_values)
            max_flow = max(flow_values)
            avg_flow = sum(flow_values) / len(flow_values)
            total_flow = sum(flow_values)
            
            flows["monthly_stats"] = {
                "points": len(flow_values),
                "min": min_flow,
                "max": max_flow,
                "avg": avg_flow,
                "total": total_flow,
            }
            
            print(f"\nMonthly Flow (this month):")
            print(f"  Data Points: {len(flow_values)}")
            print(f"  Min Flow: {min_flow:.4f} l/min")
            print(f"  Max Flow: {max_flow:.4f} l/min")
            print(f"  Average Flow: {avg_flow:.4f} l/min")
            print(f"  Total: {total_flow:.2f} l (cumulative)")

    # Process yearly flow data
    year_data = analysis.get("flow_data_year", [])
    if year_data and len(year_data) > 0:
        flow_values = [float(point.get("v", 0)) for point in year_data]
        if flow_values:
            min_flow = min(flow_values)
            max_flow = max(flow_values)
            avg_flow = sum(flow_values) / len(flow_values)
            total_flow = sum(flow_values)
            
            flows["yearly_stats"] = {
                "points": len(flow_values),
                "min": min_flow,
                "max": max_flow,
                "avg": avg_flow,
                "total": total_flow,
            }
            
            print(f"\nYearly Flow (this year):")
            print(f"  Data Points: {len(flow_values)}")
            print(f"  Min Flow: {min_flow:.4f} l/min")
            print(f"  Max Flow: {max_flow:.4f} l/min")
            print(f"  Average Flow: {avg_flow:.4f} l/min")
            print(f"  Total: {total_flow:.2f} l (cumulative)")

    return flows


def check_data_consistency(analysis: Dict[str, Any], flows: Dict[str, Any]):
    """Check for data consistency and anomalies.

    Args:
        analysis: Analysis data.
        flows: Flow rate calculations.
    """
    print("\n" + "=" * 70)
    print("DATA CONSISTENCY CHECKS")
    print("=" * 70)

    checks = {
        "passed": 0,
        "warnings": 0,
        "errors": 0,
        "issues": [],
    }

    # Check 1: Device is being updated
    device = analysis.get("device_details", {})
    last_update = device.get("LastUpdate")

    if last_update:
        try:
            from datetime import datetime, timedelta

            last_update_dt = datetime.strptime(last_update, "%Y-%m-%d %H:%M:%S")
            time_diff = datetime.now() - last_update_dt

            if time_diff.total_seconds() < 60:
                print("✓ PASS: Data is being updated in real-time (< 1 minute)")
                checks["passed"] += 1
            elif time_diff.total_seconds() < 600:
                print("⚠ WARN: Data is recent but not real-time")
                checks["warnings"] += 1
                checks["issues"].append("Data updates not continuous")
            else:
                print("✗ FAIL: Data is stale")
                checks["errors"] += 1
                checks["issues"].append("Data not being updated")
        except Exception as e:
            print(f"? SKIP: Could not check update frequency: {e}")
    else:
        print("? SKIP: No last update timestamp")

    # Check 2: Flow data has data points
    day_flow_data = analysis.get("flow_data_day", [])
    if day_flow_data and len(day_flow_data) > 0:
        print(f"✓ PASS: Flow data has {len(day_flow_data)} data points")
        checks["passed"] += 1
    else:
        print("✗ FAIL: No flow data points available")
        checks["errors"] += 1
        checks["issues"].append("No flow data points from API")

    # Check 3: Flow rates are reasonable
    daily_stats = flows.get("daily_stats")
    if daily_stats and daily_stats.get("max", 0) > 0:
        max_flow = daily_stats.get("max", 0)
        avg_flow = daily_stats.get("avg", 0)
        print(f"✓ PASS: Flow data shows activity: avg={avg_flow:.4f}, max={max_flow:.4f} l/min")
        checks["passed"] += 1
    elif daily_stats and daily_stats.get("max", 0) == 0:
        print("⚠ WARN: No water flow detected today")
        checks["warnings"] += 1
        checks["issues"].append("Zero flow might indicate no heating activity")
    else:
        print("⚠ WARN: Could not calculate flow statistics")
        checks["warnings"] += 1

    # Check 4: Data points are consistent
    day_flow_values = []
    if day_flow_data:
        try:
            day_flow_values = [float(point.get("v", 0)) for point in day_flow_data]
            if all(v >= 0 for v in day_flow_values):
                print(f"✓ PASS: All flow values are valid (non-negative)")
                checks["passed"] += 1
            else:
                print("✗ FAIL: Found negative flow values")
                checks["errors"] += 1
                checks["issues"].append("Negative flow values detected")
        except (ValueError, TypeError) as e:
            print(f"✗ FAIL: Could not parse flow values: {e}")
            checks["errors"] += 1
            checks["issues"].append("Invalid flow data format")

    # Summary
    print("\n" + "-" * 70)
    print(f"Checks Passed: {checks['passed']}")
    print(f"Warnings: {checks['warnings']}")
    print(f"Errors: {checks['errors']}")

    if checks["issues"]:
        print("\nIssues Found:")
        for issue in checks["issues"]:
            print(f"  - {issue}")

    return checks


def generate_mqtt_discovery_config(
    device: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Generate Home Assistant MQTT discovery config based on device.

    Args:
        device: Domoticz device details.

    Returns:
        MQTT discovery payload.
    """
    print("\n" + "=" * 70)
    print("MQTT AUTO-DISCOVERY CONFIG")
    print("=" * 70)

    device_id = device.get("idx")
    device_name = device.get("Name")
    hw_name = device.get("HardwareName")

    if not device_id:
        print("✗ Cannot generate config: no device ID")
        return None

    config = {
        "dev": {
            "ids": f"domoticz_{device_id}",
            "name": device_name,
            "mf": "Domoticz",
            "mdl": device.get("Type"),
        },
        "o": {
            "name": "myUplink2mqtt",
            "sw": "1.0.0",
            "url": "https://github.com/j-b-n/myUplink2mqtt",
        },
        "unique_id": f"domoticz_{device_id}_flow",
        "name": device_name,
        "state_topic": f"myuplink/domoticz/{device_id}/state",
        "unit_of_measurement": "l/min",
        "device_class": "volume",
        "value_template": "{{ value_json.flow }}",
        "availability_topic": f"myuplink/domoticz/{device_id}/available",
    }

    print("\nGenerated MQTT Discovery Config:")
    print(json.dumps(config, indent=2))

    print("\nTo publish this config to MQTT:")
    print(f'mosquitto_pub -r -h <broker> -t "homeassistant/sensor/domoticz_{device_id}/config" \\')
    print(f"  -m '{json.dumps(config)}'")

    return config


def diagnose_issues(analysis: Dict[str, Any]) -> List[str]:
    """Diagnose potential issues based on analysis.

    Args:
        analysis: Analysis data.

    Returns:
        List of diagnostic messages.
    """
    print("\n" + "=" * 70)
    print("DIAGNOSTIC REPORT")
    print("=" * 70)

    diagnostics = []

    if analysis.get("errors"):
        print(f"\n✗ {len(analysis['errors'])} Error(s) Found:")
        for error in analysis["errors"]:
            print(f"  - {error}")
            diagnostics.append(error)

    device = analysis.get("device_details", {})

    # Check 1: Hardware type
    hw_name = device.get("HardwareName", "")
    if "MQTT" in hw_name:
        print("\n✓ Device is connected via MQTT (good for myUplink2mqtt)")
    else:
        print(f"\n⚠ Device is connected via: {hw_name}")
        if hw_name not in ["MQTT"]:
            diagnostics.append(
                f"Device uses {hw_name}, not MQTT. Consider if this affects data flow."
            )

    # Check 2: Device status
    status = device.get("Status")
    if status is None or status == "None":
        print("ℹ  Device status is 'None' (normal for waterflow sensors)")
    else:
        print(f"ℹ  Device status: {status}")

    # Check 3: Hidden/protected status
    hidden = device.get("Hidden", 0)
    protected = device.get("Protected", False)

    if hidden:
        print("⚠ Device is hidden in Domoticz")
        diagnostics.append("Device is hidden - may affect visibility")

    if protected:
        print("ℹ  Device is protected")

    if not diagnostics:
        print("\n✓ No issues detected!")

    return diagnostics


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Advanced water flow sensor debugging for Domoticz",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic analysis
  python demo_water_flow_debug.py

  # With specific device ID
  python demo_water_flow_debug.py --device-id 9185

  # Debug mode with detailed logging
  python demo_water_flow_debug.py --debug
        """,
    )

    parser.add_argument(
        "--domoticz-host",
        default=DOMOTICZ_HOST,
        help=f"Domoticz server (default: {DOMOTICZ_HOST})",
    )
    parser.add_argument(
        "--domoticz-port",
        type=int,
        default=DOMOTICZ_PORT,
        help=f"Domoticz port (default: {DOMOTICZ_PORT})",
    )
    parser.add_argument(
        "--device-id",
        type=int,
        help="Device ID (if not provided, searches by name)",
    )
    parser.add_argument(
        "--sensor-name",
        default=WATER_FLOW_SENSOR_NAME,
        help=f"Sensor name (default: {WATER_FLOW_SENSOR_NAME})",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()
    setup_logging(debug_mode=args.debug)

    print("\n" + "=" * 70)
    print("WATER FLOW SENSOR ADVANCED DEBUGGING")
    print("=" * 70)
    print(f"Domoticz: {args.domoticz_host}:{args.domoticz_port}")

    # Create client
    client = create_domoticz_client(
        args.domoticz_host,
        args.domoticz_port,
        use_https=False,
        username=DOMOTICZ_USERNAME,
        password=DOMOTICZ_PASSWORD,
    )

    if not client:
        print("✗ Failed to connect to Domoticz")
        return 1

    print("✓ Connected to Domoticz\n")

    # Find device
    device_id = args.device_id
    if not device_id:
        device = client.get_device_by_name(args.sensor_name)
        if not device:
            print(f"✗ Device '{args.sensor_name}' not found")
            return 1
        device_id = device.get("idx")

    # Run analysis
    analysis = get_domoticz_analysis(client, device_id)

    if analysis.get("status") != "OK":
        print("\n✗ Analysis failed!")
        return 1

    flows = calculate_flow_rates(analysis)
    checks = check_data_consistency(analysis, flows)
    diagnostics = diagnose_issues(analysis)

    # Generate MQTT config
    device = analysis.get("device_details")
    if device:
        generate_mqtt_discovery_config(device)

    # Final summary
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)

    if checks["errors"] > 0:
        print(f"\n⚠ {checks['errors']} critical error(s) detected")
        return 1
    elif checks["warnings"] > 0:
        print(f"\n⚠ {checks['warnings']} warning(s) detected")
    else:
        print("\n✓ All checks passed!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
