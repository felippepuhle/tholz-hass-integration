"""Offline fixtures using the real Home Assistant framework."""

from inspect import signature
from unittest.mock import Mock

import pytest
import pytest_asyncio
from homeassistant import loader
from homeassistant.config_entries import ConfigEntry, ConfigEntries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry, entity_registry

from custom_components.tholz.socket.client import TholzSocketClient
from custom_components.tholz.socket.client_manager import TholzSocketClientManager


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Fail any accidental device connection."""
    blocked = Mock(side_effect=AssertionError)
    monkeypatch.setattr("socket.create_connection", blocked)
    yield
    blocked.assert_not_called()


@pytest.fixture
def device_data():
    return {
        "id": 21505,
        "heatings": {
            "h1": {"type": 3, "t1": 245, "t2": 251, "t3": 252, "sp": 420},
            "h2": {"type": 5, "t1": 251, "sp": 390, "on": False, "opMode": 0},
            "h3": {"type": 4, "t1": 251, "sp": 410, "on": False, "opMode": 0},
        },
    }


@pytest.fixture
def client(device_data):
    client = Mock(spec=TholzSocketClient)
    client.get_status.return_value = device_data
    return client


@pytest.fixture
def manager(client):
    return TholzSocketClientManager(client, polling_interval=5)


@pytest.fixture
def clock(monkeypatch):
    now = [100.0]
    monkeypatch.setattr(
        "custom_components.tholz.socket.client_manager.monotonic", lambda: now[0]
    )
    return now


@pytest.fixture
def entry():
    # Newer HA versions require subentries_data; keep the pinned base compatible.
    kwargs = (
        {"subentries_data": []}
        if "subentries_data" in signature(ConfigEntry).parameters
        else {}
    )
    return ConfigEntry(
        domain="tholz",
        entry_id="test-entry",
        data={"name": "Controlador"},
        title="Controlador",
        version=1,
        minor_version=1,
        source="user",
        options={},
        unique_id=None,
        discovery_keys={},
        **kwargs,
    )


@pytest_asyncio.fixture
async def hass(tmp_path):
    hass = HomeAssistant(str(tmp_path))
    yield hass
    await hass.async_stop(force=True)


@pytest_asyncio.fixture
async def lifecycle_hass(hass, monkeypatch):
    """Initialize real config-entry lifecycle without sockets or pip installs."""
    blocked = Mock(side_effect=AssertionError("Network forbidden in lifecycle test"))
    monkeypatch.setattr("socket.socket.connect", blocked)
    monkeypatch.setattr("socket.socket.connect_ex", blocked)
    loader.async_setup(hass)
    hass.config.skip_pip = True
    hass.config_entries = ConfigEntries(hass, {})
    await hass.config_entries.async_initialize()
    if setup_registry := getattr(device_registry, "async_setup", None):
        setup_registry(hass)
    await device_registry.async_load(hass)
    await entity_registry.async_load(hass)
    yield hass
    blocked.assert_not_called()
