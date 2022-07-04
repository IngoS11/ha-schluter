"""Break out the temperature of the thermostat into a separate sensor entity."""

from aioschluter import Thermostat

from homeassistant.const import (
    TEMP_CELSIUS,
    POWER_WATT,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import SchluterData
from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    data: SchluterData = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        SchluterPowerSensor(data.coordinator, thermostat_id)
        for thermostat_id in data.coordinator.data
    )

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
        self._attr_unique_id = (
            f"{coordinator.data[thermostat_id].name}-{self._attr_device_class}"
        )

    @property
    def available(self) -> bool:
        """Return True if Schluter thermostat is available."""
        return self.coordinator.data[self._thermostat_id].is_online

    @property
    def device_info(self):
        """Return information to link this entity."""
        return {
            "identifiers": {(DOMAIN, self._thermostat_id)},
        }

    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""
        return self.coordinator.data[self._thermostat_id].temperature


class SchluterPowerSensor(CoordinatorEntity[DataUpdateCoordinator], SensorEntity):
    """Representation of a Sensor."""

    _attr_native_unit_of_measurement = POWER_WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[dict[str, dict[str, Thermostat]]],
        thermostat_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = coordinator.data[thermostat_id].name + " Power"
        self._thermostat_id = thermostat_id
        self._attr_unique_id = (
            f"{coordinator.data[thermostat_id].name}-{self._attr_device_class}"
        )

    @property
    def available(self) -> bool:
        """Return True if Schluter thermostat is available."""
        return self.coordinator.data[self._thermostat_id].is_online

    @property
    def device_info(self):
        """Return information to link this entity."""
        return {
            "identifiers": {(DOMAIN, self._thermostat_id)},
        }

    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""
        if self.coordinator.data[self._thermostat_id].is_heating:
            return self.coordinator.data[self._thermostat_id].load_measured_watt
        else:
            return 0
