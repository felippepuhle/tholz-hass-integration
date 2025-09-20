from .entities.heating.heating_water_heater import (
    get_heating_water_heater_config,
    HeatingWaterHeater,
)
from .entities.heating.utils import heating_has_valid_temperatures
from .utils.const import DOMAIN
from .utils.device import get_device_info


async def async_setup_entry(hass, entry, async_add_entities):
    manager = hass.data[DOMAIN][entry.entry_id]["manager"]
    data = await manager.get_status()
    if not data:
        return

    device_info = get_device_info(entry, data)

    entities = []
    if "heatings" in data:
        for heating_key, state in data["heatings"].items():
            config = get_heating_water_heater_config(state)
            if config is None or not heating_has_valid_temperatures(state):
                continue

            entities.append(
                HeatingWaterHeater(
                    hass,
                    entry,
                    manager,
                    device_info,
                    ["heatings", heating_key],
                    state,
                )
            )

    async_add_entities(entities, update_before_add=True)
