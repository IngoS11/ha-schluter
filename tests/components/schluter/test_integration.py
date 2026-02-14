"""Test Schluter integration behavior."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from homeassistant.components.climate.const import PRESET_AWAY
from homeassistant.helpers import entity_registry as er

from custom_components.schluter.const import (
    CONF_ENABLE_ENERGY_SENSOR,
    CONF_ENABLE_HEATING_EVENT,
    CONF_ENABLE_ONLINE_STATUS_SENSOR,
)
from custom_components.schluter.diagnostics import async_get_config_entry_diagnostics


async def test_unique_ids_use_serial_number(hass, setup_integration) -> None:
    """Test entities use serial-based unique IDs."""
    registry = er.async_get(hass)
    schluter_entries = er.async_entries_for_config_entry(
        registry, setup_integration.entry_id
    )

    assert schluter_entries
    for entry in schluter_entries:
        assert "SERIAL123" in entry.unique_id


async def test_options_disable_optional_entities(
    hass, patch_schluter_api
) -> None:
    """Test options flow toggles optional entity creation."""
    from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    mock_config_entry = MockConfigEntry(
        domain="schluter",
        data={CONF_USERNAME: "test_user", CONF_PASSWORD: "test_pass"},
        options={
            CONF_ENABLE_ONLINE_STATUS_SENSOR: False,
            CONF_ENABLE_ENERGY_SENSOR: False,
            CONF_ENABLE_HEATING_EVENT: False,
        },
        unique_id="test_user",
    )
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.living_room_energy") is None
    assert hass.states.get("binary_sensor.living_room_online_status") is None
    assert hass.states.get("event.living_room_heating_event") is None


async def test_climate_preset_mode(hass, setup_integration, thermostat_payload) -> None:
    """Test climate preset mode support and API mapping."""
    registry = er.async_get(hass)
    climate_entries = [
        entry
        for entry in er.async_entries_for_config_entry(
            registry, setup_integration.entry_id
        )
        if entry.domain == "climate"
    ]
    climate_entity_id = climate_entries[0].entity_id

    await hass.services.async_call(
        "climate",
        "set_preset_mode",
        {"entity_id": climate_entity_id, "preset_mode": PRESET_AWAY},
        blocking=True,
    )

    assert thermostat_payload["thermostat_1"].regulation_mode == 3


async def test_energy_sensor_uses_elapsed_time(
    hass, setup_integration, thermostat_payload, monkeypatch
) -> None:
    """Test energy sensor uses elapsed-time accumulation."""
    base = datetime(2026, 1, 1, 0, 0, 0)
    monkeypatch.setattr(
        "custom_components.schluter.sensor.dt_util.utcnow", lambda: base
    )

    coordinator = setup_integration.runtime_data.coordinator
    first = SimpleNamespace(**vars(coordinator.data["thermostat_1"]))
    first.is_heating = True
    first.load_measured_watt = 1000
    coordinator.async_set_updated_data({"thermostat_1": first})
    await hass.async_block_till_done()

    monkeypatch.setattr(
        "custom_components.schluter.sensor.dt_util.utcnow",
        lambda: base + timedelta(hours=1),
    )
    second = SimpleNamespace(**vars(first))
    coordinator.async_set_updated_data({"thermostat_1": second})
    await hass.async_block_till_done()

    energy_state = hass.states.get("sensor.living_room_energy")
    assert energy_state is not None
    assert float(energy_state.state) == pytest.approx(1.0, rel=1e-2)


async def test_heating_event_entity(
    hass, setup_integration, thermostat_payload
) -> None:
    """Test heating transition event entity emits event types."""
    coordinator = setup_integration.runtime_data.coordinator

    first = SimpleNamespace(**vars(coordinator.data["thermostat_1"]))
    first.is_heating = True
    coordinator.async_set_updated_data({"thermostat_1": first})
    await hass.async_block_till_done()

    event_state = hass.states.get("event.living_room_heating_event")
    assert event_state is not None
    assert event_state.attributes.get("event_type") == "heating_started"

    second = SimpleNamespace(**vars(first))
    second.is_heating = False
    coordinator.async_set_updated_data({"thermostat_1": second})
    await hass.async_block_till_done()

    event_state = hass.states.get("event.living_room_heating_event")
    assert event_state is not None
    assert event_state.attributes.get("event_type") == "heating_stopped"


async def test_diagnostics_redacts_sensitive_data(hass, setup_integration) -> None:
    """Test diagnostics output redacts sensitive values."""
    diagnostics = await async_get_config_entry_diagnostics(hass, setup_integration)

    assert diagnostics["entry"]["data"]["password"] == "**REDACTED**"
    assert "test_pass" not in str(diagnostics)


async def test_coordinator_handles_non_expired_naive_session_timestamp(
    hass, setup_integration, monkeypatch
) -> None:
    """Test coordinator refresh works with non-expired naive session timestamp."""
    coordinator = setup_integration.runtime_data.coordinator
    coordinator._sessionid = "existing-session"
    coordinator._api.sessionid_timestamp = datetime(2026, 1, 31, 0, 0, 1)

    now = datetime(2026, 2, 1, 0, 0, 0, tzinfo=UTC)
    monkeypatch.setattr("custom_components.schluter.dt_util.utcnow", lambda: now)

    await coordinator.async_refresh()

    assert coordinator.last_update_success
    assert coordinator.session_id == "existing-session"


async def test_coordinator_renews_expired_naive_session_timestamp(
    hass, setup_integration, monkeypatch
) -> None:
    """Test coordinator renews an expired naive session timestamp."""
    coordinator = setup_integration.runtime_data.coordinator
    coordinator._sessionid = "stale-session"
    coordinator._api.sessionid_timestamp = datetime(2026, 1, 30, 0, 0, 0)

    now = datetime(2026, 2, 1, 0, 0, 0, tzinfo=UTC)
    monkeypatch.setattr("custom_components.schluter.dt_util.utcnow", lambda: now)

    await coordinator.async_refresh()

    assert coordinator.last_update_success
    assert coordinator.session_id == "test_user-session"
