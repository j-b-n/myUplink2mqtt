"""Test script for retrieving system and device names from myUplink API."""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from myuplink2mqtt.utils.myuplink_utils import (
    check_oauth_prerequisites,
    create_oauth_session,
    get_device_details,
    get_manufacturer,
    get_systems,
)

# Logger initialization
logger = logging.getLogger(__name__)


async def test_get_names():
    """Test retrieving and displaying system and device names."""
    try:
        # Create OAuth session
        myuplink = create_oauth_session()

        # Get systems
        systems = get_systems(myuplink)

        if systems is None:
            return False

        logger.info(f"Found {len(systems)} system(s):")

        for system in systems:
            system_id = system["systemId"]
            system_name = system["name"]
            logger.info(f"System ID: {system_id}")
            logger.info(f"System Name: {system_name}")
            logger.info(f"Country: {system['country']}")
            logger.info(f"Number of devices: {len(system['devices'])}")

            # Get device names
            logger.info("Devices:")
            for device in system["devices"]:
                device_id = device["id"]
                logger.info(f"  Device ID: {device_id}")

                # Get detailed device information for product name
                device_details = get_device_details(myuplink, device_id)
                if device_details:
                    if "product" in device_details and "name" in device_details["product"]:
                        product_name = device_details["product"]["name"]
                        logger.info(f"  Product: {product_name}")
                        logger.info(f"  Manufacturer: {get_manufacturer(device_details)}")
                    else:
                        logger.info("  Product: (unable to retrieve)")
                        logger.info("  Manufacturer: Unknown")
                else:
                    logger.info("  Device details: (unable to retrieve)")

            logger.info("-" * 50)

        return True

    except (OSError, ValueError, KeyError) as e:
        logger.error(f"Name retrieval test failed: {e}")
        return False


async def main():
    """Run the get names test."""
    logger.info("Testing myUplink API - Get Names...")
    logger.info("=" * 50)

    # Check OAuth prerequisites
    logger.info("Checking OAuth prerequisites...")
    can_proceed, error_msg = check_oauth_prerequisites()

    if not can_proceed:
        logger.info("❌ OAuth prerequisites not met:")
        logger.error(error_msg)
        logger.info("Test Summary:")
        logger.info("OAuth Prerequisites: ✗")
        logger.info("Name Retrieval Test: Skipped")
        return

    # Test: Get Names
    logger.info("Retrieving system and device names...")
    names_success = await test_get_names()

    # Summary
    logger.info("Test Summary:")
    logger.info("OAuth Prerequisites: ✓")
    logger.info(f"Name Retrieval: {'✓' if names_success else '✗'}")

    if names_success:
        logger.info("Name retrieval test passed!")
    else:
        logger.info("Name retrieval test failed. Check the output above for details.")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    asyncio.run(main())
