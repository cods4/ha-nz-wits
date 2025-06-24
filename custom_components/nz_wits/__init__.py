"""The NZ WITS Spot Price integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WitsApiClient, CannotConnect, InvalidAuth
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# List the platforms that you want to support.
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NZ WITS Spot Price from a config entry."""
    # Get the shared aiohttp session and create an API client instance.
    session = async_get_clientsession(hass)
    api_client = WitsApiClient(entry.data, session)

    # Test the API connection. If it fails, Home Assistant will retry later.
    try:
        await api_client.test_authentication()
    except (CannotConnect, InvalidAuth) as err:
        raise ConfigEntryNotReady(f"Failed to connect to WITS API: {err}") from err

    # Store the API client in the hass.data dictionary to be accessed by platforms
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = api_client

    # Set up the platforms (e.g., sensor)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This is called when an integration instance is removed from Home Assistant.
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
