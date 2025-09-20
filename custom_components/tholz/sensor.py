from .entities.header.header_sensor import get_header_sensors
from .entities.heating.heating_temperature_sensor import get_heating_temperature_sensors
from .utils.const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    manager = hass.data[DOMAIN][entry.entry_id]["manager"]
    data = await manager.get_status()
    if not data:
        return

    entities = [
        *get_header_sensors(hass, entry, manager, data),
        *get_heating_temperature_sensors(hass, entry, manager, data),
    ]

    async_add_entities(entities, update_before_add=True)
