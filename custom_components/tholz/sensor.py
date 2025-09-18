from .entities.header.header_sensor import (
    HEADER_SENSOR_CONFIG,
    HeaderSensor,
)
from .entities.heating.heating_temperature_sensor import (
    HEATING_TEMPERATURE_SENSOR_CONFIG,
    HeatingTemperatureSensor,
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
    for sensor_key in HEADER_SENSOR_CONFIG:
        entities.append(
            HeaderSensor(
                hass,
                entry,
                manager,
                device_info,
                sensor_key,
                data["response"],
            )
        )
    if "heatings" in data["response"]:
        for heating_key, state in data["response"]["heatings"].items():
            heating_type = state.get("type")
            if heating_type not in HEATING_TEMPERATURE_SENSOR_CONFIG:
                continue

            for sensor_key in HEATING_TEMPERATURE_SENSOR_CONFIG[heating_type]:
                entities.append(
                    HeatingTemperatureSensor(
                        hass,
                        entry,
                        manager,
                        device_info,
                        heating_key,
                        sensor_key,
                        state,
                    )
                )

    async_add_entities(entities, update_before_add=True)
