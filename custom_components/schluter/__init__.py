"""The Schluter integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
import logging
from typing import Any

from aiohttp.client_exceptions import ClientConnectorError
from aioschluter import (
    ApiError,
    InvalidSessionIdError,
    InvalidUserPasswordError,
    SchluterApi,
    Thermostat,
)
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.core_config import Config
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    HEATING_STARTED_EVENT,
    HEATING_STOPPED_EVENT,
    PLATFORMS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


type SchluterConfigEntry = ConfigEntry["SchluterData"]


async def async_setup(hass: HomeAssistant, config: Config) -> bool:
    """Set up the Schluter integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: SchluterConfigEntry) -> bool:
    """Set up Schluter from a config entry."""
    username: str = entry.data[CONF_USERNAME]
    password: str = entry.data[CONF_PASSWORD]

    websession = async_get_clientsession(hass)
    api = SchluterApi(websession)

    coordinator = SchluterDataUpdateCoordinator(hass, api, username, password)
    await coordinator.async_config_entry_first_refresh()

    runtime_data = SchluterData(
        api=api,
        coordinator=coordinator,
    )
    entry.runtime_data = runtime_data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = runtime_data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: SchluterConfigEntry) -> bool:
    """Unload a Schluter config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def update_listener(hass: HomeAssistant, entry: SchluterConfigEntry) -> None:
    """Reload the entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)


class SchluterDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Thermostat]]):
    """Coordinate Schluter thermostat data updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: SchluterApi,
        username: str,
        password: str,
    ) -> None:
        """Initialize the coordinator."""
        self._username = username
        self._password = password
        self._api = api
        self._sessionid: str | None = None
        self._last_heating_state: dict[str, bool] = {}
        self._pending_heating_events: dict[str, str] = {}

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),
        )

    @property
    def session_id(self) -> str | None:
        """Return the active Schluter session ID."""
        return self._sessionid

    def pop_heating_event(self, thermostat_id: str) -> str | None:
        """Return and remove a pending heating transition event."""
        return self._pending_heating_events.pop(thermostat_id, None)

    def async_set_updated_data(self, data: dict[str, Thermostat]) -> None:
        """Set coordinator data and keep transition tracking consistent."""
        self._capture_heating_transitions(data)
        super().async_set_updated_data(data)

    async def _async_update_data(self) -> dict[str, Thermostat]:
        """Fetch thermostat data from the API."""
        try:
            async with async_timeout.timeout(10):
                if self._sessionid is None:
                    self._sessionid = await self._api.async_get_sessionid(
                        self._username,
                        self._password,
                    )

                session_timestamp = self._api.sessionid_timestamp
                if session_timestamp is None:
                    self._sessionid = await self._api.async_get_sessionid(
                        self._username,
                        self._password,
                    )
                else:
                    expiration_timestamp = dt_util.as_utc(
                        session_timestamp + timedelta(days=1)
                    )
                    if expiration_timestamp <= dt_util.utcnow():
                        self._sessionid = await self._api.async_get_sessionid(
                            self._username,
                            self._password,
                        )

                thermostats = await self._api.async_get_current_thermostats(
                    self._sessionid
                )
                self._capture_heating_transitions(thermostats)
                return thermostats

        except InvalidSessionIdError:
            try:
                self._sessionid = await self._api.async_get_sessionid(
                    self._username,
                    self._password,
                )
                thermostats = await self._api.async_get_current_thermostats(
                    self._sessionid
                )
                self._capture_heating_transitions(thermostats)
                return thermostats

            except InvalidUserPasswordError as err:
                raise ConfigEntryAuthFailed from err

            except (ApiError, ClientConnectorError) as err:
                raise UpdateFailed(err) from err

        except InvalidUserPasswordError as err:
            raise ConfigEntryAuthFailed from err

        except (ApiError, ClientConnectorError) as err:
            raise UpdateFailed(err) from err

    def _capture_heating_transitions(self, thermostats: dict[str, Thermostat]) -> None:
        """Track heating transitions for event entities."""
        for thermostat_id, thermostat in thermostats.items():
            is_heating = thermostat.is_heating
            if thermostat_id in self._last_heating_state:
                previous = self._last_heating_state[thermostat_id]
                if is_heating != previous:
                    self._pending_heating_events[thermostat_id] = (
                        HEATING_STARTED_EVENT if is_heating else HEATING_STOPPED_EVENT
                    )
            self._last_heating_state[thermostat_id] = is_heating


@dataclass
class SchluterData:
    """Runtime data for Schluter integration."""

    api: SchluterApi
    coordinator: SchluterDataUpdateCoordinator
    metadata: dict[str, Any] = field(default_factory=dict)
