[![GitHub Release](https://img.shields.io/github/release/felippepuhle/tholz-hass-integration.svg?style=flat-square)](https://github.com/felippepuhle/tholz-hass-integration/releases)
[![License](https://img.shields.io/github/license/felippepuhle/tholz-hass-integration.svg?style=flat-square)](https://github.com/felippepuhle/tholz-hass-integration/LICENSE)
[![hacs](https://img.shields.io/badge/HACS-default-orange.svg?style=flat-square)](https://hacs.xyz)

# Tholz Home Assistant Integration

This custom integration provides control and monitoring for **Tholz Smart devices**. The following models have been tested:

- **Tholz Smart Pool v2**  
- **Tholz Smart Heat v2**  

### Features

- **Sensors & Binary Sensors** (e.g., header and temperature sensors)  
- **Water Heater Control** (heating entities)  
- **Pump Controls** (switch entities)  

> ⚠️ Some entities are still under development and will be added in future updates.

## Energy consumption

The controller does not measure consumption, but it does report whether the
electric element is energised. Given the element rating, the integration derives
power and accumulated energy from the time the relay stays on.

### Setup

Open the integration options and fill in **the rating of the electric element,
in watts**. A field appears for every electric heating circuit found on the
device; leaving it at `0` keeps the sensors off.

The rating is on the element nameplate, e.g. `5500 W`. Voltage is already
accounted for there, since the nameplate figure is stated for the installation
voltage.

Two sensors are then created per configured circuit:

| Sensor | Unit | Description |
|---|---|---|
| `Potência Apoio Elétrico` | W | Rated power while the relay is on, `0` otherwise |
| `Energia Apoio Elétrico` | kWh | Accumulated energy, restored across restarts |

### Daily and monthly views

The energy sensor is declared as `total_increasing`, so it can be added directly
to the **Energy dashboard**, under *Individual devices*. Daily, monthly and
yearly breakdowns come from there, along with cost if a tariff is configured.

For standalone daily and monthly entities, a `utility_meter` helper works
without any extra code:

```yaml
utility_meter:
  apoio_eletrico_diario:
    source: sensor.tholz_energia_apoio_eletrico
    cycle: daily
  apoio_eletrico_mensal:
    source: sensor.tholz_energia_apoio_eletrico
    cycle: monthly
```

### Accuracy

Consumption is derived, not measured. Accuracy is bounded by two things: the
element rating being correct, and the polling interval, since a relay that
switches between two polls is accounted for from the poll that observed it.

At the default polling interval the error per switching event is bounded by that
interval. For a resistive element that runs in cycles of minutes, this is well
within useful range for tracking monthly consumption.

## Installation

The recommended installation method is via [HACS](https://hacs.xyz/):

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=felippepuhle&repository=tholz-hass-integration&category=integration)

Notes:

- HACS only installs the files; you still need to go to `Settings → Devices & Services` and add the integration manually.  
- For manual installation (advanced users), copy `custom_components/tholz` to your Home Assistant `custom_components` directory.


## Configuration

After restarting, add the integration via the **Home Assistant UI**:

1. Go to **Settings → Devices & Services → Add Integration → Tholz**.

   <img src="https://iili.io/KAXQ6bI.png" alt="step1" width="400">

2. Provide the required information:  

   <img src="https://iili.io/KAXQrRp.png" alt="step2" width="350">

     - **Name**: Friendly name for your device  
     - **IP Address**: Device IP address  
     - **Port**: Socket connection port  
     - **Polling Interval**: How often (in seconds) device data is refreshed

## Example configuration in action

**Controls:**  
<img src="https://iili.io/KAXQixt.png" alt="controls" width="640">

**Sensors:**  
<img src="https://iili.io/KAXQLsn.png" alt="sensors" width="640">
