"""Existing write contracts are unchanged; writes never reach a controller."""

from copy import deepcopy
import asyncio
from threading import Event

import pytest
from homeassistant.components.water_heater import (
    STATE_OFF,
    STATE_PERFORMANCE,
    STATE_HEAT_PUMP,
)
from homeassistant.exceptions import HomeAssistantError

from custom_components.tholz.entities.heating.heating_switch import get_heating_switches
from custom_components.tholz.entities.heating.heating_water_heater import (
    get_heating_water_heaters,
)
from custom_components.tholz.entities.led.led_light import get_led_lights
from custom_components.tholz.entities.led.led_effect_speed_number import (
    get_led_effect_speed_numbers,
)
from custom_components.tholz.entities.output.output_switch import get_output_switches


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("heating_type", "on", "op_mode", "on_aut"),
    [
        (5, True, 1, None),
        (5, False, 0, None),
        (4, True, 1, None),
        (4, False, 0, None),
        (10, True, 1, False),
        (10, False, 0, False),
        (3, True, 0, None),
    ],
)
async def test_existing_switch_command_fields(
    hass, entry, manager, client, device_data, heating_type, on, op_mode, on_aut
):
    channel = {
        "type": heating_type,
        "t1": 245,
        "t2": 251,
        "t3": 252,
        "sp": 390,
        "on": False,
        "opMode": 0,
    }
    device_data["heatings"] = {"h1": channel}
    data = await manager.get_status()
    entity = get_heating_switches(hass, entry, manager, data)[0]
    client.set_status.return_value = True
    if on:
        await entity.async_turn_on()
    else:
        await entity.async_turn_off()
    expected = deepcopy(channel)
    expected.update({"on": on, "opMode": op_mode})
    if on_aut is not None:
        expected["onAut"] = on_aut
    client.set_status.assert_called_once_with({"heatings": {"h1": expected}})
    assert await manager.get_status() == data


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("operation", "on", "on_aut", "op_mode"),
    [
        (STATE_OFF, False, False, 0),
        (STATE_PERFORMANCE, True, False, 1),
        (STATE_HEAT_PUMP, True, True, 2),
    ],
)
async def test_existing_thermostat_water_heater_command_fields(
    hass, entry, manager, client, device_data, operation, on, on_aut, op_mode
):
    channel = {"type": 10, "t1": 245, "sp": 390, "on": False, "opMode": 0}
    device_data["heatings"] = {"h1": channel}
    data = await manager.get_status()
    entity = get_heating_water_heaters(hass, entry, manager, data)[0]
    client.set_status.return_value = data
    await entity.async_set_operation_mode(operation)
    expected = {**channel, "on": on, "onAut": on_aut, "opMode": op_mode}
    client.set_status.assert_called_once_with({"heatings": {"h1": expected}})
    assert await manager.get_status() == data


@pytest.mark.asyncio
async def test_failed_water_heater_setpoint_write_does_not_change_read_snapshot(
    hass, entry, manager, client
):
    data = await manager.get_status()
    entity = get_heating_water_heaters(hass, entry, manager, data)[0]
    client.set_status.return_value = False
    original = deepcopy(data)
    await entity.async_set_temperature(temperature=40.5)
    expected = deepcopy(original["heatings"]["h1"])
    expected["sp"] = 405
    client.set_status.assert_called_once_with({"heatings": {"h1": expected}})
    assert await manager.get_sensor_status() == original
    assert len(get_heating_water_heaters(hass, entry, manager, data)) == 1


@pytest.mark.asyncio
async def test_chained_heater_commands_preserve_latest_response_across_platforms(
    hass, entry, manager, client, device_data
):
    channel = {
        "type": 10,
        "t1": 245,
        "sp": 390,
        "on": True,
        "onAut": True,
        "opMode": 2,
    }
    device_data["heatings"] = {"h1": channel}
    data = await manager.get_status()
    heater = get_heating_water_heaters(hass, entry, manager, data)[0]
    switch = get_heating_switches(hass, entry, manager, data)[0]
    controller = deepcopy(data)
    writes = []

    def write(payload):
        writes.append(deepcopy(payload))
        controller["heatings"].update(deepcopy(payload["heatings"]))
        return deepcopy(controller)

    client.set_status.side_effect = write
    successful = manager.last_successful_read
    await heater.async_set_operation_mode(STATE_PERFORMANCE)
    await heater.async_set_temperature(temperature=40.5)
    assert writes[1]["heatings"]["h1"] == {
        **channel,
        "on": True,
        "onAut": False,
        "opMode": 1,
        "sp": 405,
    }
    await switch.async_turn_off()
    assert writes[2]["heatings"]["h1"] == {
        **channel,
        "on": False,
        "onAut": False,
        "opMode": 0,
        "sp": 405,
    }
    assert manager.last_successful_read == successful
    assert client.get_status.call_count == 1


@pytest.mark.asyncio
async def test_separate_led_entities_preserve_chained_on_and_brightness(
    hass, entry, manager, client, device_data
):
    channel = {"type": 1, "on": False, "brightness": 100, "effect": 255, "speed": 10}
    device_data["leds"] = {"l1": channel}
    data = await manager.get_status()
    light = get_led_lights(hass, entry, manager, data)[0]
    speed = get_led_effect_speed_numbers(hass, entry, manager, data)[0]
    await light.async_update()
    await speed.async_update()
    controller = deepcopy(data)
    writes = []

    def write(payload):
        writes.append(deepcopy(payload))
        controller["leds"].update(deepcopy(payload["leds"]))
        return deepcopy(controller)

    client.set_status.side_effect = write
    successful = manager.last_successful_read
    await light.async_turn_on(brightness=128)
    await speed.async_set_native_value(35)
    assert writes[1]["leds"]["l1"] == {
        **channel,
        "on": True,
        "brightness": 50,
        "speed": 35,
    }
    assert manager.last_successful_read == successful
    assert client.get_status.call_count == 1


