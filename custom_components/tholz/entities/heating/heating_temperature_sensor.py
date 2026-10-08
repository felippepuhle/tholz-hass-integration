from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import UnitOfTemperature

from ...utils.const import DOMAIN, CONF_NAME_KEY, ENTITIES_SCAN_INTERVAL
from ...utils.device import get_device_info
from ...utils.dict import get_in
from .const import HEATING_TYPE
from .utils import (
    get_heating_sensor_type,
    get_heating_sensor_channels,
    get_native_temperature,
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


class HeatingReadSensor(SensorEntity):
    """A read-only native heating value backed by a fresh device snapshot."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self, hass, entry, manager, device_info, heating_key, sensor_key, state, name
    ):
        self._hass = hass
        self._entry = entry
        self._manager = manager
        self._device_info = device_info
        self._id = id
        self._heating_key = heating_key
        self._sensor_key = sensor_key

        self._state = state
        self._name = f"{entry.data.get(CONF_NAME_KEY)} {name}"
        self._heating_type = get_heating_sensor_type(state)

        self._attr_should_poll = True
        self._attr_scan_interval = ENTITIES_SCAN_INTERVAL

    async def async_update(self):
        data = await self._manager.get_sensor_status()
        state = get_in(data, self._heating_key)
        self._state = state if isinstance(state, dict) else {}

    @property
    def available(self):
        return (
            self._manager.is_fresh
            and get_heating_sensor_type(self._state) == self._heating_type
            and get_native_temperature(self._state.get(self._sensor_key)) is not None
        )

    @property
    def native_value(self):
        if not self.available:
            return None
        return get_native_temperature(self._state.get(self._sensor_key))

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return "mdi:thermometer"

    @property
    def device_info(self):
        return self._device_info


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
