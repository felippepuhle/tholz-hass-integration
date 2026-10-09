"""Read validity and cache regressions; device I/O is mocked."""

import asyncio

from copy import deepcopy

import pytest
from homeassistant.exceptions import HomeAssistantError


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "ack",
    [
        True,
        {"ok": True},
        {"heatings": {"h2": {"sp": 900}}},
        {"id": 21505, "heatings": {"h2": {"type": 5, "t1": 251, "sp": 900}}},
        False,
    ],
)
async def test_command_ack_does_not_replace_read_snapshot(manager, client, ack):
    original = deepcopy(await manager.get_status())
    successful = manager.last_successful_read
    client.set_status.return_value = ack
    assert await manager.set_status({"heatings": {"h2": {"on": True}}}) == ack
    assert await manager.get_sensor_status() == original
    assert manager.last_successful_read == successful
    client.set_status.assert_called_once_with({"heatings": {"h2": {"on": True}}})


@pytest.mark.asyncio
async def test_failed_mutating_write_cannot_poison_shared_snapshot(
    manager, client, device_data
):
    original = deepcopy(await manager.get_status())
    outgoing = await manager.get_status()
    outgoing["heatings"]["h1"]["sp"] = 999
    client.set_status.return_value = False
    await manager.set_status(outgoing)
    assert await manager.get_sensor_status() == original
    device_data["heatings"]["h1"]["t1"] = 999
    assert await manager.get_sensor_status() == original


@pytest.mark.asyncio
@pytest.mark.parametrize("interval", [1, 5, 30])
async def test_stopped_poller_expires_without_getter_read_storm(
    manager, client, clock, interval
):
    manager._polling_interval = interval
    first = await manager.get_status()
    successful = manager.last_successful_read
    clock[0] += 3 * interval + 5
    assert manager.is_fresh
    clock[0] += 0.01
    assert not manager.is_fresh
    async with manager._lock:
        for _ in range(5):
            assert (
                await asyncio.wait_for(manager.get_sensor_status(), timeout=0.1) is None
            )
    assert client.get_status.call_count == 1
    await manager._fetch_data()
    assert manager.is_fresh
    assert await manager.get_sensor_status() == first
    assert manager.last_successful_read > successful


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "partial",
    [
        {"ok": True},
        {"id": None},
        {"id": True},
        {"heatings": {}},
        {"heatings": {"h2": {"sp": 900}}},
        {"id": 21505, "heatings": {"h2": {"sp": 900}}},
        {"id": 21505, "outputs": []},
        {"id": 21505, "monitors": True},
    ],
)
async def test_partial_or_malformed_read_does_not_count_as_success(
    manager, client, partial
):
    await manager.get_status()
    successful = manager.last_successful_read
    client.get_status.return_value = partial
    await manager._fetch_data()
    assert not manager.is_fresh
    assert await manager.get_sensor_status() is None
    assert manager.last_successful_read == successful


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure",
    [
        None,
        {},
        [],
        "invalid",
        {"heatings": []},
        {"heatings": {"h1": None}},
        {"unexpected": True},
        OSError("read failed"),
    ],
)
async def test_failed_read_invalidates_previous_success(manager, client, failure):
    assert await manager.get_status() is not None
    successful = manager.last_successful_read
    client.get_status.side_effect = [failure]
    await manager._fetch_data()
    assert await manager.get_sensor_status() is None
    assert manager.last_successful_read == successful
    assert not manager.is_fresh


@pytest.mark.asyncio
async def test_command_exception_keeps_snapshot_and_success_time(manager, client):
    data = await manager.get_status()
    successful = manager.last_successful_read
    client.set_status.side_effect = OSError
    with pytest.raises(OSError, match=r"^$"):
        await manager.set_status({"heatings": {"h2": {"on": True}}})
    assert await manager.get_status() == data
    assert manager.last_successful_read == successful


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data",
    [
        {"id": 1551, "leds": {"l1": {"on": False}}},
        {"id": 51528, "monitors": {"m1": {"type": 1}}},
        {"id": 1551, "outputs": {"o1": None}},
    ],
)
async def test_non_heating_device_snapshots_remain_supported(manager, client, data):
    client.get_status.return_value = data
    assert await manager.get_status() == data
    assert manager.is_fresh


@pytest.mark.asyncio
@pytest.mark.parametrize("lost_read", ["initial", "expired"])
@pytest.mark.parametrize(
    "failure", [None, {"ok": True}, {"heatings": []}, OSError("offline")]
)
async def test_get_status_raises_offline_error_then_recovers(
    manager, client, device_data, clock, lost_read, failure
):
    successful = None
    if lost_read == "expired":
        await manager.get_status()
        successful = manager.last_successful_read
        clock[0] += 21
    calls = client.get_status.call_count
    client.get_status.side_effect = [failure, device_data]
    # Read-only sensors must stay nonblocking, including during command I/O.
    async with manager._lock:
        assert await asyncio.wait_for(manager.get_sensor_status(), timeout=0.1) is None
    assert client.get_status.call_count == calls
    with pytest.raises(HomeAssistantError, match=r"^Controller unavailable$"):
        await manager.get_status()
    assert not manager._lock.locked()
    assert manager.last_successful_read == successful
    assert not manager.is_fresh
    assert await manager.get_sensor_status() is None
    assert client.get_status.call_count == calls + 1
    client.set_status.assert_not_called()
    recovered = await asyncio.wait_for(manager.get_status(), timeout=1)
    assert recovered == device_data
    assert await manager.get_status() is recovered
    assert manager.is_fresh
    assert await manager.get_sensor_status() == device_data
    assert client.get_status.call_count == calls + 2
    client.set_status.assert_not_called()
