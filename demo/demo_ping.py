"""Test script for myUplink API connectivity and OAuth authentication."""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from myuplink2mqtt.utils.myuplink_utils import (
    check_oauth_prerequisites,
    create_oauth_session,
    get_device_brands,
    get_systems,
    test_api_availability,
)

# Logger initialization
logger = logging.getLogger(__name__)


async def test_oauth_and_get_systems():
    """Test OAuth authentication and retrieve systems using requests_oauthlib."""
    try:
        # Create OAuth session
        myuplink = create_oauth_session()

        # Get systems
        systems = get_systems(myuplink)

        if systems is None:
            return False

        count = len(systems)
        logger.info(f"Successfully retrieved {count} system(s)")

        for system in systems:
            logger.info(f"System ID: {system['systemId']}")

            logger.info(f"System Name: {system['name']}")

            logger.info(f"Has Alarm: {system['hasAlarm']}")

            logger.info(f"Security Level: {system['securityLevel']}")

            logger.info(f"Country: {system['country']}")

            logger.info(f"Number of devices: {len(system['devices'])}")

            # Get device details to show brand information
            brands = get_device_brands(myuplink, system["devices"])

            if brands:
                logger.info(f"Device Brands: {', '.join(brands)}")

            logger.info("---")

        return True

    except (OSError, ValueError, KeyError) as e:
        logger.error(f"OAuth test failed: {e}")
        return False


async def main():
    """Run all tests."""
    logger.info("Testing myUplink API...")
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
        logger.info("OAuth Test: Skipped")

        if api_available:
            logger.info("API is available but OAuth cannot be tested due to missing prerequisites.")
        else:
            logger.info("Both API availability and OAuth tests failed.")

        # Exit early
        return

    # Test 2: OAuth and Data Retrieval
    logger.info("Test 2: OAuth Authentication and Data Retrieval")
    oauth_success = await test_oauth_and_get_systems()

    # Summary
    logger.info("Test Summary:")
    logger.info(f"API Available: {'✓' if api_available else '✗'}")

    logger.info("OAuth Prerequisites: ✓")
    logger.info(f"OAuth Successful: {'✓' if oauth_success else '✗'}")

    if api_available and oauth_success:
        logger.info("All tests passed!")
    else:
        logger.info("Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    asyncio.run(main())
