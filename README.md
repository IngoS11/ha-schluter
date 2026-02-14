[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![ha-schluter](https://img.shields.io/github/v/release/IngoS11/ha-schluter.svg?1)](https://github.com/IngoS11/ha-schluter) ![Maintenance](https://img.shields.io/maintenance/yes/2025.svg)

# Schluter integration for Home Assistant

This custom integration connects Schluter DITRA-HEAT-E-WiFi thermostats to Home Assistant.
It is an alternative to the built-in Schluter integration and uses async I/O through
`aioschluter`.

## Scope and compatibility

- Device support: Schluter DITRA-HEAT-E-WiFi thermostats sold in North America
- Backend: Schluter North America cloud backend
- Not supported: thermostats sold in Europe that use a different cloud backend
- New DITRA-HEAT-E-RS1 thermostats that use https://schluterditraheat.com/ as the backend

## Installation

### HACS

This repository is a custom repository in HACS.

1. Open HACS.
2. Go to Integrations.
3. Open the menu in the top-right corner and select `Custom repositories`.
4. Add `https://github.com/IngoS11/ha-schluter` with category `Integration`.
5. Install the integration and restart Home Assistant.

### Manual

1. Copy `custom_components/schluter/` into your Home Assistant config directory under
   `custom_components/`.
2. Restart Home Assistant.

## Setup

1. In Home Assistant, go to **Settings > Devices & Services**.
2. Select **Add integration**.
3. Search for `Schluter`.
4. Enter your Schluter account username and password.

## Entities and features

### Climate

Each thermostat creates one climate entity with:

- HVAC modes: `heat`, `auto`, `off`
- Target temperature support
- Preset mode support:
  - `manual`
  - `schedule`
  - `away`
  - `none`

### Sensors

Each thermostat creates these sensors:

- `Current Temperature` (`°C`)
- `Target Temperature` (`°C`)
- `Power` (`W`)
- `Price` (`$/kWh`)
- `Energy` (`kWh`, total increasing)

Energy is calculated from elapsed time and measured wattage while heating, and is restored
across Home Assistant restarts.

### Optional entities

You can enable or disable optional entities from the integration options:

- Online status binary sensor (`binary_sensor`)
- Energy sensor (`sensor`)
- Heating event entity (`event`)

Open **Settings > Devices & Services > Schluter > Configure** to change these options.

### Heating transition events

If the heating event entity is enabled, it emits event types when heating state changes:

- `heating_started`
- `heating_stopped`

## Diagnostics

The integration implements a diagnostics endpoint for support troubleshooting.
Sensitive fields such as usernames, passwords, and session IDs are redacted.

## Development

Useful commands:

- `ruff check custom_components/schluter tests/components/schluter`
- `pytest -q tests/components/schluter -q`
- `pytest -q tests -q`

## Known issue

- Changing credentials from the integration UI is not yet implemented.
