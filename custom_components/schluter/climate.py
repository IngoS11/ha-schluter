"""Support for Schluter DITRA-HEAT-E-WIFI Thermostats."""
from __future__ import annotations
import logging

from aiohttp.client_exceptions import ClientConnectorError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.components.climate import (
    TEMP_CELSIUS,
    ClimateEntity,
)

from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
    UpdateFailed,
)

from aioschluter import (
    SchluterApi,
    Thermostat,
    ApiError,
    InvalidSessionIdError,
    InvalidUserPasswordError,
)

from . import SchluterData
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up device tracker for DITRA-HEAT-E-WIFI component."""
    data: SchluterData = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        SchluterThermostat(data.api, data.coordinator, thermostat_id)
        for thermostat_id in data.coordinator.data
    )


class SchluterThermostat(CoordinatorEntity[DataUpdateCoordinator], ClimateEntity):
    """Define an Schluter Thermostat Entity"""

    _attr_hvac_mode = HVACMode.HEAT
    _attr_hvac_modes = [HVACMode.HEAT]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

    coordinator: DataUpdateCoordinator[dict[str, dict[str, Thermostat]]]

    def __init__(
        self,
        api: SchluterApi,
        coordinator: DataUpdateCoordinator[dict[str, dict[str, Thermostat]]],
        thermostat_id: str,
    ) -> None:
        """Initialize Schluter Thermostat"""
        super().__init__(coordinator)
        self._api = api
        self._name = coordinator.data[thermostat_id].name
        self._attr_unique_id = thermostat_id
        self._serial_number = coordinator.data[thermostat_id].serial_number
        ClimateEntity.__init__(self)

    @property
    def device_info(self):
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self._attr_unique_id)},
            # If desired, the name for the device could be different to the entity
            "name": self._name,
            "sw_version": self.coordinator.data[self._attr_unique_id].sw_version,
            "model": "DITRA-HEAT-E-Wifi",
            "manufacturer": "Schluter",
        }

    @property
    def unique_id(self):
        """Return unique ID for this device."""
        return self._serial_number

    @property
    def name(self):
        """Return the name of the thermostat."""
        return self._name

    @property
    def temperature_unit(self):
        """Schluter API always uses celsius."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self.coordinator.data[self._attr_unique_id].temperature

    @property
    def hvac_action(self) -> HVACAction:
        """Return current operation. Can only be heating or idle."""
        if self.coordinator.data[self._attr_unique_id].is_heating:
            return HVACAction.HEATING
        return HVACAction.IDLE

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self.coordinator.data[self._attr_unique_id].set_point_temp

    @property
    def min_temp(self):
        """Identify min_temp in Schluter API."""
        return self.coordinator.data[self._attr_unique_id].min_temp

    @property
    def max_temp(self):
        """Identify max_temp in Schluter API."""
        return self.coordinator.data[self._attr_unique_id].max_temp

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Mode is always heating, so do nothing."""

    # This property is important to let HA know if this entity is online or not.
    # If an entity is offline (return False), the UI will refelect this.
    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return self.coordinator.data[self._attr_unique_id].is_online

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        target_temp = kwargs.get(ATTR_TEMPERATURE)
        serial_number = self.coordinator.data[self._attr_unique_id].serial_number
        session_id = self._api.sessionid
        _LOGGER.debug("Setting thermostat temperature: %s", target_temp)

        try:
            if target_temp is not None:
                await self._api.async_set_temperature(
                    session_id, serial_number, target_temp
                )
        except (
            InvalidUserPasswordError,
            InvalidSessionIdError,
        ) as err:
            raise ConfigEntryAuthFailed from err
        except (ApiError, ClientConnectorError) as err:
            raise UpdateFailed(err) from err
