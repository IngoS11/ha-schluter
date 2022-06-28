"""Config flow for ingo_test integration."""
from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import ClientError
from aiohttp.client_exceptions import ClientConnectorError
from async_timeout import timeout
import voluptuous as vol

from aioschluter import SchluterApi, ApiError, InvalidUserPasswordError

from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class SchluterConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for schluter."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial setup of username and password"""
        # Only allow a single instance of the integration.
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors = {}

        if user_input is not None:
            websession = async_get_clientsession(self.hass)
            try:
                async with timeout(10):
                    schluter = SchluterApi(websession)
                    await schluter.async_get_sessionid(
                        user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                    )
            except (ApiError, ClientConnectorError, asyncio.TimeoutError, ClientError):
                errors["base"] = "cannot_connect"
            except InvalidUserPasswordError:
                errors[CONF_USERNAME] = "invalid_user_pass"
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
