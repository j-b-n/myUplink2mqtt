"""Demo script for saving myUplink API data to JSON file.

This script demonstrates how to use the save_api_data_to_file function
to retrieve all data from the myUplink API and save it to a JSON file.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from myuplink2mqtt.utils.myuplink_utils import (
    check_oauth_prerequisites,
    create_oauth_session,
    save_api_data_to_file,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


def main():
    """Main demo function."""
    logger.info("=" * 70)
    logger.info("myUplink API Data Save Demo")
    logger.info("=" * 70)
    logger.info("")

    # Check prerequisites
    logger.info("Checking OAuth prerequisites...")
    can_proceed, error_msg = check_oauth_prerequisites()

    if not can_proceed:
        logger.error("OAuth prerequisites not met:")
        logger.error(error_msg)
        logger.info("\nPlease configure OAuth credentials before running this demo.")
        return False

    logger.info("OAuth prerequisites met ✓")
    logger.info("")

    # Create OAuth session
    logger.info("Creating OAuth session...")
    try:
        myuplink = create_oauth_session()
        logger.info("OAuth session created ✓")
    except (OSError, ValueError, KeyError) as e:
        logger.error(f"Failed to create OAuth session: {e}")
        return False

    logger.info("")

    # Save data to file
    output_file = "/tmp/myuplink_demo.json"
    logger.info(f"Saving all API data to: {output_file}")
    logger.info("This may take a moment...")
    logger.info("")

    success = save_api_data_to_file(myuplink, output_file)

    if success:
        logger.info("")
        logger.info("=" * 70)
        logger.info("✓ Data export completed successfully")
        logger.info(f"✓ Data saved to: {output_file}")
        logger.info("=" * 70)
        return True
    else:
        logger.error("")
        logger.error("=" * 70)
        logger.error("✗ Data export failed")
        logger.error("=" * 70)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
