"""The schluter integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any

from aiohttp.client_exceptions import ClientConnectorError
from aioschluter import (
    ApiError,
    InvalidSessionIdError,
    InvalidUserPasswordError,
    SchluterApi,
)
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.core_config import Config
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CLIMATE, Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: Config) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    username: str = entry.data[CONF_USERNAME]
    password: str = entry.data[CONF_PASSWORD]

    websession = async_get_clientsession(hass)
    api = SchluterApi(websession)

    coordinator = SchluterDataUpdateCoordinator(hass, api, username, password)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = SchluterData(
        api=api,
        coordinator=coordinator,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


class SchluterDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self,
        hass: HomeAssistant,
        api: SchluterApi,
        username: str,
        password: str,
    ) -> None:
        self._username = username
        self._password = password
        self._api = api
        self._sessionid: str | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            async with async_timeout.timeout(10):
                if self._sessionid is None:
                    self._sessionid = await self._api.async_get_sessionid(
                        self._username,
                        self._password,
                    )

                expiration_timestamp = (
                    self._api.sessionid_timestamp + timedelta(days=1)
                )
                if expiration_timestamp <= datetime.now():
                    self._sessionid = await self._api.async_get_sessionid(
                        self._username,
                        self._password,
                    )

                return await self._api.async_get_current_thermostats(self._sessionid)

        except InvalidSessionIdError:
            try:
                self._sessionid = await self._api.async_get_sessionid(
                    self._username,
                    self._password,
                )
                return await self._api.async_get_current_thermostats(self._sessionid)

            except InvalidUserPasswordError as err:
                raise ConfigEntryAuthFailed from err

            except (ApiError, ClientConnectorError) as err:
                raise UpdateFailed(err) from err

        except InvalidUserPasswordError as err:
            raise ConfigEntryAuthFailed from err

        except (ApiError, ClientConnectorError) as err:
            raise UpdateFailed(err) from err


@dataclass
class SchluterData:
    api: SchluterApi
    coordinator: SchluterDataUpdateCoordinator