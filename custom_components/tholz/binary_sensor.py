from .entities.header.header_binary_sensor import (
    HEADER_BINARY_SENSOR_CONFIG,
    HeaderBinarySensor,
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
    for sensor_key in HEADER_BINARY_SENSOR_CONFIG:
        if data["response"].get(sensor_key) is None:
            continue

        entities.append(
            HeaderBinarySensor(
                hass,
                entry,
                manager,
                device_info,
                sensor_key,
                data["response"],
            )
        )

    async_add_entities(entities, update_before_add=True)
