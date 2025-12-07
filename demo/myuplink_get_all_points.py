"""Test script for retrieving all data points from myUplink API devices."""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from myuplink2mqtt.utils.myuplink_utils import (
    check_oauth_prerequisites,
    create_api_client,
    format_parameter_value,
    get_device_details,
    get_device_points,
    get_parameter_display_name,
    get_systems,
)

# Logger initialization
logger = logging.getLogger(__name__)


async def test_get_all_points():
    """Test retrieving all data points from devices."""
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

                # Get detailed device information
                device_data = await get_device_details(api, device_id)
                if device_data is None:
                    logger.info(f"Could not retrieve device details for {device_id}")
                    continue

                logger.info(f"Device: {device_data['product']['name']} ({device_id})")
                logger.info("=" * 60)

                # Get ALL data points for this device with proper labels
                all_points_data = await get_device_points(api, device_id)

                if all_points_data is None:
                    logger.info(f"Could not retrieve data points for {device_id}")
                    continue

                logger.info(f"Total parameters: {len(all_points_data)}")
                # Display all parameters with their values
                for point in all_points_data:
                    parameter_name = get_parameter_display_name(point)

                    formatted_value = format_parameter_value(point, display_name=parameter_name)
                    logger.info(f"{parameter_name}: {formatted_value}")
        return True

    except (OSError, ValueError, KeyError) as e:
        logger.error(f"All points test failed: {e}")
        return False
    finally:
        if session:
            await session.close()


async def main():
    """Run the get all points test."""
    logger.info("Testing myUplink API - Get All Points...")
    logger.info("=" * 50)

    # Check OAuth prerequisites
    logger.info("Checking OAuth prerequisites...")
    can_proceed, error_msg = check_oauth_prerequisites()

    if not can_proceed:
        logger.info("❌ OAuth prerequisites not met:")
        logger.error(error_msg)
        logger.info("Test Summary:")
        logger.info("OAuth Prerequisites: ✗")
        logger.info("All Points Test: Skipped")
        return

    # Test: Get All Points
    logger.info("Retrieving all data points from devices...")
    all_points_success = await test_get_all_points()
    # Summary
    logger.info("Test Summary:")
    logger.info("OAuth Prerequisites: ✓")
    logger.info(f"All Points Retrieval: {'✓' if all_points_success else '✗'}")

    if all_points_success:
        logger.info("All points test passed!")
    else:
        logger.error("All points test failed. Check the output above for details.")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    asyncio.run(main())
