"""Config flow for NZ WITS Spot Price integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WitsApiClient, CannotConnect, InvalidAuth
from .const import (
    DOMAIN,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_NODE,
    DEFAULT_NODE,
    CONF_UPDATE_RTD,
    CONF_UPDATE_INTERIM,
    CONF_UPDATE_PRSS,
    CONF_UPDATE_PRSL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CLIENT_ID): str,
        vol.Required(CONF_CLIENT_SECRET): str,
        vol.Optional(CONF_NODE, default=DEFAULT_NODE): str,
    }
)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    client = WitsApiClient(data, async_get_clientsession(hass))
    await client.test_authentication()
    return {"title": f"WITS Node {data[CONF_NODE]}"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NZ WITS Spot Price."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_NODE])
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for NZ WITS."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Note: If a sensor is disabled, it can be updated on a custom schedule
        # by calling the 'homeassistant.update_entity' service in an automation.
        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_UPDATE_RTD,
                    default=self.config_entry.options.get(CONF_UPDATE_RTD, True),
                ): bool,
                vol.Required(
                    CONF_UPDATE_INTERIM,
                    default=self.config_entry.options.get(CONF_UPDATE_INTERIM, True),
                ): bool,
                vol.Required(
                    CONF_UPDATE_PRSS,
                    default=self.config_entry.options.get(CONF_UPDATE_PRSS, True),
                ): bool,
                vol.Required(
                    CONF_UPDATE_PRSL,
                    default=self.config_entry.options.get(CONF_UPDATE_PRSL, True),
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            description_placeholders={
                "rtd_sensor": "Real Time Dispatch (RTD)",
                "interim_sensor": "Interim Price",
                "prss_sensor": "Price Responsive Schedule Short (PRSS)",
                "prsl_sensor": "Price Responsive Schedule Long (PRSL)",
            },
        )
