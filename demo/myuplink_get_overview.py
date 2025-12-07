"""Test script for displaying device overview information from myUplink API."""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from myuplink2mqtt.utils.myuplink_utils import (
    check_oauth_prerequisites,
    create_api_client,
    get_device_details,
    get_device_points,
    get_systems,
)

# Logger initialization
logger = logging.getLogger(__name__)

# Overview parameters to display (based on common myUplink device parameters)
OVERVIEW_PARAMETERS = [
    "40004",  # BT1 - Current outdoor temperature
    "40940",  # Calculated supply climate system 1
    "40005",  # BT2 - Supply heating
    "40006",  # BT3 - Return heating
    "40013",  # HMIL - Relative humidity Room
    "40008",  # BT69.1 - Primary return heating
    "49999",  # QN11.1 - Exercising
    "40014",  # BT38 - Hot water out
    "40015",  # BT69.2 - Primary out hot water
    "40016",  # BF4 - Flow, hot water
    "50000",  # QN11.2 - Exercising
]


def format_parameter_value(point):
    """Format parameter value with appropriate units."""
    value = point["value"]
    parameter_name = point["parameterName"]

    # Add units based on parameter name patterns
    if "temp" in parameter_name.lower() or "BT" in parameter_name:
        return f"{value} °C"
    if "humid" in parameter_name.lower():
        return f"{value} rh%"
    if "flow" in parameter_name.lower():
        return f"{value} l/m"

    return str(value)


async def display_device_overview(api, device_id):  # noqa: C901
    """Display overview information for a device."""
    # Get detailed device information
    device_data = await get_device_details(api, device_id)
    if device_data is None:
        logger.info(f"Could not retrieve device details for {device_id}")
        return False

    logger.info(f"Overview for {device_data['product']['name']}")
    logger.info("=" * 50)

    # First, get all available parameters to see what's actually available
    all_points_data = await get_device_points(api, device_id)

    if all_points_data is None:
        logger.info(f"Could not retrieve data points for {device_id}")
        return False

    logger.info(f"Device has {len(all_points_data)} total parameters available")

    # Filter for overview-relevant parameters and deduplicate
    overview_points = []
    seen_labels = set()

    # Define parameter mappings
    param_mappings = {
        "BT1": "Current outd temp (BT1)",
        "BT2": "Supply heating (BT2)",
        "BT3": "Return heating (BT3)",
        "BT38": "Hot water out (BT38)",
        "BT69.1": "Primary return heating (BT69.1)",
        "BT69.2": "Primary out hot water (BT69.2)",
        "BF4": "Flow, hot water (BF4)",
        "QN11.1": "QN11.1 exercising",
        "QN11.2": "QN11.2 exercising",
    }
    for point in all_points_data:
        param_name = point["parameterName"]
        # Clean up soft hyphens and other encoding issues
        param_name = param_name.replace("\u00ad", "")  # Remove soft hyphens entirely

        # Look for parameters that match common overview patterns
        if any(
            keyword in param_name.upper()
            for keyword in [
                "BT1",
                "BT2",
                "BT3",
                "BT38",
                "BT69",
                "BF4",
                "QN11",
                "TEMP",
                "HUMID",
                "FLOW",
                "OUTDOOR",
                "SUPPLY",
                "RETURN",
                "HOT WATER",
            ]
        ):
            # Create a label for deduplication
            label = None
            for key, display_label in param_mappings.items():
                if key in param_name:
                    label = display_label
                    break

            if label is None:
                # For other parameters, use a simplified name
                if "HUMID" in param_name.upper():
                    label = "Relative humidity Room humid. HMIL"
                else:
                    label = param_name
                    # Clean up any remaining encoding issues in the label
                    label = label.replace("\u00ad", "")
            # Only add if we haven't seen this label before
            if label not in seen_labels:
                overview_points.append((point, label))
                seen_labels.add(label)

    if not overview_points:
        logger.info("No overview parameters found for this device.")
        logger.info("Available parameters:")
        for point in all_points_data[:10]:  # Show first 10 parameters as examples
            logger.info(f"  {point['parameterId']} | {point['parameterName']}")
        if len(all_points_data) > 10:
            logger.info(f"  ... and {len(all_points_data) - 10} more")
        return True

    logger.info(f"Found {len(overview_points)} overview parameters:")
    # Display parameters in a formatted overview
    for point, label in overview_points:
        formatted_value = format_parameter_value(point)
        logger.info(f"{label}: {formatted_value}")

    return True


async def test_get_overview():
    """Test retrieving and displaying device overview information."""
    session = None
    try:
        session, api, _token_manager = await create_api_client()

        systems = await get_systems(api)

        if systems is None:
            return False

        logger.info(f"Found {len(systems)} system(s)")
        for system in systems:
            logger.info(f"System: {system['name']}")
            logger.info(f"Devices: {len(system['devices'])}")
            for device in system["devices"]:
                device_id = device["id"]
                success = await display_device_overview(api, device_id)
                if not success:
                    logger.error(f"Failed to get overview for device {device_id}")
        return True

    except (OSError, ValueError, KeyError) as e:
        logger.error(f"Overview test failed: {e}")
        return False
    finally:
        if session:
            await session.close()


async def main():
    """Run the get overview test."""
    logger.info("Testing myUplink API - Get Overview...")
    logger.info("=" * 50)

    # Check OAuth prerequisites
    logger.info("Checking OAuth prerequisites...")
    can_proceed, error_msg = check_oauth_prerequisites()

    if not can_proceed:
        logger.info("❌ OAuth prerequisites not met:")
        logger.error(error_msg)
        logger.info("Test Summary:")
        logger.info("OAuth Prerequisites: ✗")
        logger.info("Overview Test: Skipped")
        return

    # Test: Get Overview
    logger.info("Retrieving device overview information...")
    overview_success = await test_get_overview()
    # Summary
    logger.info("Test Summary:")
    logger.info("OAuth Prerequisites: ✓")
    logger.info(f"Overview Retrieval: {'✓' if overview_success else '✗'}")

    if overview_success:
        logger.info("Overview test passed!")
    else:
        logger.error("Overview test failed. Check the output above for details.")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    asyncio.run(main())
