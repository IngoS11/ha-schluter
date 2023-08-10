"""Tests for Schluter Home Assistant Custom Component integration"""
from unittest.mock import AsyncMock, patch
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_TOKEN, CONF_NAME
from homeassistant.core import HomeAssistant

from custom_components.schluter.const import DOMAIN

from .common import MockConfigEntry


NAME = "Schluter DIETRA"
TOKEN = "abcd1234"

CONF_INPUT = {CONF_API_TOKEN: TOKEN}

CONF_DATA = {CONF_API_TOKEN: TOKEN, CONF_NAME: NAME}


def create_entry(hass: HomeAssistant) -> ConfigEntry:
    """Add config entry in Home Assistant"""
    entry = MockConfigEntry(domain=DOMAIN, data=CONF_DATA, unique_id="0123456789")
    entry.add_to_hass(hass)
    return entry


def mocked_schluter_info():
    """Created mocked Schluter"""
    mocked_schluter = AsyncMock()
    mocked_schluter.id = "0123456789"
    mocked_schluter.name = NAME
    return patch(
        "custom_components.schluter.config_flow.nextcord.Client.application_info",
        return_value=mocked_schluter,
    )


def patch_schluter_login():
    """Patch schluter info."""
    return patch("custom_components.schluter.config_flow.aioschluter.SchluterAPI")
