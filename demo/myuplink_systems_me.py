"""Demo script to retrieve and print systems from myUplink API /v2/systems/me endpoint."""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from myuplink2mqtt.utils.myuplink_utils import (
    check_oauth_prerequisites,
    create_api_client,
    get_systems,
)

# Logger initialization
logger = logging.getLogger(__name__)


async def main():
    """Main function to demonstrate /v2/systems/me endpoint usage."""

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    can_proceed, error = check_oauth_prerequisites()
    if not can_proceed:
        logger.error(f"OAuth prerequisites not met: {error}")
        return 1

    session = None
    try:
        session, api, _token_manager = await create_api_client()
        if api is None:
            logger.error("Failed to create myUplink API client")
            return 1

        systems = await get_systems(api)
        if systems is None:
            logger.error("Failed to retrieve systems from /v2/systems/me")
            return 1

        logger.info(f"Successfully retrieved {len(systems)} system(s)")
        print(json.dumps(systems, indent=2))
        return 0
    finally:
        if session:
            await session.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
