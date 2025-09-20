from .entities.heating.heating_switch import get_heating_switches
from .entities.output.output_switch import get_output_switches
from .utils.const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    manager = hass.data[DOMAIN][entry.entry_id]["manager"]
    data = await manager.get_status()
    if not data:
        return

    entities = [
        *get_heating_switches(hass, entry, manager, data),
        *get_output_switches(hass, entry, manager, data),
    ]

    async_add_entities(entities, update_before_add=True)
