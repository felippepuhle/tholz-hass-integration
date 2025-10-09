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
