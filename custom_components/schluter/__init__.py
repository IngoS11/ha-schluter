"""The schluter integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import async_timeout
from aiohttp.client_exceptions import ClientConnectorError
from aioschluter import (
    ApiError,
    InvalidSessionIdError,
    InvalidUserPasswordError,
    SchluterApi,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CLIMATE, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up schluter from a config entry."""
    username: str = entry.data[CONF_USERNAME]
    password: str = entry.data[CONF_PASSWORD]

    _LOGGER.debug("Using username %s to connect to Schluter Api", username)

    websession = async_get_clientsession(hass)
    api = SchluterApi(websession)

    coordinator = SchluterDataUpdateCoordinator(hass, api, username, password)
    await coordinator.async_config_entry_first_refresh()

    schluter_data = SchluterData(api, coordinator)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = schluter_data
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        _LOGGER.debug("Unloading configuration entry %s", entry.entry_id)
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    _LOGGER.debug("Update Listener for entry %s", entry.entry_id)
    await hass.config_entries.async_reload(entry.entry_id)


class SchluterDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Schluter temerature data from API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: SchluterApi,
        username: str,
        password: str,
    ) -> None:
        """Initialize."""
        self._username = username
        self._password = password
        self._api = api
        self._sessionid = None
        self._counter = 0

        update_interval = timedelta(minutes=1)
        _LOGGER.debug("Data will be update every %s", update_interval)

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via schluter library."""
        try:

            async with async_timeout.timeout(10):
                if self._sessionid is None:
                    _LOGGER.info("No Schluter Sessionid found, authenticating")
                    self._sessionid = await self._api.async_get_sessionid(
                        self._username, self._password
                    )
                # add 1 day to the session timestamp to be able to check agains
                # the current time. if the time is expired renew the sessionid.
                # This workaround mediates the missing long lived tokens on
                # ths Schluter API side.
                expiration_timestamp = self._api.sessionid_timestamp + timedelta(
                    days=+1
                )
                _LOGGER.debug(
                    "Sessionid expiration timestamp is: %s",
                    expiration_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                )
                if expiration_timestamp <= datetime.now():
                    _LOGGER.info("Schluter Sessionid is expired, authenticating again")
                    self._sessionid = await self._api.async_get_sessionid(
                        self._username, self._password
                    )
                return await self._api.async_get_current_thermostats(self._sessionid)
        except InvalidSessionIdError as err:
            raise ConfigEntryAuthFailed from err
        except InvalidUserPasswordError as err:
            raise ConfigEntryAuthFailed from err
        except (ApiError, ClientConnectorError) as err:
            raise UpdateFailed(err) from err


@dataclass
class SchluterData:
    """Data for the schluter integration."""

    api: SchluterApi
    coordinator: SchluterDataUpdateCoordinator
