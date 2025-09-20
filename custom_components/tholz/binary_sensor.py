from .entities.header.header_binary_sensor import (
    HEADER_BINARY_SENSOR_CONFIG,
    HeaderBinarySensor,
)
from .entities.heating.heating_binary_sensor import (
    get_heating_binary_sensor_config,
    HeatingBinarySensor,
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
    for sensor_key in HEADER_BINARY_SENSOR_CONFIG:
        if data.get(sensor_key) is None:
            continue

        entities.append(
            HeaderBinarySensor(
                hass,
                entry,
                manager,
                device_info,
                sensor_key,
                data,
            )
        )

    if "heatings" in data:
        for heating_key, state in data["heatings"].items():
            config = get_heating_binary_sensor_config(state)
            if config is None or not heating_has_valid_temperatures(state):
                continue

            for sensor_key in config:
                if state.get(sensor_key) is None:
                    continue

                entities.append(
                    HeatingBinarySensor(
                        hass,
                        entry,
                        manager,
                        device_info,
                        ["heatings", heating_key],
                        sensor_key,
                        state,
                    )
                )

    async_add_entities(entities, update_before_add=True)
