"""Fixtures for Schluter integration tests."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.schluter.const import DOMAIN


@dataclass
class ApiBehavior:
    """Behavior switches for fake API."""

    invalid_credentials: bool = False
    cannot_connect: bool = False


@pytest.fixture
def thermostat_payload() -> dict[str, Any]:
    """Return mutable thermostat payload used by fake API."""
    return {
        "thermostat_1": SimpleNamespace(
            name="Living Room",
            serial_number="SERIAL123",
            sw_version="1.0.0",
            regulation_mode=2,
            temperature=21.5,
            is_heating=False,
            set_point_temp=22.0,
            min_temp=5.0,
            max_temp=35.0,
            load_measured_watt=1000,
            kwh_charge=0.15,
            is_online=True,
        )
    }


@pytest.fixture
def patch_schluter_api(
    monkeypatch: pytest.MonkeyPatch,
    thermostat_payload: dict[str, Any],
) -> ApiBehavior:
    """Patch Schluter API with a controllable fake implementation."""
    from aioschluter import ApiError, InvalidUserPasswordError

    behavior = ApiBehavior()

    class FakeSchluterApi:
        """Test double for Schluter API."""

        def __init__(self, websession: Any) -> None:
            self.sessionid = "test-session"
            self.sessionid_timestamp = dt_util.utcnow()

        async def async_get_sessionid(self, username: str, password: str) -> str:
            if behavior.invalid_credentials:
                raise InvalidUserPasswordError(401)
            if behavior.cannot_connect:
                raise ApiError(500)

            self.sessionid = f"{username}-session"
            self.sessionid_timestamp = dt_util.utcnow()
            return self.sessionid

        async def async_get_current_thermostats(self, sessionid: str) -> dict[str, Any]:
            return {
                thermostat_id: SimpleNamespace(**vars(thermostat))
                for thermostat_id, thermostat in thermostat_payload.items()
            }

        async def async_set_regulation_mode(
            self, sessionid: str, serial_number: str, regulation_mode: int
        ) -> None:
            for thermostat in thermostat_payload.values():
                if thermostat.serial_number == serial_number:
                    thermostat.regulation_mode = regulation_mode

        async def async_set_temperature(
            self, sessionid: str, serial_number: str, target_temp: float
        ) -> None:
            for thermostat in thermostat_payload.values():
                if thermostat.serial_number == serial_number:
                    thermostat.set_point_temp = target_temp

    monkeypatch.setattr("custom_components.schluter.SchluterApi", FakeSchluterApi)
    monkeypatch.setattr(
        "custom_components.schluter.config_flow.SchluterApi", FakeSchluterApi
    )

    return behavior


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock Schluter config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_USERNAME: "test_user", CONF_PASSWORD: "test_pass"},
        unique_id="test_user",
    )


@pytest.fixture
async def setup_integration(
    hass,
    mock_config_entry: MockConfigEntry,
    patch_schluter_api: ApiBehavior,
) -> MockConfigEntry:
    """Set up the Schluter integration and return the entry."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
