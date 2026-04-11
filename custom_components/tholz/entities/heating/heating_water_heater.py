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
from ...utils.device import get_device_info
from ...utils.dict import get_in, set_in
from .const import HEATING_TYPE, HEATING_OP_MODE
from .utils import get_heating_type, get_valid_heatings


HEATING_WATER_HEATER_CONFIG = {
    HEATING_TYPE.SOLAR_PISCINA: {
        "sensor_key": "t2",
        "name": "Piscina",
        "icon": "mdi:pool-thermometer",
        "tholz_to_ha_opmode": {
            HEATING_OP_MODE.DESLIGADO: STATE_OFF,
            HEATING_OP_MODE.LIGADO: STATE_PERFORMANCE,
            HEATING_OP_MODE.AUTOMATICO: STATE_HEAT_PUMP,
        },
    },
    HEATING_TYPE.TROCADOR_CALOR_PISCINA: {
        "sensor_key": "t2",
        "name": "Piscina",
        "icon": "mdi:pool-thermometer",
        "tholz_to_ha_opmode": {
            HEATING_OP_MODE.DESLIGADO: STATE_OFF,
            HEATING_OP_MODE.LIGADO: STATE_PERFORMANCE,
            HEATING_OP_MODE.AUTOMATICO: STATE_HEAT_PUMP,
        },
    },
    HEATING_TYPE.ELETRICO_PISCINA: {
        "sensor_key": "t2",
        "name": "Piscina",
        "icon": "mdi:pool-thermometer",
        "tholz_to_ha_opmode": {
            HEATING_OP_MODE.DESLIGADO: STATE_OFF,
            HEATING_OP_MODE.LIGADO: STATE_PERFORMANCE,
            HEATING_OP_MODE.AUTOMATICO: STATE_HEAT_PUMP,
        },
    },
    HEATING_TYPE.SOLAR_RESIDENCIAL: {
        "sensor_key": "t3",
        "name": "Boiler",
        "icon": "mdi:water-boiler",
        "tholz_to_ha_opmode": {
            HEATING_OP_MODE.DESLIGADO: STATE_OFF,
            HEATING_OP_MODE.LIGADO: STATE_PERFORMANCE,
            HEATING_OP_MODE.AUTOMATICO: STATE_HEAT_PUMP,
            HEATING_OP_MODE.ECONOMICO: STATE_ECO,
        },
    },
    HEATING_TYPE.TROCADOR_CALOR_FAIRLAND: {
        "sensor_key": "t3",
        "name": "Piscina",
        "icon": "mdi:pool-thermometer",
        "tholz_to_ha_opmode": {
            HEATING_OP_MODE.DESLIGADO: STATE_OFF,
            HEATING_OP_MODE.AQUECER: STATE_HEAT_PUMP,
        },
    },
    HEATING_TYPE.TERMOSTATO: {
        "sensor_key": "t1",
        "name": "Boiler",
        "icon": "mdi:water-boiler",
        "tholz_to_ha_opmode": {
            HEATING_OP_MODE.DESLIGADO: STATE_OFF,
            HEATING_OP_MODE.LIGADO: STATE_PERFORMANCE,
            HEATING_OP_MODE.AUTOMATICO: STATE_HEAT_PUMP,
        },
    },
}


def get_heating_water_heater_config(state):
    heating_type = get_heating_type(state)
    return HEATING_WATER_HEATER_CONFIG.get(heating_type)


def get_opmode_maps(state):
    config = get_heating_water_heater_config(state)
    if not config:
        return {}, {}

    tholz_to_ha_opmode = config.get("tholz_to_ha_opmode", {})

    ha_to_tholz_opmode = {}
    for tholz, ha in tholz_to_ha_opmode.items():
        if ha not in ha_to_tholz_opmode:
            ha_to_tholz_opmode[ha] = tholz

    return tholz_to_ha_opmode, ha_to_tholz_opmode


def get_heating_water_heaters(hass, entry, manager, data):
    device_info = get_device_info(entry, data)
    heating_water_heaters = []

    for heating_key, state in get_valid_heatings(data):
        if get_heating_water_heater_config(state) is None:
            continue

        heating_water_heaters.append(
            HeatingWaterHeater(
                hass,
                entry,
                manager,
                device_info,
                heating_key,
                state,
            )
        )

    return heating_water_heaters


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
            self._state = get_in(data, self._heating_key)

    async def async_set_temperature(self, **kwargs):
        self._state["sp"] = int(kwargs.get("temperature") * 10)
        await self._manager.set_status(set_in({}, self._heating_key, self._state))

    async def async_set_operation_mode(self, operation_mode):
        _, ha_to_tholz_opmode = get_opmode_maps(self._state)

        if operation_mode not in ha_to_tholz_opmode:
            return

        self._state["opMode"] = ha_to_tholz_opmode[operation_mode]
        await self._manager.set_status(set_in({}, self._heating_key, self._state))

    @property
    def temperature_unit(self):
        return UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self):
        config = get_heating_water_heater_config(self._state)
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
        tholz_to_ha_opmode, _ = get_opmode_maps(self._state)
        return tholz_to_ha_opmode.get(self._state.get("opMode"), STATE_OFF)

    @property
    def operation_list(self):
        tholz_to_ha_opmode, _ = get_opmode_maps(self._state)
        return list(dict.fromkeys(tholz_to_ha_opmode.values()))

    @property
    def supported_features(self):
        return (
            WaterHeaterEntityFeature.TARGET_TEMPERATURE
            | WaterHeaterEntityFeature.OPERATION_MODE
        )

    @property
    def name(self):
        config = get_heating_water_heater_config(self._state)
        return f"{self._entry.data.get(CONF_NAME_KEY)} {config['name']}"

    @property
    def icon(self):
        config = get_heating_water_heater_config(self._state)
        return config["icon"]

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._entry.entry_id}_heating_{self._heating_key[-1]}_water_heater"

    @property
    def device_info(self):
        return self._device_info
