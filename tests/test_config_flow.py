"""Test Home Assitant Schluter Custom Component config flow"""
import pytest

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_API_TOKEN, CONF_SOURCE
from custom_components.schluter.const import DOMAIN

from . import (
    CONF_DATA,
    CONF_INPUT,
    NAME,
    create_entry,
    mocked_schluter_info,
    patch_schluter_login,
)


async def test_flow_user_step_no_input(hass: HomeAssistant) -> None:
    """Test appropriate erro when no input is provided"""
    _result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
    )
    result = await hass.config_entries.flow.async_configure(
        _result["flow_id"], user_input={}
    )

    assert {"base": "missing"} == result["errors"]


# async def test_flow_user(hass: HomeAssistant) -> None:
#     """Test user initialized flow."""
#     result = await hass.config_entries.flow.async_init(
#         DOMAIN,
#         context={"source": context={"source": "user"}
#     )
#     with mocked_schluter_info(), patch_schluter_login():
#         result = await hass.config_entries.flow.async_configure(
#             result["flow_id"],
#             user_input=CONF_INPUT,
#         )
#     assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
#     assert result["title"] == NAME
#     assert result["data"] == CONF_DATA


# @pytest.mark.asyncio
# async def test_flow_user_already_configured(hass: HomeAssistant) -> None:
#     """Test user initialized flow with duplicate server."""
#     create_entry(hass)
#     result = await hass.config_entries.flow.async_init(
#         DOMAIN, context={"source": config_entries.SOURCE_USER}
#     )
#     with mocked_schluter_info(), patch_schluter_login():
#         result = await hass.config_entries.flow.async_configure(
#             result["flow_id"],
#             user_input=CONF_INPUT,
#         )
#     assert result["type"] == data_entry_flow.FlowResultType.ABORT
#     assert result["reason"] == "already_configured"


# @pytest.mark.asyncio
# async def test_flow_user_unkonwn_error(hass: HomeAssistant) -> None:
#    """Test user initialized flow with reachable server."""
#    with patch_schluter_login() as mock:
#        mock.side_effect = Exception
#        result = await hass.config_entries.async_init(
#            DOMAIN,
#            context={"source": config_entries.SOURCE_USER},
#            data=CONF_DATA,
#        )
#    assert result["type"] == data_entry_flow.FlowResultType.FORM
#    assert result["step_id"] == "user"
#    assert result["errors"] == {"base": "unknown"}
#
#    with mocked_schluter_info(), patch_schluter_login():
#        result = await hass.config_entries.flow.async_configure(
#            result["flow_id"],
#            user_input=CONF_INPUT,
#        )
#    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
#    assert result["title"] == NAME
#    assert result["data"] == CONF_DATA


# @pytest.mark.asyncio
# async def test_flow_reauth(hass: HomeAssistant) -> None:
#    """Test a reauth flow."""
#    entry = create_entry(hass)
#    result = await hass.config_entries.flow.async_init(
#        DOMAIN,
#        context={
#            CONF_SOURCE: config_entries.SOURCE_REAUTH,
#            "entry_id": entry.entry_id,
#            "unique_id": entry.unique_id,
#        },
#        data=entry.data,
#    )
#
#    assert result["type"] == data_entry_flow.FlowResultType.FORM
#    assert result["step_id"] == "reauth_confirm"
#
#    new_conf = {CONF_API_TOKEN: "1234567890123"}
#    with patch_schluter_login() as mock:
#        mock.side_effect = nextcord.LoginFailure
#        result = await hass.config_entries.flow.async_configure(
#            result["flow_id"],
#            user_input=new_conf,
#        )
#    assert result["type"] == data_entry_flow.FlowResultType.FORM
#    assert result["step_id"] == "reauth_confim"
#    assert result["errors"] == {"base": "invalid_auth"}
#
#    with mocked_schluter_info(), patch_schluter_login():
#        result = await hass.config_entries.flow.async_configure(
#            result["flow_id"],
#            user_input=new_conf,
#        )
#    assert result["type"] == data_entry_flow.FlowResultType.ABORT
#    assert result["reason"] == "reauth_successful"
#    assert entry.data == CONF_DATA | new_conf
