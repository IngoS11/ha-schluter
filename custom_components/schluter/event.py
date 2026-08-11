"""Event platform for Schluter integration."""

from __future__ import annotations

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SchluterData
from .const import (
    CONF_ENABLE_HEATING_EVENT,
    DEFAULT_ENABLE_HEATING_EVENT,
    DOMAIN,
    HEATING_STARTED_EVENT,
    HEATING_STOPPED_EVENT,
)
from .entity import SchluterEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Schluter heating event entities."""
    if not config_entry.options.get(
        CONF_ENABLE_HEATING_EVENT,
        DEFAULT_ENABLE_HEATING_EVENT,
    ):
        return

    data: SchluterData = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        SchluterHeatingEvent(data.coordinator, thermostat_id)
        for thermostat_id in data.coordinator.data
    )


class SchluterHeatingEvent(SchluterEntity, EventEntity):
    """Event entity that emits heating transitions."""

    _attr_event_types = [HEATING_STARTED_EVENT, HEATING_STOPPED_EVENT]

    def __init__(self, coordinator, thermostat_id: str) -> None:
        """Initialize the heating event entity."""
        super().__init__(coordinator, thermostat_id)
        self._attr_name = f"{self.thermostat.name} Heating Event"
        self._attr_unique_id = f"{self.serial_number}-heating-event"
        self._last_is_heating = self.thermostat.is_heating

    def _handle_coordinator_update(self) -> None:
        """Emit events when heating state transitions."""
        is_heating = self.thermostat.is_heating
        if is_heating != self._last_is_heating:
            event_type = HEATING_STARTED_EVENT if is_heating else HEATING_STOPPED_EVENT
            self._trigger_event(event_type)
        self._last_is_heating = is_heating

        self.async_write_ha_state()
