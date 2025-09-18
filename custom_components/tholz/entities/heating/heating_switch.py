from homeassistant.components.switch import SwitchEntity

from ...utils.const import DOMAIN, CONF_NAME_KEY, ENTITIES_SCAN_INTERVAL
from .const import (
    HEATING_TYPE,
    HEATING_OP_MODE,
)

HEATING_SWITCH_CONFIG = {
    HEATING_TYPE.SOLAR_PISCINA: {
        "name": "Solar",
        "icon": "mdi:weather-sunset",
    },
    HEATING_TYPE.TROCADOR_CALOR_PISCINA: {
        "name": "Trocador de Calor",
        "icon": "mdi:heat-pump",
    },
    HEATING_TYPE.ELETRICO_PISCINA: {
        "name": "Elétrico",
        "icon": "mdi:radiator",
    },
    HEATING_TYPE.SOLAR_RESIDENCIAL: {
        "name": "Solar",
        "icon": "mdi:weather-sunset",
    },
    HEATING_TYPE.APOIO_GAS: {
        "name": "Apoio a Gás",
        "icon": "mdi:gas-burner",
        "opMode": {"off": HEATING_OP_MODE.DESLIGADO, "on": HEATING_OP_MODE.LIGADO},
    },
    HEATING_TYPE.APOIO_ELETRICO: {
        "name": "Apoio Elétrico",
        "icon": "mdi:radiator",
        "opMode": {"off": HEATING_OP_MODE.DESLIGADO, "on": HEATING_OP_MODE.LIGADO},
    },
    HEATING_TYPE.RECIRCULACAO_BARRILETE: {
        "name": "Recirculação",
        "icon": "mdi:engine",
        "opMode": {"off": HEATING_OP_MODE.DESLIGADO, "on": HEATING_OP_MODE.LIGADO},
    },
    HEATING_TYPE.AQUECIMENTO: {
        "name": "Aquecimento",
        "icon": "mdi:fire",
        "opMode": {"off": HEATING_OP_MODE.DESLIGADO, "on": HEATING_OP_MODE.AQUECER},
    },
    HEATING_TYPE.REFRIGERACAO: {
        "name": "Refrigeração",
        "icon": "mdi:snowflake",
        "opMode": {"off": HEATING_OP_MODE.DESLIGADO, "on": HEATING_OP_MODE.RESFRIAR},
    },
    HEATING_TYPE.TERMOSTATO: {
        "name": "Termostato",
        "icon": "mdi:thermometer",
    },
}


class HeatingSwitch(SwitchEntity):
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
            self._state = data["response"]["heatings"][self._heating_key]

    async def async_turn_on(self):
        self._state["on"] = True

        config = HEATING_SWITCH_CONFIG[self._state.get("type")]
        if "opMode" in config:
            self._state["opMode"] = config["opMode"]["on"]

        await self._manager.set_status({"heatings": {self._heating_key: self._state}})

    async def async_turn_off(self):
        self._state["on"] = False

        config = HEATING_SWITCH_CONFIG[self._state.get("type")]
        if "opMode" in config:
            self._state["opMode"] = config["opMode"]["off"]

        await self._manager.set_status({"heatings": {self._heating_key: self._state}})

    @property
    def is_on(self):
        return self._state.get("on", False)

    @property
    def name(self):
        config = HEATING_SWITCH_CONFIG[self._state.get("type")]
        return f"{self._entry.data.get(CONF_NAME_KEY)} {config['name']}"

    @property
    def icon(self):
        config = HEATING_SWITCH_CONFIG[self._state.get("type")]
        return config["icon"]

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._entry.entry_id}_heating_{self._heating_key}_switch"

    @property
    def device_info(self):
        return self._device_info
