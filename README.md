[![GitHub Release](https://img.shields.io/github/release/felippepuhle/tholz-hass-integration.svg?style=flat-square)](https://github.com/felippepuhle/tholz-hass-integration/releases)
[![License](https://img.shields.io/github/license/felippepuhle/tholz-hass-integration.svg?style=flat-square)](https://github.com/felippepuhle/tholz-hass-integration/LICENSE)
[![hacs](https://img.shields.io/badge/HACS-default-orange.svg?style=flat-square)](https://hacs.xyz)

# Tholz Home Assistant Integration

This custom integration provides control and monitoring for **Tholz Smart devices**. The following models have been tested:

- **Tholz Smart Pool v2**  
- **Tholz Smart Heat v2**  
- **Tholz TLS Smart**

Chlorinator monitor support is implemented for **THC30, THC45, THC60, and THC80**. It has been tested on the **THC45**; the other chlorinator models have not been independently tested.

### Features

- **Sensors & Binary Sensors** (e.g., header and temperature sensors)  
- **Water Heater Control** (heating entities)  
- **Pump Controls** (switch entities)  
- **Chlorinator monitoring and control**: salt level, water temperature, pool volume, salt required, water to replace, salt status, chlorine generation preset, and operation mode

> ⚠️ Some entities are still under development and will be added in future updates.

## Heating readings and backup targets

Backup heating channels (`APOIO_ELETRICO` and `APOIO_GAS`) expose read-only
**Temperatura Alvo Apoio Elétrico** and **Temperatura Alvo Apoio a Gás** sensors.
Their values come from that channel's native `sp / 10`, in degrees Celsius,
and follow subsequent device reads. They do not use the solar channel's target,
create writable controls, or change existing water-heater/switch behavior.
Legacy devices using `mode` instead of `type` are also supported. A recognized
backup channel can be discovered even when its setpoint is initially missing;
its sensor remains unavailable until a valid value is read.

Heating temperature sensors and these backup target sensors fail closed:

- Failed, empty, or structurally malformed reads invalidate the read cache;
  missing channels, changed channel types, and missing/invalid numbers make the
  corresponding sensors unavailable. Missing values are not reported as zero.
  Numeric zero is valid; booleans, strings, NaN, and infinity are not.
- The last successful native read expires after **three configured polling
  intervals plus five seconds**, allowing missed polls and I/O/publication
  latency. Freshness uses a monotonic clock, not wall time or HA `last_changed`.
  This also detects a stopped or blocked poller without blocking sensor updates
  on the device I/O lock or triggering extra reads from each unavailable entity.
- An identical successful reading restores availability. Command acknowledgements
  (including full or partial command responses) never replace the read snapshot
  or renew its freshness. No per-poll heartbeat attributes are added.
- Existing temperature unique IDs, names, and device association are preserved;
  unavailable readings do not change entity identity.

After installing or updating the integration files, a **Home Assistant restart
is normally required** to load the new code and discover the added sensors.
These regressions are tested offline with the real Home Assistant framework and
mocked device I/O; this does not establish live controller/heating behavior.

## Development tests

With Python 3.13, install `requirements-test.txt` and run:

```sh
python -m pytest -p no:cacheprovider -q
python -m ruff check --no-cache .
python -m ruff format --no-cache --check .
```

The test requirements retain the project's pinned Home Assistant version.
PR CI runs the offline regression suite without controller access.

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
