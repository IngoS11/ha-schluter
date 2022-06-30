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
    TEMP_CELSIUS,
    ClimateEntity,
)

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)

from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)

from aioschluter import SchluterApi, Thermostat

from . import SchluterData
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up device tracker for DITRA-HEAT-E-WIFI component."""
    data: SchluterData = hass.data[DOMAIN][entry.unique_id]
    async_add_entities(
        SchluterThermostat(data.api, data.coordinator, thermostat_id)
        for thermostat_id in data.coordinator.data["thermostats"]
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
        self._name = coordinator.data["thermostats"][thermostat_id].name
        self._attr_unique_id = thermostat_id
        ClimateEntity.__init__(self)
