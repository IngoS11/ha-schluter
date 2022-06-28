"""Support for Schluter DITRA-HEAT-E-WIFI Thermostats."""
from __future__ import annotations
from datetime import timedelta
import logging
from msilib.schema import Error

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.icon import icon_for_battery_level
from homeassistant.components.climate import ClimateEntity

from homeassistant.components.climate import (
    PLATFORM_SCHEMA,
    SCAN_INTERVAL,
    TEMP_CELSIUS,
    ClimateEntity,
)

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)

from . import SchluterDataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up device tracker for DITRA-HEAT-E-WIFI component."""
    name: str = entry.data[CONF_NAME]

    coordinator: SchluterDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    """Add thermostats entities """
    await coordinator.async_config_entry_first_refresh()
    async_add_entities([SchluterThermostatEntry(name, coordinator)])


class SchluterThermostatEntry(
    CoordinatorEntity[SchluterDataUpdateCoordinator], ClimateEntity
):
    """Define an Schluter Thermostat Entity"""

    _attr_hvac_mode = HVACMode.HEAT
    _attr_hvac_modes = [HVACMode.HEAT]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

    def __init__(self, name: str, coordinator: SchluterDataUpdateCoordinator) -> None:
        """Initialize"""
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = coordinator

    @property
    def unique_id(self):
        """Return unique ID for this device."""
        return self._serial_number

    @property
    def name(self):
        """Return the name of the thermostat."""
        return self._attr_name

    @property
    def temperature_unit(self):
        """Schluter API always uses celsius."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._temperature

    @property
    def hvac_action(self) -> HVACAction:
        """Return current operation. Can only be heating or idle."""
        if self._thermostat.is_heating:
            return HVACAction.HEATING
        return HVACAction.IDLE

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._set_point_temp

    @property
    def min_temp(self):
        """Identify min_temp in Schluter API."""
        return self._min_temp

    @property
    def max_temp(self):
        """Identify max_temp in Schluter API."""
        return self._max_temp

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self.coordinator.data[self._attr_name]["state"]
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Mode is always heating, so do nothing."""
        _LOGGER.info("Set the HVAC Mode to the current mode on the Schluter API")

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        _LOGGER.info("This will set the temperature of the thermostat")
        # target_temp = None
        # target_temp = kwargs.get(ATTR_TEMPERATURE)
        # serial_number = self.coordinator.data[self._serial_number].serial_number
        # _LOGGER.debug("Setting thermostat temperature: %s", target_temp)

        # try:
        #    if target_temp is not None:
        #        self._api.set_temperature(self._session_id, serial_number, target_temp)
        # except RequestException as ex:
        #    _LOGGER.error("An error occurred while setting temperature: %s", ex)
