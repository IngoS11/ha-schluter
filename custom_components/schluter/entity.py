"""Shared entity helpers for Schluter integration."""
from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity


class SchluterEntity(CoordinatorEntity):
    """Base entity that provides consistent availability semantics."""

    def __init__(self, coordinator, thermostat_id: str) -> None:
        super().__init__(coordinator)
        self._thermostat_id = thermostat_id

    @property
    def available(self) -> bool:
        """Return True only when coordinator and device are available."""
        obj = self.coordinator.data.get(self._thermostat_id)
        return (
            self.coordinator.last_update_success
            and obj is not None
            and getattr(obj, "is_online", True)
        )