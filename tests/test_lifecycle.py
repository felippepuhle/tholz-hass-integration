"""Config-entry lifecycle regression tests with mocked device I/O."""

import asyncio
from unittest.mock import AsyncMock


import pytest

from homeassistant.config_entries import ConfigEntries, ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry, entity_component

from custom_components.tholz import async_setup_entry, async_unload_entry, PLATFORMS


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response", [None, {}, [], {"heatings": []}, OSError("offline")]
)
async def test_initial_setup_retries_invalid_device_reads(
    hass, entry, client, monkeypatch, response
):
    client.get_status.side_effect = [response]
    monkeypatch.setattr(
        "custom_components.tholz.TholzSocketClient", lambda *_args: client
    )
    with pytest.raises(ConfigEntryNotReady):
        await async_setup_entry(hass, entry)
    assert "tholz" not in hass.data
    client.set_status.assert_not_called()


@pytest.mark.asyncio
async def test_setup_and_unload_stop_the_only_poller(hass, entry, client, monkeypatch):
    # Keep real framework objects; replace only platform orchestration so this
    # bounded test does not load unrelated HA components or open any sockets.
    hass.config_entries = ConfigEntries(hass, {})
    forward = AsyncMock()
    monkeypatch.setattr(hass.config_entries, "async_forward_entry_setups", forward)
    monkeypatch.setattr(
        "custom_components.tholz.TholzSocketClient", lambda *_args: client
    )
    assert await async_setup_entry(hass, entry)
    forward.assert_awaited_once_with(entry, PLATFORMS)
    manager = hass.data["tholz"][entry.entry_id]["manager"]
    task = manager._task
    manager.start(hass)
    assert manager._task is task
    # Real unload implementation with an empty platform list: sensor wiring is
    # exercised independently, and here only cancellation/lifecycle is in scope.
    monkeypatch.setattr("custom_components.tholz.PLATFORMS", [])
    assert await async_unload_entry(hass, entry)
    assert task.cancelled()
    assert manager._task is None
    assert entry.entry_id not in hass.data["tholz"]
    await manager.stop()
    client.set_status.assert_not_called()


@pytest.mark.asyncio
async def test_failed_platform_unload_keeps_poller(hass, entry, manager, monkeypatch):
    await manager.get_status()
    manager.start(hass)
    hass.data["tholz"] = {entry.entry_id: {"manager": manager}}
    hass.config_entries = ConfigEntries(hass, {})
    monkeypatch.setattr(
        hass.config_entries, "async_unload_platforms", AsyncMock(return_value=False)
    )
    task = manager._task
    try:
        assert not await async_unload_entry(hass, entry)
        assert manager._task is task
        assert entry.entry_id in hass.data["tholz"]
    finally:
        await manager.stop()


@pytest.mark.asyncio
async def test_updater_continues_after_read_exception(
    hass, manager, client, device_data
):
    recovered = asyncio.Event()
    count = 0

    def read():
        nonlocal count
        count += 1
        if count == 1:
            raise OSError
        hass.loop.call_soon_threadsafe(recovered.set)
        return device_data

    client.get_status.side_effect = read
    manager._polling_interval = 0.01
    manager.start(hass)
    task = manager._task
    try:
        await asyncio.wait_for(recovered.wait(), timeout=1)
        # The event marks the mock read; await its snapshot publication too.
        async with manager._lock:
            assert manager.is_fresh
    finally:
        await manager.stop()
    assert task.cancelled()
    assert count >= 2


@pytest.mark.asyncio
async def test_real_entry_forwarding_survives_immediate_poll_failure(
    lifecycle_hass, entry, client, device_data, monkeypatch
):
    """Use real ConfigEntries, all seven platforms, registries and publication."""
    hass = lifecycle_hass
    reads = 0
    poll_failed = asyncio.Event()

    def read():
        nonlocal reads
        reads += 1
        if reads > 1:
            hass.loop.call_soon_threadsafe(poll_failed.set)
        return device_data if reads == 1 else None

    client.get_status.side_effect = read
    monkeypatch.setattr(
        "custom_components.tholz.TholzSocketClient", lambda *_args: client
    )
    manager = None
    try:
        await hass.config_entries.async_add(entry)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.LOADED
        manager = hass.data["tholz"][entry.entry_id]["manager"]
        await asyncio.wait_for(poll_failed.wait(), timeout=1)
        async with manager._lock:
            assert not manager.is_fresh
        registry = entity_registry.async_get(hass)
        entities = entity_registry.async_entries_for_config_entry(
            registry, entry.entry_id
        )
        targets = [
            entity for entity in entities if entity.unique_id.endswith("_setpoint")
        ]
        assert len(targets) == 2
        assert {entity.domain for entity in entities} >= {
            "sensor",
            "switch",
            "water_heater",
        }
        assert reads >= 2
        assert not manager.is_fresh
        client.get_status.side_effect = None
        client.get_status.return_value = device_data
        await manager._fetch_data()
        for target in targets:
            await entity_component.async_update_entity(hass, target.entity_id)
        assert sorted(
            float(hass.states.get(target.entity_id).state) for target in targets
        ) == [39, 41]
        task = manager._task
        assert await hass.config_entries.async_unload(entry.entry_id)
        assert entry.state is ConfigEntryState.NOT_LOADED
        assert task.cancelled()
        assert manager._task is None
        assert entry.entry_id not in hass.data["tholz"]
        client.set_status.assert_not_called()
    finally:
        if manager is None:
            manager = hass.data.get("tholz", {}).get(entry.entry_id, {}).get("manager")
        if manager is not None:
            await manager.stop()


@pytest.mark.asyncio
async def test_real_config_entry_retry_recovers_initial_read_failure(
    lifecycle_hass, entry, client, device_data, monkeypatch
):
    """Compatibility coverage: actual HA retry callback, not mocked forwarding."""
    hass = lifecycle_hass
    client.get_status.return_value = None
    monkeypatch.setattr(
        "custom_components.tholz.TholzSocketClient", lambda *_args: client
    )
    manager = None
    try:
        await hass.config_entries.async_add(entry)
        assert entry.state is ConfigEntryState.SETUP_RETRY
        assert entry.entry_id not in hass.data.get("tholz", {})
        client.get_status.return_value = device_data
        # Deliver the real framework's startup retry event inside the fixture;
        # do not start Home Assistant, servers, or any network integrations.
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done(wait_background_tasks=True)
        assert entry.state is ConfigEntryState.LOADED
        manager = hass.data["tholz"][entry.entry_id]["manager"]
        registry = entity_registry.async_get(hass)
        entities = entity_registry.async_entries_for_config_entry(
            registry, entry.entry_id
        )
        assert (
            len(
                [
                    entity
                    for entity in entities
                    if entity.unique_id.endswith("_setpoint")
                ]
            )
            == 2
        )
        client.set_status.assert_not_called()
        assert await hass.config_entries.async_unload(entry.entry_id)
        assert manager._task is None
    finally:
        if manager is None:
            manager = hass.data.get("tholz", {}).get(entry.entry_id, {}).get("manager")
        if manager is not None:
            await manager.stop()
