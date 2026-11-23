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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("model", "t1", "t4", "expected_temperature"),
    [
        (21505, None, 321, 32.1),
        (21505, 450, 321, 32.1),
        (21505, 450, 0, 0.0),
        (21505, 450, None, None),
        (21505, 450, False, None),
        (21505, 450, "321", None),
        (21392, 450, 321, 45.0),
    ],
)
async def test_thermostat_current_temperature_uses_model_probe(
    hass, entry, manager, client, model, t1, t4, expected_temperature
):
    """The SmartHeat v2 thermostat reads T4, and legacy thermostats read T1."""
    client.get_status.return_value = {
        "id": model,
        "heatings": {
            "heat3": {
                "type": 10,
                "t1": t1,
                "t4": t4,
                "sp": 540,
                "on": False,
                "opMode": 0,
            }
        },
    }
    data = await manager.get_status()
    water_heater = get_heating_water_heaters(hass, entry, manager, data)[0]
    await water_heater.async_update()

    assert water_heater.current_temperature == expected_temperature
    assert water_heater.target_temperature == 54.0
    assert water_heater.current_operation == "off"
    client.set_status.assert_not_called()
