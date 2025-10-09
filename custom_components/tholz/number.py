from .entities.led.led_effect_speed_number import get_led_effect_speed_numbers
from .utils.const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    manager = hass.data[DOMAIN][entry.entry_id]["manager"]
    data = await manager.get_status()
    if not data:
        return

    entities = [
        *get_led_effect_speed_numbers(hass, entry, manager, data),
    ]

    async_add_entities(entities, update_before_add=True)
