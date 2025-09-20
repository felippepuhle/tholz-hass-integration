from .entities.heating.heating_water_heater import get_heating_water_heaters
from .utils.const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    manager = hass.data[DOMAIN][entry.entry_id]["manager"]
    data = await manager.get_status()
    if not data:
        return

    entities = [
        *get_heating_water_heaters(hass, entry, manager, data),
    ]

    async_add_entities(entities, update_before_add=True)
