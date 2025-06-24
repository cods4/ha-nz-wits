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
    session = async_get_clientsession(hass)
    api_client = WitsApiClient(entry.data, session)

    try:
        await api_client.test_authentication()
    except (CannotConnect, InvalidAuth) as err:
        # This will trigger the re-authentication flow if credentials fail
        raise ConfigEntryNotReady(f"Failed to connect to WITS API: {err}") from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = api_client

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

