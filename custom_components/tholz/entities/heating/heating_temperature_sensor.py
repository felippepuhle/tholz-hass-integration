from ...utils.const import DOMAIN
from ...utils.device import get_device_info
from .const import HEATING_TYPE
from .heating_read_sensor import HeatingReadSensor
from .utils import (
    get_heating_sensor_type,
    get_heating_sensor_channels,
)


HEATING_TEMPERATURE_SENSOR_CONFIG = {
    HEATING_TYPE.SOLAR_PISCINA: {
        "t1": {
            "name": "Temperatura Coletor",
        },
        "t2": {
            "name": "Temperatura Piscina",
        },
    },
    HEATING_TYPE.TROCADOR_CALOR_PISCINA: {
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
    HEATING_TYPE.TROCADOR_CALOR_FAIRLAND: {
        "t1": {
            "name": "Temperatura Ambiente",
        },
        "t2": {
            "name": "Temperatura Saída",
        },
        "t3": {
            "name": "Temperatura Entrada",
        },
    },
    HEATING_TYPE.TERMOSTATO: {
        "t1": {
            "name": "Temperatura Boiler",
        },
    },
}


def get_heating_temperature_sensor_config(state):
    heating_type = get_heating_sensor_type(state)
    return HEATING_TEMPERATURE_SENSOR_CONFIG.get(heating_type)


def get_heating_temperature_sensors(hass, entry, manager, data):
    device_info = get_device_info(entry, data)
    heating_temperature_sensors = []
    for heating_key, state in get_heating_sensor_channels(data):
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


class HeatingTemperatureSensor(HeatingReadSensor):
    def __init__(
        self, hass, entry, manager, device_info, heating_key, sensor_key, state
    ):
        config = get_heating_temperature_sensor_config(state)[sensor_key]
        super().__init__(
            hass,
            entry,
            manager,
            device_info,
            heating_key,
            sensor_key,
            state,
            config["name"],
        )

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._entry.entry_id}_heating_{self._heating_key[-1]}_{self._sensor_key}_temperature"
