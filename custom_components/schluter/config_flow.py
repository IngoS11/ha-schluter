"""Config flow for ingo_test integration."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from aiohttp import ClientError
from aiohttp.client_exceptions import ClientConnectorError
from aioschluter import ApiError, InvalidUserPasswordError, SchluterApi
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


@config_entries.HANDLERS.register(DOMAIN)
class SchluterConfigFlowHandler(
    config_entries.ConfigFlow,
):
    """Handle a config flow for schluter."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial setup of username and password."""
        # Only allow a single instance of the integration.
        # if self._async_current_entries():
        #    return self.async_abort(reason="single_instance_allowed")

        errors = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            hid, error = await self.async_try_connect(username, password)
            if error is None:
                entry = await self.async_set_unique_id(hid)
                if entry:
                    self.hass.config_entries.async_update_entry(entry, data=user_input)
                    await self.hass.config_entries.async_reload(entry.entry_id)
                    return self.async_abort(reason="reauth_successful")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=username, data=user_input)
            errors["base"] = error

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> FlowResult:
        """Handle re-auth if token invalid."""
        # pylint: disable=unused-argument
        _LOGGER.debug("Not implemented yet")
        return await self.async_step_user()

    async def async_try_connect(
        self, username: str, password: str
    ) -> tuple[str | None, str | None]:
        """Try connecting to Schluter API."""
        websession = async_get_clientsession(self.hass)
        schluter = SchluterApi(websession)
        try:
            await schluter.async_get_sessionid(username, password)
        except (ApiError, ClientConnectorError, asyncio.TimeoutError, ClientError):
            return None, "cannot_connect"
        except InvalidUserPasswordError:
            return None, "invalid_user_pass"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            return None, "unknown"
        return username, None
