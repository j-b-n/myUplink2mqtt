"""Test script for testing specific data points from myUplink API devices."""

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
    test_api_availability,
)

# Logger initialization
logger = logging.getLogger(__name__)

# Specific parameters to test (based on example_specific_points.py)
PARAMETERS = ["40004", "40940", "40005"]


async def process_device_points(api, device_id):
    """Process and display specific data points for a device."""
    # Get detailed device information first
    device_data = await get_device_details(api, device_id)
    if device_data is None:
        logger.info(f"Device {device_id}: Could not retrieve device details")
        return

    logger.info(f"Device id: {device_data['id']}")
    logger.info(f"Device productName: {device_data['product']['name']}")
    logger.info(f"Device productSerialNumber: {device_data['product']['serialNumber']}")
    logger.info(f"Device firmwareCurrent: {device_data['firmware']['currentFwVersion']}")
    logger.info(f"Device firmwareDesired: {device_data['firmware']['desiredFwVersion']}")
    logger.info(f"Device connectionState: {device_data.get('connectionState', 'Unknown')}")

    # Get specific data points for this device
    points_data = await get_device_points(api, device_id, PARAMETERS)

    if points_data is None:
        logger.info(f"Device {device_id}: Could not retrieve data points")
        return

    logger.info(f"Retrieved {len(points_data)} specific data points:")

    for point in points_data:
        parameter_id = point["parameterId"]
        parameter_name = point["parameterName"]
        value = point["value"]
        logger.info(f"  {parameter_id} | {parameter_name} | {value}")


async def test_specific_points():
    """Test OAuth authentication and retrieve specific data points from devices."""
    session = None
    try:
        session, api, _token_manager = await create_api_client()

        systems = await get_systems(api)

        if systems is None:
            return False

        count = len(systems)
        logger.info(f"Successfully retrieved {count} system(s)")

        for system in systems:
            logger.info(f"System id: {system['systemId']}")
            logger.info(f"System name: {system['name']}")
            logger.info(f"No of devices in system: {len(system['devices'])}")

            for device_info in system["devices"]:
                device_id = device_info["id"]
                await process_device_points(api, device_id)
        return True

    except (OSError, ValueError, KeyError) as e:
        logger.error(f"OAuth test failed: {e}")
        return False
    finally:
        if session:
            await session.close()


async def main():
    """Run all tests."""
    logger.info("Testing myUplink API - Specific Points Test")
    logger.info("=" * 50)

    # Test 1: API Availability
    logger.info("Test 1: API Availability")
    api_available = await test_api_availability()
    # Check OAuth prerequisites before attempting OAuth test
    logger.info("Checking OAuth prerequisites...")
    can_proceed, error_msg = check_oauth_prerequisites()

    if not can_proceed:
        logger.info("❌ OAuth prerequisites not met:")
        logger.error(error_msg)
        # Summary
        logger.info("Test Summary:")
        logger.info(f"API Available: {'✓' if api_available else '✗'}")
        logger.info("OAuth Prerequisites: ✗")
        logger.info("Specific Points Test: Skipped")

        if api_available:
            logger.info("API is available but OAuth cannot be tested due to missing prerequisites.")
        else:
            logger.error("Both API availability and OAuth tests failed.")

        # Exit early
        return

    # Test 2: Specific Points Test
    logger.info("Test 2: Specific Data Points Test")
    logger.info(f"Testing with parameters: {PARAMETERS}")
    points_success = await test_specific_points()
    # Summary
    logger.info("Test Summary:")
    logger.info(f"API Available: {'✓' if api_available else '✗'}")
    logger.info("OAuth Prerequisites: ✓")
    logger.info(f"Specific Points Test: {'✓' if points_success else '✗'}")

    if api_available and points_success:
        logger.info("All tests passed!")
    else:
        logger.error("Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    asyncio.run(main())
