"""Shared entity helpers for Schluter integration."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class SchluterEntity(CoordinatorEntity):
    """Base entity that provides consistent availability semantics."""

    def __init__(self, coordinator: Any, thermostat_id: str) -> None:
        """Initialize the base Schluter entity."""
        super().__init__(coordinator)
        self._thermostat_id = thermostat_id

    @property
    def available(self) -> bool:
        """Return True only when coordinator and device are available."""
        thermostat = self.coordinator.data.get(self._thermostat_id)
        return (
            self.coordinator.last_update_success
            and thermostat is not None
            and getattr(thermostat, "is_online", True)
        )

    @property
    def thermostat(self) -> Any:
        """Return the thermostat payload for this entity."""
        return self.coordinator.data[self._thermostat_id]

    @property
    def serial_number(self) -> str:
        """Return the immutable thermostat serial number."""
        return self.thermostat.serial_number

    @property
    def device_info(self) -> dict[str, Any]:
        """Return information to link this entity with a device."""
        return {
            "identifiers": {(DOMAIN, self.serial_number)},
            "name": self.thermostat.name,
            "sw_version": getattr(self.thermostat, "sw_version", None),
            "model": "DITRA-HEAT-E-Wifi",
            "manufacturer": "Schluter",
        }
