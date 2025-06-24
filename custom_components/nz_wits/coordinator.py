"""DataUpdateCoordinator for the NZ WITS integration."""
import async_timeout
from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant

from .api import WitsApiClient, CannotConnect, InvalidAuth
from .const import DOMAIN, SCHEDULE_TYPES

_LOGGER = logging.getLogger(__name__)


class WitsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching WITS data from the API."""

    def __init__(self, hass: HomeAssistant, api_client: WitsApiClient, node: str):
        """Initialize."""
        self.api_client = api_client
        self.node = node
        # Define a default update interval, e.g., 5 minutes.
        # This can be made configurable later if needed.
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({node})",
            update_interval=timedelta(minutes=5),
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Using async_timeout.timeout protects against API hangs indefinitely.
            # Adjust timeout as necessary for your API.
            async with async_timeout.timeout(30):
                # Fetch data for all relevant schedule types.
                # The API client is expected to fetch data for its configured node.
                # We will store data for all schedules under a common structure.
                all_schedule_data = {}
                for schedule_key, schedule_info in SCHEDULE_TYPES.items():
                    price_data = await self.api_client.get_price_data(schedule_key)
                    all_schedule_data[schedule_key] = price_data

                if not any(all_schedule_data.values()): # Check if all schedules returned empty data
                    # This could indicate an issue with the node or API returning no data
                    # even if the calls were successful.
                    _LOGGER.warning("No price data received for node %s across all schedules.", self.node)
                    # Depending on desired behavior, you might raise UpdateFailed here
                    # or return the empty structure. For now, returning it.

                return all_schedule_data
        except InvalidAuth as err:
            # Raising ConfigEntryAuthFailed will direct user to reconfigure the integration.
            # This is for cases where credentials are no longer valid.
            _LOGGER.error("Authentication failed while updating WITS data: %s", err)
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except CannotConnect as err:
            # Temporary connection issues should raise UpdateFailed to retry later.
            _LOGGER.error("Error connecting to WITS API while updating data: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            # Catch any other unexpected errors.
            _LOGGER.exception("Unexpected error fetching WITS data for node %s: %s", self.node, err)
            raise UpdateFailed(f"An unexpected error occurred: {err}") from err
