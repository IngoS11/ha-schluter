# About
This is a work in progress alternative to the default [Schluter integration in Homeassistant](https://www.home-assistant.io/integrations/schluter/) and
is currently in an alpha stage. In comparison to the standard integration this one is built making use the [Integration Setup]((https://my.home-assistant.io/redirect/integrations) and is written using async library.

## Getting Started

### Prerequisites
You need at least one configured [Schluter®-DITRA-HEAT-E-WiFi Thermostat](https://www.schluter.com/schluter-us/en_US/ditra-heat-wifi) in your home. The configuration of you Thermostat will include creting a username and password at [https://ditra-heat-e-wifi.schluter.com/](https://ditra-heat-e-wifi.schluter.com/). This user and password will need to be provided during the configuration in the [Integration Setup](#integration-setup) step.


### HACS Installation

The installation through HACS is not tested yet. Your mileage may vary.

### Manual Installation

1. Open the directory with your Home Assistant configuration (where you find `configuration.yaml`,
   usually `~/.homeassistant/`).
2. If you do not have a `custom_components` directory there, you need to create it.

#### Git clone method

This is a preferred method of manual installation, because it allows you to keep the `git` functionality,
allowing you to manually install updates just by running `git pull origin main` from the created directory.

Now you can clone the repository somewhere else and symlink it to Home Assistant like so:

1. Clone the repo.

```shell
git clone https://github.com/ingos11/ha-schluter.git schluter
```

2. Create the symlink to `schluter` in the configuration directory.
   If you have non standard directory for configuration, use it instead.

```shell
ln -s ha-schluter/custom_components/schluter ~/.homeassistant/custom_components/schluter
```

#### Copy method

1. Download [ZIP](https://github.com/ingos11/ha-schluter/archive/main.zip) with the code.
2. Unpack it.
3. Copy the `custom_components/schluter/` from the unpacked archive to `custom_components`
   in your Home Assistant configuration directory.

### Integration Setup

- Browse to your Home Assistant instance.
- In the sidebar click on [Configuration](https://my.home-assistant.io/redirect/config).
- From the configuration menu select: [Integrations](https://my.home-assistant.io/redirect/integrations).
- In the bottom right, click on the [Add Integration](https://my.home-assistant.io/redirect/config_flow_start?domain=schluter) button.
- From the list, search and select “Schluter”.
- Follow the instruction on screen to complete the set up.
- After completing, the Schluter integration will be immediately available for use.
