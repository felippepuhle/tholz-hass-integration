"""Water heater current temperature across legacy and current structures."""

import pytest

from custom_components.tholz.entities.heating.heating_water_heater import (
    get_heating_water_heaters,
)


@pytest.mark.asyncio
async def test_smartheat_v1_current_temperature_falls_back_to_t2(
    hass, entry, manager, client
):
    """Legacy SmartHeat 1st gen exposes only t1/t2; current temperature uses t2."""
    client.get_status.return_value = {
        "id": 21392,
        "heating": {
            "on": False,
            "mode": 3,
            "opMode": 3,
            "unit": True,
            "t1": 550,
            "t2": 450,
            "sp": 450,
            "maxSp": 600,
        },
    }
    data = await manager.get_status()
    water_heater = get_heating_water_heaters(hass, entry, manager, data)[0]
    await water_heater.async_update()
    assert water_heater.current_temperature == 45.0
    assert water_heater.target_temperature == 45.0


@pytest.mark.asyncio
async def test_current_temperature_prefers_t3_when_available(
    hass, entry, manager, client
):
    """Structures that expose t3 keep using it as the current temperature."""
    client.get_status.return_value = {
        "id": 21505,
        "heatings": {
            "h1": {"type": 3, "t1": 245, "t2": 251, "t3": 463, "sp": 420},
        },
    }
    data = await manager.get_status()
    water_heater = get_heating_water_heaters(hass, entry, manager, data)[0]
    await water_heater.async_update()
    assert water_heater.current_temperature == 46.3
