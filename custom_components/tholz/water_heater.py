from .entities.heating.heating_water_heater import (
    HEATING_WATER_HEATER_CONFIG,
    HeatingWaterHeater,
)
from .utils.const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    manager = hass.data[DOMAIN][entry.entry_id]["manager"]
    data = await manager.get_status()
    if not data:
        return

    model = data["response"].get("firmwareSec")

    entities = []
    if "heatings" in data["response"]:
        for heating_key, state in data["response"]["heatings"].items():
            HEATING_TYPE = state.get("type")
            if HEATING_TYPE not in HEATING_WATER_HEATER_CONFIG:
                continue

            entities.append(
                HeatingWaterHeater(
                    hass,
                    entry,
                    manager,
                    model,
                    heating_key,
                    state,
                )
            )

    async_add_entities(entities, update_before_add=True)
