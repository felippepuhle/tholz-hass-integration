from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature

from ...utils.const import DOMAIN, CONF_NAME_KEY, ENTITIES_SCAN_INTERVAL
from .const import HEATING_TYPE


# A documentação não é explícita quanto a esta configuração.
# Foram adicionados apenas os sensores validados em testes práticos até o momento.
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
            self._state = data["heatings"][self._heating_key]

    @property
    def state(self):
        raw = self._state.get(self._sensor_key)
        return raw / 10 if raw is not None else None

    @property
    def unit_of_measurement(self):
        return UnitOfTemperature.CELSIUS

    @property
    def name(self):
        config = HEATING_TEMPERATURE_SENSOR_CONFIG[self._state.get("type")][
            self._sensor_key
        ]
        return f"{self._entry.data.get(CONF_NAME_KEY)} {config['name']}"

    @property
    def icon(self):
        return "mdi:thermometer"

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._entry.entry_id}_heating_{self._heating_key}_{self._sensor_key}_temperature"

    @property
    def device_info(self):
        return self._device_info
