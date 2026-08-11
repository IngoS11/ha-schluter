"""Support for Schluter DITRA-HEAT-E-WIFI thermostats."""

from __future__ import annotations

import logging

from aiohttp.client_exceptions import ClientConnectorError
from aioschluter import (
    ApiError,
    InvalidSessionIdError,
    InvalidUserPasswordError,
    SchluterApi,
    Thermostat,
)
from aioschluter.const import (
    REGULATION_MODE_AWAY,
    REGULATION_MODE_MANUAL,
    REGULATION_MODE_SCHEDULE,
)

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
    PRESET_AWAY,
    PRESET_NONE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import SchluterData
from .const import DOMAIN, PRESET_MANUAL, PRESET_SCHEDULE
from .entity import SchluterEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Schluter thermostat entities."""
    data: SchluterData = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        SchluterThermostat(data.api, data.coordinator, thermostat_id)
        for thermostat_id in data.coordinator.data
    )


class SchluterThermostat(SchluterEntity, ClimateEntity):
    """Representation of a Schluter thermostat."""

    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.AUTO, HVACMode.OFF]
    _attr_preset_modes = [PRESET_MANUAL, PRESET_SCHEDULE, PRESET_AWAY, PRESET_NONE]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.PRESET_MODE
    )
    _enable_turn_on_off_backwards_compatibility: bool = False

    coordinator: DataUpdateCoordinator[dict[str, Thermostat]]

    def __init__(
        self,
        api: SchluterApi,
        coordinator: DataUpdateCoordinator[dict[str, Thermostat]],
        thermostat_id: str,
    ) -> None:
        """Initialize a Schluter thermostat entity."""
        super().__init__(coordinator, thermostat_id)
        self._api = api
        self._attr_unique_id = f"{self.serial_number}-climate"

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        regulation_mode = self.thermostat.regulation_mode
        if regulation_mode == REGULATION_MODE_SCHEDULE:
            return HVACMode.AUTO
        if regulation_mode == REGULATION_MODE_MANUAL:
            return HVACMode.HEAT
        return HVACMode.OFF

    @property
    def temperature_unit(self) -> str:
        """Return the temperature unit used by the API."""
        return UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self) -> float:
        """Return the current temperature."""
        return self.thermostat.temperature

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current HVAC action."""
        if self.thermostat.is_heating:
            return HVACAction.HEATING
        return HVACAction.IDLE

    @property
    def target_temperature(self) -> float:
        """Return the target temperature."""
        return self.thermostat.set_point_temp

    @property
    def min_temp(self) -> float:
        """Return the minimum target temperature."""
        return self.thermostat.min_temp

    @property
    def max_temp(self) -> float:
        """Return the maximum target temperature."""
        return self.thermostat.max_temp

    @property
    def preset_mode(self) -> str:
        """Return the active preset mode."""
        regulation_mode = self.thermostat.regulation_mode
        if regulation_mode == REGULATION_MODE_SCHEDULE:
            return PRESET_SCHEDULE
        if regulation_mode == REGULATION_MODE_MANUAL:
            return PRESET_MANUAL
        if regulation_mode == REGULATION_MODE_AWAY:
            return PRESET_AWAY
        return PRESET_NONE

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode."""
        if hvac_mode == HVACMode.AUTO:
            regulation_mode = REGULATION_MODE_SCHEDULE
        elif hvac_mode == HVACMode.HEAT:
            regulation_mode = REGULATION_MODE_MANUAL
        else:
            regulation_mode = REGULATION_MODE_AWAY

        await self._async_set_regulation_mode(regulation_mode)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the climate preset mode."""
        if preset_mode == PRESET_SCHEDULE:
            regulation_mode = REGULATION_MODE_SCHEDULE
        elif preset_mode == PRESET_MANUAL:
            regulation_mode = REGULATION_MODE_MANUAL
        elif preset_mode == PRESET_AWAY:
            regulation_mode = REGULATION_MODE_AWAY
        else:
            regulation_mode = REGULATION_MODE_MANUAL

        await self._async_set_regulation_mode(regulation_mode)

    async def _async_set_regulation_mode(self, regulation_mode: int) -> None:
        """Set regulation mode through the Schluter API."""
        session_id = self.coordinator.session_id
        if session_id is None:
            await self.coordinator.async_request_refresh()
            session_id = self.coordinator.session_id

        if session_id is None:
            raise UpdateFailed("No active session ID")

        _LOGGER.debug(
            "Setting regulation mode of thermostat %s to %s",
            self.thermostat.name,
            regulation_mode,
        )

        try:
            await self._api.async_set_regulation_mode(
                session_id,
                self.serial_number,
                regulation_mode,
            )
            await self.coordinator.async_request_refresh()
        except (InvalidUserPasswordError, InvalidSessionIdError) as err:
            raise ConfigEntryAuthFailed from err
        except (ApiError, ClientConnectorError) as err:
            raise UpdateFailed(err) from err

    async def async_set_temperature(self, **kwargs: float) -> None:
        """Set a new target temperature."""
        target_temp = kwargs.get(ATTR_TEMPERATURE)
        if target_temp is None:
            return

        session_id = self.coordinator.session_id
        if session_id is None:
            await self.coordinator.async_request_refresh()
            session_id = self.coordinator.session_id

        if session_id is None:
            raise UpdateFailed("No active session ID")

        _LOGGER.debug("Setting thermostat temperature to %s", target_temp)

        try:
            await self._api.async_set_temperature(
                session_id,
                self.serial_number,
                target_temp,
            )
            await self.coordinator.async_request_refresh()
        except (InvalidUserPasswordError, InvalidSessionIdError) as err:
            raise ConfigEntryAuthFailed from err
        except (ApiError, ClientConnectorError) as err:
            raise UpdateFailed(err) from err
