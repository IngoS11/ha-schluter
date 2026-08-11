# Schluter integration enhancement spec

## Objective
Refactor the Schluter Home Assistant integration for reliability, maintainability,
and Home Assistant quality compliance while adding high-value user features.

## Current baseline
- Platforms today: `climate`, `sensor`
- Polling coordinator: 60 seconds
- Config flow exists with reauth path
- Sensors are implemented as separate classes
- Energy sensor uses sample averaging, not elapsed-time accumulation
- Several unique IDs are derived from thermostat name, which can change
- No diagnostics platform, options flow, `binary_sensor`, or `event` platform

## Scope
1. Stabilize architecture and entity identity
2. Correct energy calculation logic
3. Modernize entity implementation patterns
4. Add user-visible features: presets, online status, heating events
5. Add tests and validation gates

## Out of scope
- Changing polling interval to be user-configurable
- Replacing `aioschluter` library behavior
- UI/dashboard customization in Home Assistant frontend

## Work plan

### Phase 0: supportability foundation

#### 0.1 Add diagnostics
- Implement `async_get_config_entry_diagnostics` in
  `custom_components/schluter/diagnostics.py`
- Include coordinator thermostat payload for troubleshooting
- Redact sensitive fields (`username`, `password`, `sessionid`, tokens)

Acceptance:
- Diagnostics endpoint returns data for a configured entry
- No secrets are present in diagnostics output

#### 0.2 Add options flow
- Implement `custom_components/schluter/options_flow.py`
- Add toggles for optional entities:
  - online status binary sensor
  - energy sensor
  - heating state event entity
- Persist options in config entry and honor them during entity setup

Acceptance:
- Options can be changed without re-adding integration
- Optional entities follow options after reload

### Phase 1: testing framework

#### 1.1 Test scaffolding
- Add/expand tests under `tests/components/schluter/`
- Create shared fixtures for config entry setup and API behavior

#### 1.2 Mock API fixture
- Provide a fixture that can emulate:
  - one thermostat and multi-thermostat payloads
  - online/offline status
  - heating on/off transitions
  - regulation modes: schedule/manual/away
  - auth and connectivity failures

#### 1.3 Config flow tests
- Cover:
  - success path
  - invalid credentials
  - API/connectivity failures
  - reauth path

Acceptance:
- Config flow tests pass for all expected outcomes

### Phase 2: correctness and refactor

#### 2.1 Unique ID hardening
- Use immutable serial number for entity unique IDs
- Keep device identifiers stable across thermostat rename operations

Acceptance:
- Renaming thermostat in vendor app does not create duplicate entities

#### 2.2 Energy sensor rewrite
- Convert energy entity to stateful accumulation model
- Use elapsed time between updates and measured watts when heating
- Persist running total across restart using restore-state behavior
- Remove sample-window averaging list logic

Acceptance:
- kWh increases only when thermostat is heating
- value persists across restart
- accumulation matches expected value within test tolerance

#### 2.3 Sensor modernization
- Replace duplicated sensor classes with a generic sensor class and
  `SensorEntityDescription`
- Keep behavior and units identical unless explicitly changed by this spec

Acceptance:
- Sensor entities retain expected names, units, and classes
- Reduced duplication in `sensor.py`

### Phase 3: feature expansion

#### 3.1 Climate presets
- Add preset support to climate entity
- Map regulation modes to presets:
  - schedule
  - manual
  - away
  - none fallback
- Implement async preset setter via API

Acceptance:
- Preset mode reflects backend state
- Changing preset mode updates thermostat mode

#### 3.2 Online status binary sensor
- Add `binary_sensor` platform entity using connectivity class
- Surface thermostat online/offline from API data

Acceptance:
- Binary sensor state tracks backend online status

#### 3.3 Heating event entity
- Add `event` platform for heating transitions
- Emit events when `is_heating` changes:
  - `heating_started`
  - `heating_stopped`

Acceptance:
- Events fire exactly on transitions, not on every refresh

### Phase 4: validation and release readiness

#### 4.1 Platform tests
- Add tests for climate, sensor, binary sensor, event, diagnostics, and options
- Include transition and persistence tests for energy/event logic

#### 4.2 Quality checks
- Run and pass:
  - `prek run --all-files`
  - targeted `pytest` for Schluter tests
  - `python -m script.hassfest`

Acceptance:
- All checks pass without suppressing lint/type issues unnecessarily

## Implementation constraints
- Python 3.13+ typing throughout
- Async-only external I/O
- No blocking calls on event loop
- Specific exception handling over broad catches
- User-facing strings in `strings.json`
- Logging must avoid sensitive data

## Definition of done
- Diagnostics implemented and redacting secrets
- Options flow controls optional entities
- Stable unique IDs based on serial number
- Time-based persistent energy accumulation implemented
- Sensor platform refactored to entity descriptions
- Climate presets implemented and mapped correctly
- Online status binary sensor implemented
- Heating transition event entity implemented
- Test coverage added for new and changed behavior
- Hassfest and lint/test checks pass
