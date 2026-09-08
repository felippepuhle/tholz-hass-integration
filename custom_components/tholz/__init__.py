from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .socket.client import TholzSocketClient
from .socket.client_manager import TholzSocketClientManager
from .utils.const import (
    DOMAIN,
    CONF_HOST_KEY,
    CONF_PORT_KEY,
    CONF_PORT_DEFAULT_VALUE,
    CONF_POLLING_INTERVAL_KEY,
    CONF_POLLING_INTERVAL_DEFAULT_VALUE,
)


PLATFORMS = [
    "binary_sensor",
    "light",
    "number",
    "select",
    "sensor",
    "switch",
    "water_heater",
]


async def async_setup(_hass, _config):
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    host = entry.data.get(CONF_HOST_KEY)
    port = entry.data.get(CONF_PORT_KEY, CONF_PORT_DEFAULT_VALUE)
    polling_interval = entry.data.get(
        CONF_POLLING_INTERVAL_KEY, CONF_POLLING_INTERVAL_DEFAULT_VALUE
    )

    client = TholzSocketClient(host, port)
    manager = TholzSocketClientManager(client, polling_interval)

    # Fail the setup here instead of forwarding the platforms with no data.
    # Entity setup assumes a populated payload, so an unreachable controller
    # would otherwise raise while the config flow is still running.
    if await manager.get_status() is None:
        raise ConfigEntryNotReady(f"no reply from the controller at {host}:{port}")

    manager.start(hass)

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "manager": manager,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unloaded:
        stored = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if stored:
            await stored["manager"].stop()

    return unloaded
