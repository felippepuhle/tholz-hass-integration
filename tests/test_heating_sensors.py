"""Heating sensor regressions against real SensorEntity classes."""

import asyncio
import logging
from copy import deepcopy
from datetime import timedelta
from importlib import import_module
from threading import Event

import pytest
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers import device_registry, entity_registry
from homeassistant.helpers.entity_platform import EntityPlatform

from custom_components.tholz.entities.heating.heating_temperature_sensor import (
    HeatingTemperatureSensor,
    get_heating_temperature_sensors,
)
from custom_components.tholz.entities.heating.heating_setpoint_sensor import (
    HeatingSetpointSensor,
    get_heating_setpoint_sensors,
)
from custom_components.tholz.sensor import async_setup_entry


@pytest.mark.parametrize(
    "sensor_type", [HeatingTemperatureSensor, HeatingSetpointSensor]
)
def test_heating_sensors_share_dedicated_read_sensor_module(sensor_type):
    module_name = "custom_components.tholz.entities.heating.heating_read_sensor"
    base = sensor_type.__bases__[0]
    assert base.__module__ == module_name
    assert base is import_module(module_name).HeatingReadSensor
    assert issubclass(sensor_type, base)
    assert issubclass(base, SensorEntity)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("factory", "channel", "field"),
    [
        (get_heating_temperature_sensors, "h1", "t1"),
        (get_heating_setpoint_sensors, "h2", "sp"),
    ],
)
@pytest.mark.parametrize(
    "replacement",
    [
        {"type": 10, "t1": 245, "sp": 390},
        {"type": "5", "t1": 245, "sp": 390},
        {"type": True, "t1": 245, "sp": 390},
        {"type": 5.0, "t1": 245, "sp": 390},
        {"t1": 245, "sp": 390},
        {},
        None,
    ],
)
async def test_channel_identity_must_match_reading(
    hass, entry, manager, client, factory, channel, field, replacement
):
    data = await manager.get_status()
    entity = factory(hass, entry, manager, data)[0]
    identity = (entity.unique_id, entity.name, entity.device_info)
    broken = deepcopy(data)
    broken["heatings"][channel] = replacement
    client.get_status.return_value = broken
    await manager._fetch_data()
    await entity.async_update()
    assert not entity.available
    assert entity.native_value is None
    assert (entity.unique_id, entity.name, entity.device_info) == identity
    client.get_status.return_value = data
    await manager._fetch_data()
    await entity.async_update()
    assert entity.available
    assert entity.native_value == data["heatings"][channel][field] / 10


@pytest.mark.asyncio
async def test_sensor_platform_adds_dynamic_read_only_backup_targets(
    hass, entry, manager, client
):
    hass.data["tholz"] = {entry.entry_id: {"manager": manager}}
    entities = []

    def add_entities(new_entities, *, update_before_add):
        assert update_before_add
        entities.extend(new_entities)

    await async_setup_entry(hass, entry, add_entities)
    targets = [entity for entity in entities if entity.unique_id.endswith("_setpoint")]
    assert len(targets) == 2
    assert [(entity.unique_id, entity.name) for entity in targets] == [
        (
            "tholz_test-entry_heating_h2_sp_setpoint",
            "Controlador Temperatura Alvo Apoio Elétrico",
        ),
        (
            "tholz_test-entry_heating_h3_sp_setpoint",
            "Controlador Temperatura Alvo Apoio a Gás",
        ),
    ]
    for entity in targets:
        assert isinstance(entity, SensorEntity)
        assert entity.device_class == "temperature"
        assert entity.native_unit_of_measurement == "°C"
        assert not hasattr(entity, "async_set_temperature")
        await entity.async_update()
    assert [entity.native_value for entity in targets] == [39, 41]
    next_data = await manager.get_status()
    next_data["heatings"]["h1"]["sp"] = 990
    next_data["heatings"]["h2"]["sp"] = 405
    client.get_status.return_value = next_data
    await manager._fetch_data()
    await targets[0].async_update()
    assert targets[0].native_value == 40.5
    client.set_status.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("raw", [None, True, "390", float("nan"), float("inf"), 0])
