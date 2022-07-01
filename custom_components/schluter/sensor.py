""" Break out the temperature of the thermostat into a separate sensor entity."""

from .const import DOMAIN
from . import SchluterData

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    TEMP_KELVIN,
)

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)

from aioschluter import Thermostat


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    data: SchluterData = hass.data[DOMAIN][config_entry.entry_id]

    temperature_unit = hass.config.units.temperature_unit
    async_add_entities(
        SchluterTemperatureSensor(data.coordinator, thermostat_id)
        for thermostat_id in data.coordinator.data
    )


class SchluterTemperatureSensor(CoordinatorEntity[DataUpdateCoordinator], SensorEntity):
    """Representation of a Sensor."""

    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[dict[str, dict[str, Thermostat]]],
        thermostat_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = coordinator.data[thermostat_id].name + " Current Temperature"
        self._thermostat_id = thermostat_id
        self._attr_unique_id = thermostat_id + "_temperature"

    @property
    def available(self) -> bool:
        """Return True if Schluter thermostat is available."""
        return self.coordinator.data[self._thermostat_id].is_online

    @property
    def device_info(self):
        """Return information to link this entity with the correct
        thermostat in the devices registry.
        """
        return {
            "identifiers": {(DOMAIN, self._thermostat_id)},
        }

    @property
    def state(self):
        """Return the state of the sensor."""
        temperature = self.coordinator.data[self._thermostat_id].temperature
        if self.unit_of_measurement == TEMP_CELSIUS:
            return temperature
        elif self.unit_of_measurement == TEMP_FAHRENHEIT:
            return (temperature * 1.8) + 32
        return round(temperature + 273.15, 2)
