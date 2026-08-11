"""Config flow for the Schluter integration."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
import logging
from typing import Any

from aiohttp import ClientError
from aiohttp.client_exceptions import ClientConnectorError
from aioschluter import ApiError, InvalidUserPasswordError, SchluterApi
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .options_flow import SchluterOptionsFlowHandler

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


@config_entries.HANDLERS.register(DOMAIN)
class SchluterConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Schluter."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        _config_entry: config_entries.ConfigEntry,
    ) -> SchluterOptionsFlowHandler:
        """Return the options flow handler."""
        return SchluterOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial setup of username and password."""
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            hid, error = await self.async_try_connect(username, password)
            if error is None and hid is not None:
                entry = await self.async_set_unique_id(hid)
                if entry:
                    self.hass.config_entries.async_update_entry(entry, data=user_input)
                    await self.hass.config_entries.async_reload(entry.entry_id)
                    return self.async_abort(reason="reauth_successful")

                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=username, data=user_input)

            errors["base"] = error or "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> FlowResult:
        """Handle reauth when credentials are invalid."""
        _LOGGER.debug("Reauthentication required")
        self.reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Perform reauth upon an API authentication error."""
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm", data_schema=STEP_USER_DATA_SCHEMA
            )

        return await self.async_step_user(user_input)

    async def async_try_connect(
        self, username: str, password: str
    ) -> tuple[str | None, str | None]:
        """Try connecting to the Schluter API."""
        websession = async_get_clientsession(self.hass)
        schluter = SchluterApi(websession)

        try:
            await schluter.async_get_sessionid(username, password)
        except (ApiError, ClientConnectorError, asyncio.TimeoutError, ClientError):
            return None, "cannot_connect"
        except InvalidUserPasswordError:
            return None, "invalid_user_pass"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            return None, "unknown"

        return username, None