async def test_backup_target_discovery_without_temperature(
    hass, entry, manager, device_data, raw
):
    device_data["heatings"]["h2"] = {"type": 5, "sp": raw}
    hass.data["tholz"] = {entry.entry_id: {"manager": manager}}
    entities = []
    await async_setup_entry(hass, entry, lambda new, **_kwargs: entities.extend(new))
    target = next(
        entity
        for entity in entities
        if entity.unique_id == "tholz_test-entry_heating_h2_sp_setpoint"
    )
    await target.async_update()
    assert target.available == (raw == 0)
    assert target.native_value == (0 if raw == 0 else None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure", [None, {}, OSError("read failed"), {"heatings": []}]
)
async def test_temperature_read_failure_recovers_same_value(
    hass, manager, client, entry, failure
):
    data = await manager.get_status()
    entity = get_heating_temperature_sensors(None, entry, manager, data)[0]
    assert isinstance(entity, SensorEntity)
    await entity.async_update()
    entity.hass = hass
    identity = (entity.unique_id, entity.name, entity.device_info)
    assert entity.state == 24.5
    assert entity.available
    client.get_status.side_effect = [failure, data]
    await manager._fetch_data()
    await entity.async_update()
    assert not entity.available
    assert entity.state is None
    assert (entity.unique_id, entity.name, entity.device_info) == identity
    await manager._fetch_data()
    await entity.async_update()
    assert entity.available
    assert entity.state == 24.5
    assert (entity.unique_id, entity.name, entity.device_info) == identity


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "raw", [None, True, False, "245", float("nan"), float("inf"), -float("inf")]
)
async def test_temperature_invalid_number_is_unavailable(
    hass, manager, client, entry, raw
):
    data = await manager.get_status()
    entity = get_heating_temperature_sensors(None, entry, manager, data)[0]
    broken = deepcopy(data)
    entity.hass = hass
    broken["heatings"]["h1"]["t1"] = raw
    client.get_status.return_value = broken
    await manager._fetch_data()
    await entity.async_update()
    assert not entity.available
    assert entity.state is None
    assert entity.name == "Controlador Temperatura Coletor"


@pytest.mark.asyncio
async def test_zero_temperature_is_not_missing_at_discovery(
    hass, manager, entry, device_data
):
    for key in ("t1", "t2", "t3"):
        device_data["heatings"]["h1"][key] = 0
    data = await manager.get_status()
    entities = get_heating_temperature_sensors(None, entry, manager, data)
    assert len(entities) == 3
    entities[0].hass = hass
    assert entities[0].unique_id == "tholz_test-entry_heating_h1_t1_temperature"
    await entities[0].async_update()
    assert entities[0].available
    assert entities[0].state == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "factory", [get_heating_temperature_sensors, get_heating_setpoint_sensors]
)
async def test_real_ha_publication_expires_while_device_read_is_blocked(
    hass, entry, manager, client, clock, factory
):
    data = await manager.get_status()
    entity = factory(hass, entry, manager, data)[0]
    entity.entity_id = "sensor.test_reading"
    if setup_registry := getattr(device_registry, "async_setup", None):
        setup_registry(hass)
    await device_registry.async_load(hass)
    await entity_registry.async_load(hass)
    platform = EntityPlatform(
        hass=hass,
        logger=logging.getLogger(__name__),
        domain="sensor",
        platform_name="tholz",
        platform=None,
        scan_interval=timedelta(seconds=1),
        entity_namespace=None,
    )
    entity.add_to_platform_start(hass, platform, None)
    await entity.async_update()
    await entity.add_to_platform_finish()
    first = hass.states.get(entity.entity_id)
    assert first.state != "unavailable"
    attributes = first.attributes
    # A successful identical read must not add a heartbeat or churn attributes.
    clock[0] += 1
    await manager._fetch_data()
    await entity.async_update()
    entity.async_write_ha_state()
    assert hass.states.get(entity.entity_id).attributes == attributes
    assert hass.states.get(entity.entity_id).last_changed == first.last_changed
    entered = Event()
    release = Event()

    def blocked_read():
        entered.set()
        release.wait(timeout=2)
        return data

    async def fetch():
        async with manager._lock:
            await manager._fetch_data()

    client.get_status.side_effect = blocked_read
    task = asyncio.create_task(fetch())
    try:
        assert await asyncio.to_thread(entered.wait, 1)
        clock[0] += 21
        await asyncio.wait_for(entity.async_update(), timeout=0.1)
        entity.async_write_ha_state()
        assert hass.states.get(entity.entity_id).state == "unavailable"
        assert entity.native_value is None
    finally:
        release.set()
        await task
    await entity.async_update()
    entity.async_write_ha_state()
    assert hass.states.get(entity.entity_id).state == first.state
    assert hass.states.get(entity.entity_id).attributes == attributes


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "factory", [get_heating_temperature_sensors, get_heating_setpoint_sensors]
)
@pytest.mark.parametrize("failure", [None, OSError("read failed"), {"heatings": []}])
async def test_read_only_sensor_failure_and_recovery(
    hass, entry, manager, client, factory, failure
):
    data = await manager.get_status()
    entity = factory(hass, entry, manager, data)[0]
    await entity.async_update()
    value = entity.native_value
    identity = (entity.unique_id, entity.name, entity.device_info)
    client.get_status.side_effect = [failure, data]
    await manager._fetch_data()
    await entity.async_update()
    assert not entity.available
    assert entity.native_value is None
    assert (entity.unique_id, entity.name, entity.device_info) == identity
    await manager._fetch_data()
    await entity.async_update()
    assert entity.available
    assert entity.native_value == value


