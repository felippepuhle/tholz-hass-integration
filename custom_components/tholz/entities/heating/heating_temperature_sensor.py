from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature

from ...utils.const import DOMAIN, CONF_NAME_KEY, ENTITIES_SCAN_INTERVAL
from ...utils.device import get_device_info
from ...utils.dict import get_in
from .const import HEATING_TYPE
from .utils import get_heating_type, get_valid_heatings


HEATING_TEMPERATURE_SENSOR_CONFIG = {
    HEATING_TYPE.SOLAR_PISCINA: {
        "t1": {
            "name": "Temperatura Coletor",
        },
        "t2": {
            "name": "Temperatura Piscina",
        },
    },
    HEATING_TYPE.SOLAR_RESIDENCIAL: {
        "t1": {
            "name": "Temperatura Coletor",
        },
        "t2": {
            "name": "Temperatura Boiler",
        },
        "t3": {
            "name": "Temperatura Consumo",
        },
    },
    HEATING_TYPE.RECIRCULACAO_BARRILETE: {
        "t4": {
            "name": "Temperatura Recirculação",
        },
    },
    HEATING_TYPE.TERMOSTATO: {
        "t1": {
            "name": "Temperatura Boiler",
        },
    },
}


def get_heating_temperature_sensor_config(state):
    heating_type = get_heating_type(state)
    return HEATING_TEMPERATURE_SENSOR_CONFIG.get(heating_type)


def get_heating_temperature_sensors(hass, entry, manager, data):
    device_info = get_device_info(entry, data)
    heating_temperature_sensors = []
    for heating_key, state in get_valid_heatings(data):
        config = get_heating_temperature_sensor_config(state)
        if config is None:
            continue
        for sensor_key in config:
            if state.get(sensor_key) is None:
                continue
            heating_temperature_sensors.append(
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
    return heating_temperature_sensors


class HeatingTemperatureSensor(SensorEntity):
    def __init__(
        self, hass, entry, manager, device_info, heating_key, sensor_key, state
    ):
        self._hass = hass
        self._entry = entry
        self._manager = manager
        self._device_info = device_info
        self._id = id
        self._heating_key = heating_key
        self._sensor_key = sensor_key

        self._state = state

        self._attr_should_poll = True
        self._attr_scan_interval = ENTITIES_SCAN_INTERVAL

    async def async_update(self):
        data = await self._manager.get_status()
        if data:
            self._state = get_in(data, self._heating_key)

    @property
    def state(self):
        raw = self._state.get(self._sensor_key)
        return raw / 10 if raw is not None else None

    @property
    def unit_of_measurement(self):
        return UnitOfTemperature.CELSIUS

    @property
    def name(self):
        config = get_heating_temperature_sensor_config(self._state)[self._sensor_key]
        return f"{self._entry.data.get(CONF_NAME_KEY)} {config['name']}"

    @property
    def icon(self):
        return "mdi:thermometer"

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._entry.entry_id}_heating_{self._heating_key[-1]}_{self._sensor_key}_temperature"

    @property
    def device_info(self):
        return self._device_info
