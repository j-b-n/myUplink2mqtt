"""Demo script for saving myUplink API data to JSON file.

This script demonstrates how to use the save_api_data_to_file function
to retrieve all data from the myUplink API and save it to a JSON file.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from myuplink2mqtt.utils.myuplink_utils import (
    check_oauth_prerequisites,
    create_api_client,
    save_api_data_to_file,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


async def main():
    """Main demo function."""

    logger.info("=" * 70)
    logger.info("myUplink API Data Save Demo")
    logger.info("=" * 70)
    logger.info("")

    logger.info("Checking OAuth prerequisites...")
    can_proceed, error_msg = check_oauth_prerequisites()

    if not can_proceed:
        logger.error("OAuth prerequisites not met:")
        logger.error(error_msg)
        logger.info("\nPlease configure OAuth credentials before running this demo.")
        return False

    logger.info("OAuth prerequisites met ✓")
    logger.info("")

    logger.info("Creating myUplink API client...")

    session = None
    try:
        session, myuplink, _token_manager = await create_api_client()
        logger.info("API client created ✓")

        logger.info("")

        output_file = "/tmp/myuplink_demo.json"
        logger.info(f"Saving all API data to: {output_file}")
        logger.info("This may take a moment...")
        logger.info("")

        success = await save_api_data_to_file(myuplink, output_file)

        if success:
            logger.info("")
            logger.info("=" * 70)
            logger.info("✓ Data export completed successfully")
            logger.info(f"✓ Data saved to: {output_file}")
            logger.info("=" * 70)
            return True

        logger.error("")
        logger.error("=" * 70)
        logger.error("✗ Data export failed")
        logger.error("=" * 70)
        return False

    except (OSError, ValueError, KeyError) as exc:
        logger.error(f"Failed to create myUplink API client: {exc}")
        return False

    finally:
        if session:
            await session.close()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