@pytest.mark.asyncio
async def test_command_waits_for_inflight_poll_before_building_payload(
    hass, entry, manager, client, device_data
):
    device_data["heatings"] = {
        "h1": {
            "type": 10,
            "t1": 245,
            "sp": 390,
            "on": True,
            "onAut": True,
            "opMode": 2,
        },
    }
    data = await manager.get_status()
    heater = get_heating_water_heaters(hass, entry, manager, data)[0]
    polled = deepcopy(data)
    polled["heatings"]["h1"].update(opMode=1, onAut=False)
    entered = Event()
    release = Event()
    writer_entered = asyncio.Event()

    def read():
        entered.set()
        assert release.wait(timeout=2)
        return polled

    async def poll():
        async with manager._lock:
            await manager._fetch_data()

    async def command():
        writer_entered.set()
        await heater.async_set_temperature(temperature=40.5)

    client.get_status.side_effect = read
    client.set_status.return_value = True
    poll_task = asyncio.create_task(poll())
    command_task = None
    try:
        assert await asyncio.to_thread(entered.wait, 1)
        command_task = asyncio.create_task(command())
        await writer_entered.wait()
        await asyncio.sleep(0)
        client.set_status.assert_not_called()
    finally:
        release.set()
        await poll_task
        if command_task is not None:
            await command_task
    client.set_status.assert_called_once_with(
        {
            "heatings": {"h1": {**polled["heatings"]["h1"], "sp": 405}},
        }
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("lost_read", ["failed", "expired"])
async def test_heater_command_retries_lost_read_before_writing(
    hass, entry, manager, client, device_data, clock, lost_read
):
    device_data["heatings"] = {
        "h1": {
            "type": 10,
            "t1": 245,
            "sp": 390,
            "on": True,
            "onAut": True,
            "opMode": 2,
        },
    }
    data = await manager.get_status()
    heater = get_heating_water_heaters(hass, entry, manager, data)[0]
    identity = (heater.unique_id, heater.name, heater.device_info)
    if lost_read == "failed":
        client.get_status.return_value = None
        await manager._fetch_data()
    else:
        clock[0] += 21
    calls = client.get_status.call_count
    assert await manager.get_sensor_status() is None
    assert client.get_status.call_count == calls
    recovered = deepcopy(data)
    recovered["heatings"]["h1"].update(opMode=1, onAut=False)
    client.get_status.return_value = recovered
    client.set_status.return_value = True
    await heater.async_set_temperature(temperature=40.5)
    client.set_status.assert_called_once_with(
        {
            "heatings": {"h1": {**recovered["heatings"]["h1"], "sp": 405}},
        }
    )
    assert client.get_status.call_count == calls + 1
    assert (heater.unique_id, heater.name, heater.device_info) == identity
    assert heater.target_temperature == 40.5


@pytest.mark.asyncio
@pytest.mark.parametrize("command", ["temperature", "operation", "switch"])
@pytest.mark.parametrize("lost_read", ["failed", "expired"])
async def test_offline_heating_command_fails_cleanly_without_corrupting_state(
    hass, entry, manager, client, device_data, clock, command, lost_read
):
    device_data["heatings"] = {
        "h1": {
            "type": 10,
            "t1": 245,
            "sp": 390,
            "on": True,
            "onAut": True,
            "opMode": 2,
        },
    }
    data = await manager.get_status()
    heater = get_heating_water_heaters(hass, entry, manager, data)[0]
    switch = get_heating_switches(hass, entry, manager, data)[0]
    entity = switch if command == "switch" else heater
    identity = (entity.unique_id, entity.name, entity.device_info)
    original = deepcopy(entity._state)
    client.get_status.return_value = None
    if lost_read == "failed":
        await manager._fetch_data()
    else:
        clock[0] += 21
    calls = client.get_status.call_count
    if command == "temperature":
        action = heater.async_set_temperature(temperature=40.5)
    elif command == "operation":
        action = heater.async_set_operation_mode(STATE_PERFORMANCE)
    else:
        action = switch.async_turn_off()
    with pytest.raises(HomeAssistantError, match="unavailable"):
        await action
    assert client.get_status.call_count == calls + 1
    client.set_status.assert_not_called()
    assert entity._state == original
    assert (entity.unique_id, entity.name, entity.device_info) == identity
    assert await manager.get_sensor_status() is None
    assert client.get_status.call_count == calls + 1


@pytest.mark.asyncio
async def test_non_heating_update_inherits_offline_error_and_recovers(
    hass, entry, manager, client, device_data, clock
):
    device_data["outputs"] = {"o1": {"id": 0, "on": False}}
    data = await manager.get_status()
    entity = get_output_switches(hass, entry, manager, data)[0]
    await entity.async_update()
    original = deepcopy(entity._state)
    identity = (entity.unique_id, entity.name, entity.device_info)
    clock[0] += 21
    client.get_status.return_value = None
    with pytest.raises(HomeAssistantError, match=r"^Controller unavailable$"):
        await entity.async_update()
    assert entity._state == original
    assert (entity.unique_id, entity.name, entity.device_info) == identity
    assert not manager._lock.locked()
    client.set_status.assert_not_called()
    recovered = deepcopy(data)
    recovered["outputs"]["o1"]["on"] = True
    client.get_status.return_value = recovered
    await asyncio.wait_for(entity.async_update(), timeout=1)
    assert entity.is_on
    assert (entity.unique_id, entity.name, entity.device_info) == identity
    assert client.get_status.call_count == 3
    client.set_status.assert_not_called()
