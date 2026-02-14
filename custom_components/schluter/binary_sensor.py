"""Binary sensor platform for Schluter integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SchluterData
from .const import (
    CONF_ENABLE_ONLINE_STATUS_SENSOR,
    DEFAULT_ENABLE_ONLINE_STATUS_SENSOR,
    DOMAIN,
)
from .entity import SchluterEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Schluter binary sensors."""
    if not config_entry.options.get(
        CONF_ENABLE_ONLINE_STATUS_SENSOR,
        DEFAULT_ENABLE_ONLINE_STATUS_SENSOR,
    ):
        return

    data: SchluterData = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        SchluterOnlineStatusSensor(data.coordinator, thermostat_id)
        for thermostat_id in data.coordinator.data
    )


class SchluterOnlineStatusSensor(SchluterEntity, BinarySensorEntity):
    """Representation of thermostat online status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator, thermostat_id: str) -> None:
        """Initialize the online status sensor."""
        super().__init__(coordinator, thermostat_id)
        self._attr_name = f"{self.thermostat.name} Online Status"
        self._attr_unique_id = f"{self.serial_number}-online_status-binary_sensor"

    @property
    def is_on(self) -> bool:
        """Return whether thermostat is online."""
        return self.thermostat.is_online
