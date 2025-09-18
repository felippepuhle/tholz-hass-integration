from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
    STATE_OFF,
    STATE_PERFORMANCE,
    STATE_HEAT_PUMP,
    STATE_ECO,
)
from homeassistant.const import UnitOfTemperature

from ...utils.const import DOMAIN, CONF_NAME_KEY, ENTITIES_SCAN_INTERVAL
from .const import HEATING_TYPE, HEATING_OP_MODE

THOLZ_OPMODE_TO_HA_OPMODE = {
    HEATING_OP_MODE.DESLIGADO: STATE_OFF,
    HEATING_OP_MODE.LIGADO: STATE_PERFORMANCE,
    HEATING_OP_MODE.AUTOMATICO: STATE_HEAT_PUMP,
    HEATING_OP_MODE.ECONOMICO: STATE_ECO,
}

HA_OPMODE_TO_THOLZ_OPMODE = {
    ha: tholz for tholz, ha in THOLZ_OPMODE_TO_HA_OPMODE.items()
}

HEATING_WATER_HEATER_CONFIG = {
    HEATING_TYPE.SOLAR_PISCINA: {
        "sensor_key": "t2",
        "operation_list": [STATE_OFF, STATE_PERFORMANCE, STATE_HEAT_PUMP],
        "name": "Piscina",
        "icon": "mdi:pool-thermometer",
    },
    HEATING_TYPE.TROCADOR_CALOR_PISCINA: {
        "sensor_key": "t2",
        "operation_list": [STATE_OFF, STATE_PERFORMANCE, STATE_HEAT_PUMP],
        "name": "Piscina",
        "icon": "mdi:pool-thermometer",
    },
    HEATING_TYPE.ELETRICO_PISCINA: {
        "sensor_key": "t2",
        "operation_list": [STATE_OFF, STATE_PERFORMANCE, STATE_HEAT_PUMP],
        "name": "Piscina",
        "icon": "mdi:pool-thermometer",
    },
    HEATING_TYPE.SOLAR_RESIDENCIAL: {
        "sensor_key": "t3",
        "operation_list": [STATE_OFF, STATE_PERFORMANCE, STATE_HEAT_PUMP, STATE_ECO],
        "name": "Boiler",
        "icon": "mdi:water-boiler",
    },
    HEATING_TYPE.TERMOSTATO: {
        "sensor_key": "t1",
        "operation_list": [STATE_OFF, STATE_PERFORMANCE, STATE_HEAT_PUMP],
        "name": "Boiler",
        "icon": "mdi:water-boiler",
    },
}


class HeatingWaterHeater(WaterHeaterEntity):
    def __init__(self, hass, entry, manager, device_info, heating_key, state):
        self._hass = hass
        self._entry = entry
        self._manager = manager
        self._device_info = device_info
        self._heating_key = heating_key

        self._state = state

        self._attr_should_poll = True
        self._attr_scan_interval = ENTITIES_SCAN_INTERVAL

    async def async_update(self):
        data = await self._manager.get_status()
        if data:
            self._state = data["heatings"][self._heating_key]

    async def async_set_temperature(self, **kwargs):
        self._state["sp"] = int(kwargs.get("temperature") * 10)
        await self._manager.set_status({"heatings": {self._heating_key: self._state}})

    async def async_set_operation_mode(self, operation_mode):
        self._state["opMode"] = HA_OPMODE_TO_THOLZ_OPMODE[operation_mode]
        await self._manager.set_status({"heatings": {self._heating_key: self._state}})

    @property
    def temperature_unit(self):
        return UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self):
        config = HEATING_WATER_HEATER_CONFIG[self._state.get("type")]
        sensor_key = config["sensor_key"]
        if self._state.get(sensor_key) is not None:
            return self._state.get(sensor_key) / 10
        return None

    @property
    def target_temperature(self):
        return self._state.get("sp", 0) / 10

    @property
    def target_temperature_step(self):
        step = self._state.get("stepSp")
        return step / 10 if step is not None else 1.0

    @property
    def min_temp(self):
        min_sp = self._state.get("minSp")
        return min_sp / 10 if min_sp is not None else 40.0

    @property
    def max_temp(self):
        max_sp = self._state.get("maxSp")
        return max_sp / 10 if max_sp is not None else 70.0

    @property
    def current_operation(self):
        return THOLZ_OPMODE_TO_HA_OPMODE[self._state.get("opMode", 0)]

    @property
    def operation_list(self):
        config = HEATING_WATER_HEATER_CONFIG[self._state.get("type")]
        return config["operation_list"]

    @property
    def supported_features(self):
        return (
            WaterHeaterEntityFeature.TARGET_TEMPERATURE
            | WaterHeaterEntityFeature.OPERATION_MODE
        )

    @property
    def name(self):
        config = HEATING_WATER_HEATER_CONFIG[self._state.get("type")]
        return f"{self._entry.data.get(CONF_NAME_KEY)} {config['name']}"

    @property
    def icon(self):
        config = HEATING_WATER_HEATER_CONFIG[self._state.get("type")]
        return config["icon"]

    @property
    def unique_id(self):
        return (
            f"{DOMAIN}_{self._entry.entry_id}_heating_{self._heating_key}_water_heater"
        )

    @property
    def device_info(self):
        return self._device_info
