"""Demo script to retrieve and print systems from myUplink API /v2/systems/me endpoint."""

import json
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from myuplink2mqtt.utils.myuplink_utils import (
    check_oauth_prerequisites,
    create_oauth_session,
    get_systems,
)

# Logger initialization
logger = logging.getLogger(__name__)


def main():
    """Main function to demonstrate /v2/systems/me endpoint usage."""
    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Check OAuth prerequisites
    can_proceed, error = check_oauth_prerequisites()
    if not can_proceed:
        logger.error(f"OAuth prerequisites not met: {error}")
        return

    # Create OAuth session
    myuplink = create_oauth_session()
    if myuplink is None:
        logger.error("Failed to create OAuth session")
        return

    # Retrieve systems using /v2/systems/me endpoint
    systems = get_systems(myuplink)
    if systems is None:
        logger.error("Failed to retrieve systems from /v2/systems/me")
        return

    # Print the result
    logger.info(f"Successfully retrieved {len(systems)} system(s)")
    print(json.dumps(systems, indent=2))


if __name__ == "__main__":
    main()
