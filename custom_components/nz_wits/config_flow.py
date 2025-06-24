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
    ) -> "OptionsFlowHandler":
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Handle configuration by re-authentication."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Dialog to confirm re-authentication."""
        errors: dict[str, str] = {}
        
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        
        if user_input is not None and entry:
            try:
                # Combine existing data with user input
                updated_data = entry.data.copy()
                updated_data.update(user_input)
                await validate_input(self.hass, updated_data)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception during re-authentication")
                errors["base"] = "unknown"
            else:
                self.hass.config_entries.async_update_entry(entry, data=updated_data)
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        prefill_schema = vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID, default=entry.data.get(CONF_CLIENT_ID) if entry else ""): str,
                vol.Required(CONF_CLIENT_SECRET, default=""): str,
                vol.Optional(CONF_NODE, default=entry.data.get(CONF_NODE, DEFAULT_NODE) if entry else DEFAULT_NODE): str,
            }
        )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=prefill_schema,
            errors=errors,
        )

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
        errors: dict[str, str] = {}

        if user_input is not None:
            # Prepare updated data for validation if credentials/node changed
            updated_core_data = self.config_entry.data.copy()
            core_data_changed = False

            if user_input.get(CONF_CLIENT_ID) != self.config_entry.data.get(CONF_CLIENT_ID) or \
               user_input.get(CONF_CLIENT_SECRET) != self.config_entry.data.get(CONF_CLIENT_SECRET) or \
               user_input.get(CONF_NODE) != self.config_entry.data.get(CONF_NODE):
                core_data_changed = True
                updated_core_data[CONF_CLIENT_ID] = user_input[CONF_CLIENT_ID]
                updated_core_data[CONF_CLIENT_SECRET] = user_input[CONF_CLIENT_SECRET]
                updated_core_data[CONF_NODE] = user_input[CONF_NODE]

            if core_data_changed:
                try:
                    _LOGGER.debug("WITS Options: Core data changed, validating new credentials/node.")
                    await validate_input(self.hass, updated_core_data)
                    # If validation passes, update the main config entry data
                    self.hass.config_entries.async_update_entry(
                        self.config_entry, data=updated_core_data
                    )
                    _LOGGER.debug("WITS Options: Core data updated successfully.")
                except CannotConnect:
                    _LOGGER.error("WITS Options: Cannot connect with new credentials/node.")
                    errors["base"] = "cannot_connect"
                except InvalidAuth:
                    _LOGGER.error("WITS Options: Invalid authentication with new credentials/node.")
                    errors["base"] = "invalid_auth"
                except Exception:
                    _LOGGER.exception("WITS Options: Unexpected exception during credential/node validation.")
                    errors["base"] = "unknown"

            if not errors:
                # Create/update the options entry with the update toggles
                # Exclude core config from options dict
                options_data = {
                    k: v for k, v in user_input.items()
                    if k not in [CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_NODE]
                }
                return self.async_create_entry(title="", data=options_data)

        # Schema for the options form
        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_CLIENT_ID,
                    default=self.config_entry.data.get(CONF_CLIENT_ID),
                ): str,
                vol.Required(
                    CONF_CLIENT_SECRET,
                    default=self.config_entry.data.get(CONF_CLIENT_SECRET),
                ): str,
                vol.Optional(
                    CONF_NODE,
                    default=self.config_entry.data.get(CONF_NODE, DEFAULT_NODE),
                ): str,
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

        # The description will now be automatically pulled from the translations
        # using the key "options.step.init.description".
        # Field labels will be pulled from "options.step.init.data.<field_name>".
        # The title will be pulled from "options.step.init.title".
        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors=errors
            # No need for description_placeholders if the description is static
            # and fully defined in the translation file.
        )
