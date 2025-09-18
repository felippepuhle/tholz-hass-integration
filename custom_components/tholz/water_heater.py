from .entities.heating.heating_water_heater import (
    HEATING_WATER_HEATER_CONFIG,
    HeatingWaterHeater,
)
from .utils.const import DOMAIN
from .utils.device import get_device_info


async def async_setup_entry(hass, entry, async_add_entities):
    manager = hass.data[DOMAIN][entry.entry_id]["manager"]
    data = await manager.get_status()
    if not data:
        return

    device_info = get_device_info(entry, data["response"])

    entities = []
    if "heatings" in data["response"]:
        for heating_key, state in data["response"]["heatings"].items():
            heating_type = state.get("type")
            if heating_type not in HEATING_WATER_HEATER_CONFIG:
                continue

            entities.append(
                HeatingWaterHeater(
                    hass,
                    entry,
                    manager,
                    device_info,
                    heating_key,
                    state,
                )
            )

    async_add_entities(entities, update_before_add=True)
