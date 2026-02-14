"""Diagnostics support for Schluter integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data

from . import SchluterConfigEntry

TO_REDACT = {"username", "password", "sessionid", "session_id", "token"}


async def async_get_config_entry_diagnostics(
    hass: Any, entry: SchluterConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    runtime_data = entry.runtime_data

    thermostats = {
        thermostat_id: vars(thermostat)
        for thermostat_id, thermostat in runtime_data.coordinator.data.items()
    }

    payload = {
        "entry": entry.as_dict(),
        "thermostats": thermostats,
    }
    return async_redact_data(payload, TO_REDACT)
