from .entities.header.header_sensor import (
    HEADER_SENSOR_CONFIG,
    HeaderSensor,
)
from .entities.heating.heating_temperature_sensor import (
    HEATING_TEMPERATURE_SENSOR_CONFIG,
    HeatingTemperatureSensor,
)
from .utils.const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    manager = hass.data[DOMAIN][entry.entry_id]["manager"]
    data = await manager.get_status()
    if not data:
        return

    model = data["response"].get("firmwareSec")

    entities = []
    for sensor_key in HEADER_SENSOR_CONFIG:
        entities.append(
            HeaderSensor(
                hass,
                entry,
                manager,
                model,
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
                        model,
                        heating_key,
                        sensor_key,
                        state,
                    )
                )

    async_add_entities(entities, update_before_add=True)
