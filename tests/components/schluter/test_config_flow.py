"""Test Schluter config flow."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from custom_components.schluter.const import (
    CONF_ENABLE_ENERGY_SENSOR,
    CONF_ENABLE_HEATING_EVENT,
    CONF_ENABLE_ONLINE_STATUS_SENSOR,
    DOMAIN,
)


async def test_user_flow_success(hass, patch_schluter_api) -> None:
    """Test successful user config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test_user", CONF_PASSWORD: "test_pass"},
    )

    assert result["type"] == "create_entry"
    assert result["title"] == "test_user"


async def test_user_flow_invalid_credentials(hass, patch_schluter_api) -> None:
    """Test config flow invalid credentials path."""
    patch_schluter_api.invalid_credentials = True

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test_user", CONF_PASSWORD: "bad_pass"},
    )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_user_pass"}


async def test_user_flow_cannot_connect(hass, patch_schluter_api) -> None:
    """Test config flow connection failure path."""
    patch_schluter_api.cannot_connect = True

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test_user", CONF_PASSWORD: "test_pass"},
    )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_options_flow_init(hass, mock_config_entry) -> None:
    """Test options flow opens and saves values."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] == "form"
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ENABLE_ONLINE_STATUS_SENSOR: False,
            CONF_ENABLE_ENERGY_SENSOR: False,
            CONF_ENABLE_HEATING_EVENT: False,
        },
    )
    assert result["type"] == "create_entry"
    assert result["data"] == {
        CONF_ENABLE_ONLINE_STATUS_SENSOR: False,
        CONF_ENABLE_ENERGY_SENSOR: False,
        CONF_ENABLE_HEATING_EVENT: False,
    }
