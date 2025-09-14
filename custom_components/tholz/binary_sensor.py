from .entities.header.header_binary_sensor import (
    HEADER_BINARY_SENSOR_CONFIG,
    HeaderBinarySensor,
)
from .utils.const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    manager = hass.data[DOMAIN][entry.entry_id]["manager"]
    data = await manager.get_status()
    if not data:
        return

    model = data["response"].get("firmwareSec")

    entities = []
    for sensor_key in HEADER_BINARY_SENSOR_CONFIG:
        entities.append(
            HeaderBinarySensor(
                hass,
                entry,
                manager,
                model,
                sensor_key,
                data["response"],
            )
        )

    async_add_entities(entities, update_before_add=True)
