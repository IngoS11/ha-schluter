"""Sensor platform for the Schluter integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from aioschluter import Thermostat

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from . import SchluterData
from .const import (
    CONF_ENABLE_ENERGY_SENSOR,
    DEFAULT_ENABLE_ENERGY_SENSOR,
    DOMAIN,
    ZERO_WATTS,
)
from .entity import SchluterEntity


type SensorValueFn = Callable[[Thermostat], float]


@dataclass(frozen=True, kw_only=True)
class SchluterSensorDescription(SensorEntityDescription):
    """Describes Schluter sensor entities."""

    suffix: str
    value_fn: SensorValueFn | None = None


SENSOR_DESCRIPTIONS: tuple[SchluterSensorDescription, ...] = (
    SchluterSensorDescription(
        key="temperature",
        suffix="Current Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda thermostat: thermostat.temperature,
    ),
    SchluterSensorDescription(
        key="target_temperature",
        suffix="Target Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda thermostat: thermostat.set_point_temp,
    ),
    SchluterSensorDescription(
        key="power",
        suffix="Power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda thermostat: (
            thermostat.load_measured_watt if thermostat.is_heating else ZERO_WATTS
        ),
    ),
    SchluterSensorDescription(
        key="price",
        suffix="Price",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="$/kWh",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda thermostat: thermostat.kwh_charge,
    ),
    SchluterSensorDescription(
        key="energy",
        suffix="Energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Schluter sensors for a config entry."""
    data: SchluterData = hass.data[DOMAIN][config_entry.entry_id]

    enable_energy_sensor = config_entry.options.get(
        CONF_ENABLE_ENERGY_SENSOR,
        DEFAULT_ENABLE_ENERGY_SENSOR,
    )

    entities: list[SchluterSensor] = []
    for thermostat_id in data.coordinator.data:
        for description in SENSOR_DESCRIPTIONS:
            if description.key == "energy" and not enable_energy_sensor:
                continue
            entities.append(
                SchluterSensor(data.coordinator, thermostat_id, description)
            )

    async_add_entities(entities)


class SchluterSensor(SchluterEntity, RestoreEntity, SensorEntity):
    """Representation of a Schluter sensor."""

    entity_description: SchluterSensorDescription

    def __init__(
        self,
        coordinator: Any,
        thermostat_id: str,
        description: SchluterSensorDescription,
    ) -> None:
        """Initialize the Schluter sensor."""
        super().__init__(coordinator, thermostat_id)
        self.entity_description = description
        self._attr_name = f"{self.thermostat.name} {description.suffix}"
        self._attr_unique_id = f"{self.serial_number}-{description.key}-sensor"
        self._last_update_timestamp: datetime | None = None
        self._attr_native_value: float | None = None

    async def async_added_to_hass(self) -> None:
        """Handle entity added to hass."""
        await super().async_added_to_hass()

        if not self._is_energy_sensor:
            return

        if (last_state := await self.async_get_last_state()) is not None:
            try:
                self._attr_native_value = float(last_state.state)
            except ValueError:
                self._attr_native_value = 0.0
        else:
            self._attr_native_value = 0.0

    @property
    def _is_energy_sensor(self) -> bool:
        """Return True when this sensor is the energy sensor."""
        return self.entity_description.key == "energy"

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        if self._is_energy_sensor:
            return self._attr_native_value

        value_fn = self.entity_description.value_fn
        if value_fn is None:
            return None

        return value_fn(self.thermostat)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self._is_energy_sensor:
            self._update_energy_total()

        self.async_write_ha_state()

    def _update_energy_total(self) -> None:
        """Update accumulated energy in kWh based on elapsed time."""
        now = dt_util.utcnow()
        if self._attr_native_value is None:
            self._attr_native_value = 0.0

        if self._last_update_timestamp is not None and self.thermostat.is_heating:
            elapsed_hours = (
                now - self._last_update_timestamp
            ).total_seconds() / 3600.0
            energy_delta = (
                self.thermostat.load_measured_watt * elapsed_hours
            ) / 1000.0
            self._attr_native_value += energy_delta

        self._last_update_timestamp = now
