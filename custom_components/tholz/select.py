from .entities.heating.heating_fan_mode_select import get_heating_fan_mode_selects
from .utils.const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    manager = hass.data[DOMAIN][entry.entry_id]["manager"]
    data = await manager.get_status()
    if not data:
        return

    entities = [
        *get_heating_fan_mode_selects(hass, entry, manager, data),
    ]

    async_add_entities(entities, update_before_add=True)
