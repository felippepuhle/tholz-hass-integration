[![GitHub Release](https://img.shields.io/github/release/felippepuhle/tholz-hass-integration.svg?style=flat-square)](https://github.com/felippepuhle/tholz-hass-integration/releases)
[![License](https://img.shields.io/github/license/felippepuhle/tholz-hass-integration.svg?style=flat-square)](LICENSE)

# Tholz Home Assistant Integration

This custom integration provides control and monitoring for **Tholz Smart devices**. The following models have been tested:

- **Tholz Smart Pool v2**  
- **Tholz Smart Heat v2**  

### Features

- **Sensors & Binary Sensors** (e.g., header and temperature sensors)  
- **Water Heater Control** (heating entities)  
- **Pump Controls** (switch entities)  

> ⚠️ Some entities, such as lights, are still under development and will be added in future updates.

## Installation

We are working towards publishing this integration in [HACS](https://hacs.xyz). In the meantime, you can install it manually:

1. Add this repository as a **custom repository** in HACS: [https://github.com/felippepuhle/tholz-hass-integration](https://github.com/felippepuhle/tholz-hass-integration)  
   - (select the **Integration** category)
2. Search for **“Tholz”** and install the integration.
3. Restart Home Assistant.

## Configuration

After restarting, add the integration via the **Home Assistant UI**:

1. Go to **Settings → Devices & Services → Add Integration → Tholz**.

   <img src="https://iili.io/KAXQ6bI.png" alt="step1" height="200">

2. Provide the required information:  

   <img src="https://iili.io/KAXQrRp.png" alt="step2" height="400">

     - **Name**: Friendly name for your device  
     - **IP Address**: Device IP address  
     - **Port**: Socket connection port  
     - **Polling Interval**: How often (in seconds) device data is refreshed

## Example configuration in action

**Controls:**  
<img src="https://iili.io/KAXQixt.png" alt="controls" style="max-height:200px;">

**Sensors:**  
<img src="https://iili.io/KAXQLsn.png" alt="sensors" style="max-height:200px;">
