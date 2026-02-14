"""Constants for the Schluter integration."""

from homeassistant.const import Platform

DOMAIN = "schluter"
ZERO_WATTS = 0

PRESET_MANUAL = "manual"
PRESET_SCHEDULE = "schedule"

CONF_ENABLE_ONLINE_STATUS_SENSOR = "enable_online_status_sensor"
CONF_ENABLE_ENERGY_SENSOR = "enable_energy_sensor"
CONF_ENABLE_HEATING_EVENT = "enable_heating_event"

DEFAULT_ENABLE_ONLINE_STATUS_SENSOR = True
DEFAULT_ENABLE_ENERGY_SENSOR = True
DEFAULT_ENABLE_HEATING_EVENT = True

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.EVENT,
]

HEATING_STARTED_EVENT = "heating_started"
HEATING_STOPPED_EVENT = "heating_stopped"
