"""Options flow for the Schluter integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_ENABLE_ENERGY_SENSOR,
    CONF_ENABLE_HEATING_EVENT,
    CONF_ENABLE_ONLINE_STATUS_SENSOR,
    DEFAULT_ENABLE_ENERGY_SENSOR,
    DEFAULT_ENABLE_HEATING_EVENT,
    DEFAULT_ENABLE_ONLINE_STATUS_SENSOR,
)


class SchluterOptionsFlowHandler(OptionsFlow):
    """Handle Schluter options."""

    def __init__(self, config_entry: ConfigEntry | None = None) -> None:
        """Initialize options flow.

        Keep optional `config_entry` support for backward compatibility with
        older custom component loading paths that still pass it explicitly.
        """
        super().__init__()
        self._legacy_config_entry: ConfigEntry | None = config_entry

    @property
    def _entry_options(self) -> Mapping[str, Any]:
        """Return config entry options for both legacy and current flow APIs."""
        if self.hass is not None:
            return self.config_entry.options
        if self._legacy_config_entry is not None:
            return self._legacy_config_entry.options
        return {}

    @callback
    def _options_schema(self) -> vol.Schema:
        """Return the options schema."""
        options = self._entry_options
        return vol.Schema(
            {
                vol.Required(
                    CONF_ENABLE_ONLINE_STATUS_SENSOR,
                    default=options.get(
                        CONF_ENABLE_ONLINE_STATUS_SENSOR,
                        DEFAULT_ENABLE_ONLINE_STATUS_SENSOR,
                    ),
                ): bool,
                vol.Required(
                    CONF_ENABLE_ENERGY_SENSOR,
                    default=options.get(
                        CONF_ENABLE_ENERGY_SENSOR,
                        DEFAULT_ENABLE_ENERGY_SENSOR,
                    ),
                ): bool,
                vol.Required(
                    CONF_ENABLE_HEATING_EVENT,
                    default=options.get(
                        CONF_ENABLE_HEATING_EVENT,
                        DEFAULT_ENABLE_HEATING_EVENT,
                    ),
                ): bool,
            }
        )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=self._options_schema())
