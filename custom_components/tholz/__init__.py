from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

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
    manager.start(hass)

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "manager": manager,
    }

    await hass.config_entries.async_forward_entry_setups(
        entry, ["binary_sensor", "light", "number", "sensor", "switch", "water_heater"]
    )

    return True
