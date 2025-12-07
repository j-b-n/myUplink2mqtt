"""Demo script for displaying all parameters with enumValues and their current values."""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from myuplink2mqtt.utils.myuplink_utils import (
    check_oauth_prerequisites,
    clean_parameter_name,
    create_api_client,
    get_device_details,
    get_device_points,
    get_parameter_display_name,
    get_systems,
)

# Logger initialization
logger = logging.getLogger(__name__)


def get_enum_text_for_value(enum_values, current_value):
    """
    Get the text representation for an enum value.

    Args:
        enum_values: List of enum value dictionaries with 'value' and 'text' keys
        current_value: The current numeric value to look up

    Returns:
        The text description if found, otherwise the numeric value as string
    """
    if not enum_values:
        return str(current_value)

    # Convert current_value to string for comparison
    value_str = str(int(current_value)) if isinstance(current_value, float) else str(current_value)

    for enum_item in enum_values:
        if enum_item.get("value") == value_str:
            # Clean the text to remove newlines and extra whitespace
            text = enum_item.get("text", value_str)
            return clean_parameter_name(text)

    return str(current_value)


def display_enum_parameter(point):
    """
    Display a single parameter with enumValues.

    Args:
        point: Parameter point data dictionary with enumValues

    Returns:
        True if parameter has enumValues and was displayed, False otherwise
    """
    enum_values = point.get("enumValues")

    # Only process parameters that have enumValues
    if not enum_values or len(enum_values) == 0:
        return False

    # Use the utility function to get cleaned parameter name
    parameter_name = get_parameter_display_name(point)
    parameter_id = point.get("parameterId", "Unknown")
    current_value = point.get("value")
    category = point.get("category", "")

    # Get the text representation of the current value
    enum_text = get_enum_text_for_value(enum_values, current_value)

    # Display the parameter with its enum value
    logger.info(f"{parameter_name}: {enum_text}")
    logger.info(f"  ID: {parameter_id} | Category: {category}")
    logger.info(f"  Current value: {current_value}")
    logger.info("  Available options:")
    for enum_item in enum_values:
        # Clean the enum text to remove newlines and extra whitespace
        enum_text_cleaned = clean_parameter_name(enum_item.get("text", ""))
        icon = f" [{enum_item['icon']}]" if enum_item.get("icon") else ""
        logger.info(f"    - {enum_item['value']}: {enum_text_cleaned}{icon}")
    logger.info("")

    return True


async def process_device_enum_parameters(myuplink, device_id, device_name):
    """Process and display enum parameters for a single device."""

    logger.info(f"\nDevice: {device_name} (ID: {device_id})")
    logger.info("-" * 80)

    all_points_data = await get_device_points(myuplink, device_id)

    if all_points_data is None:
        logger.info(f"Could not retrieve data points for {device_id}")
        return 0

    device_enum_count = 0
    for point in all_points_data:
        if display_enum_parameter(point):
            device_enum_count += 1

    if device_enum_count == 0:
        logger.info("  No parameters with enumValues found for this device")
    else:
        logger.info(f"  Total enum parameters found: {device_enum_count}")

    return device_enum_count


async def display_enum_parameters():
    """Display all parameters with enumValues and their current values."""

    session = None
    try:
        session, myuplink, _token_manager = await create_api_client()

        systems = await get_systems(myuplink)
        if systems is None:
            return False

        logger.info(f"Found {len(systems)} system(s)")
        logger.info("")

        enum_count = 0

        for system in systems:
            logger.info(f"System: {system['name']}")
            logger.info("=" * 80)

            for device in system["devices"]:
                device_id = device["id"]

                device_data = await get_device_details(myuplink, device_id)
                if device_data is None:
                    logger.info(f"Could not retrieve device details for {device_id}")
                    continue

                device_name = device_data["product"]["name"]
                device_enum_count = await process_device_enum_parameters(
                    myuplink, device_id, device_name
                )
                enum_count += device_enum_count

            logger.info("")

        logger.info("=" * 80)
        logger.info(f"Total parameters with enumValues found: {enum_count}")
        return True

    except (OSError, ValueError, KeyError) as e:
        logger.error(f"Enum parameters display failed: {e}")
        return False
    finally:
        if session:
            await session.close()


async def main():
    """Run the enum parameters demo."""
    logger.info("myUplink API - Enum Parameters Demo")
    logger.info("=" * 80)
    logger.info("This demo displays all parameters with enumValues and their current values")
    logger.info("")

    # Check OAuth prerequisites
    logger.info("Checking OAuth prerequisites...")
    can_proceed, error_msg = check_oauth_prerequisites()

    if not can_proceed:
        logger.info("❌ OAuth prerequisites not met:")
        logger.error(error_msg)
        logger.info("\nDemo Summary:")
        logger.info("OAuth Prerequisites: ✗")
        logger.info("Enum Parameters Display: Skipped")
        return

    logger.info("✓ OAuth prerequisites met")
    logger.info("")

    logger.info("Retrieving and displaying enum parameters...")
    logger.info("")
    success = await display_enum_parameters()

    # Summary
    logger.info("\nDemo Summary:")
    logger.info("OAuth Prerequisites: ✓")
    logger.info(f"Enum Parameters Display: {'✓' if success else '✗'}")

    if success:
        logger.info("\n✓ Enum parameters demo completed successfully!")
    else:
        logger.info("\n✗ Enum parameters demo failed")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )
    asyncio.run(main())
