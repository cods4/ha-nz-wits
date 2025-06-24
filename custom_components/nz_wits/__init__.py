"""The NZ WITS Spot Price integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WitsApiClient, CannotConnect, InvalidAuth
from .const import DOMAIN, CONF_NODE
from .coordinator import WitsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# List the platforms that you want to support.
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NZ WITS Spot Price from a config entry."""
    session = async_get_clientsession(hass)
    # Pass the whole entry.data to WitsApiClient, as it expects a config dict
    api_client = WitsApiClient(entry.data, session)

    # Get the WITS node (region) from the config entry
    # It's assumed CONF_NODE is defined in your const.py and present in entry.data
    wits_node = entry.data.get(CONF_NODE)
    if not wits_node:
        _LOGGER.error("WITS node not found in config entry data. Cannot set up coordinator.")
        # Or raise ConfigEntryNotReady("WITS node not configured") - depends on how critical it is at this stage
        # For now, let's assume it's critical and prevent setup.
        return False


    coordinator = WitsDataUpdateCoordinator(hass, api_client, wits_node)

    try:
        # Perform initial refresh to fetch data and confirm API access.
        # This will call _async_update_data in the coordinator.
        await coordinator.async_config_entry_first_refresh()
    except InvalidAuth as err:
        # If auth fails during the first refresh, raise ConfigEntryAuthFailed
        # This will typically prompt the user to reconfigure or re-authenticate.
        _LOGGER.error("Authentication failed during initial WITS data refresh: %s", err)
        raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
    except (CannotConnect, Exception) as err:
        # For other connection errors or unexpected issues during first refresh,
        # raise ConfigEntryNotReady to allow Home Assistant to retry setup later.
        _LOGGER.error("Error connecting to WITS API during initial refresh: %s", err)
        raise ConfigEntryNotReady(f"Failed to connect to WITS API: {err}") from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Add a listener to reload the integration when options are updated
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle an options update."""
    await hass.config_entries.async_reload(entry.entry_id)