@pytest.mark.asyncio
async def test_expired_command_ack_cannot_restore_sensor_availability(
    hass, entry, manager, client, clock
):
    data = await manager.get_status()
    targets = get_heating_setpoint_sensors(hass, entry, manager, data)
    successful = manager.last_successful_read
    clock[0] += 21
    client.set_status.return_value = data
    await manager.set_status({"heatings": {"h2": {"on": True}}})
    for entity in targets:
        await entity.async_update()
        assert not entity.available
        assert entity.native_value is None
    assert manager.last_successful_read == successful
    assert client.get_status.call_count == 1


@pytest.mark.asyncio
async def test_missing_backup_field_does_not_use_solar_or_cached_target(
    hass, entry, manager, client
):
    data = await manager.get_status()
    entity = get_heating_setpoint_sensors(hass, entry, manager, data)[0]
    broken = deepcopy(data)
    del broken["heatings"]["h2"]["sp"]
    client.get_status.return_value = broken
    await manager._fetch_data()
    await entity.async_update()
    assert not entity.available
    assert entity.native_value is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("heating_type", "factory", "suffix"),
    [
        (3, get_heating_temperature_sensors, "_t1_temperature"),
        (5, get_heating_setpoint_sensors, "_sp_setpoint"),
        (4, get_heating_setpoint_sensors, "_sp_setpoint"),
    ],
)
async def test_legacy_mode_and_channel_ids(
    hass, entry, manager, client, heating_type, factory, suffix
):
    client.get_status.return_value = {
        "id": 21392,
        "heating": {"mode": heating_type, "t1": 245, "t2": 251, "t3": 252, "sp": 390},
    }
    data = await manager.get_status()
    entity = factory(hass, entry, manager, data)[0]
    await entity.async_update()
    assert entity.unique_id == f"tholz_test-entry_heating_heating{suffix}"
    assert entity.available


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "raw",
    [None, True, False, "390", float("nan"), float("inf"), -float("inf"), 10**1000],
)
async def test_changed_backup_setpoint_number_recovers_after_invalid_read(
    hass, entry, manager, client, raw
):
    data = await manager.get_status()
    entity = get_heating_setpoint_sensors(hass, entry, manager, data)[0]
    changed = deepcopy(data)
    changed["heatings"]["h2"]["sp"] = raw
    client.get_status.return_value = changed
    await manager._fetch_data()
    await entity.async_update()
    assert not entity.available
    assert entity.native_value is None
    client.get_status.return_value = data
    await manager._fetch_data()
    await entity.async_update()
    assert entity.available
    assert entity.native_value == 39


@pytest.mark.asyncio
async def test_backup_target_initially_missing_then_becomes_valid(
    hass, entry, manager, client, device_data
):
    del device_data["heatings"]["h2"]["sp"]
    data = await manager.get_status()
    entity = get_heating_setpoint_sensors(hass, entry, manager, data)[0]
    await entity.async_update()
    identity = (entity.unique_id, entity.name, entity.device_info)
    assert not entity.available
    assert entity.native_value is None
    changed = deepcopy(data)
    changed["heatings"]["h2"]["sp"] = 0
    client.get_status.return_value = changed
    await manager._fetch_data()
    await entity.async_update()
    assert entity.available
    assert entity.native_value == 0
    assert (entity.unique_id, entity.name, entity.device_info) == identity
