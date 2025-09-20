from homeassistant.components.switch import SwitchEntity

from ...utils.const import DOMAIN, CONF_NAME_KEY, ENTITIES_SCAN_INTERVAL
from ...utils.device import get_device_info
from ...utils.dict import get_in, set_in
from .const import (
    HEATING_TYPE,
    HEATING_OP_MODE,
)
from .utils import get_heating_type, get_valid_heatings

HEATING_SWITCH_CONFIG = {
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


def get_heating_switch_config(state):
    heating_type = get_heating_type(state)
    return HEATING_SWITCH_CONFIG.get(heating_type)


def get_heating_switches(hass, entry, manager, data):
    device_info = get_device_info(entry, data)
    heating_switches = []
    for heating_key, state in get_valid_heatings(data):
        if get_heating_switch_config(state) is None:
            continue
        heating_switches.append(
            HeatingSwitch(
                hass,
                entry,
                manager,
                device_info,
                heating_key,
                state,
            )
        )
    return heating_switches


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
            self._state = get_in(data, self._heating_key)

    async def async_turn_on(self):
        config = get_heating_switch_config(self._state)

        self._state["on"] = True
        if "opMode" in config:
            self._state["opMode"] = config["opMode"]["on"]

        await self._manager.set_status(set_in({}, self._heating_key, self._state))

    async def async_turn_off(self):
        config = get_heating_switch_config(self._state)

        self._state["on"] = False
        if "opMode" in config:
            self._state["opMode"] = config["opMode"]["off"]

        await self._manager.set_status(set_in({}, self._heating_key, self._state))

    @property
    def is_on(self):
        return self._state.get("on", False)

    @property
    def name(self):
        config = get_heating_switch_config(self._state)
        return f"{self._entry.data.get(CONF_NAME_KEY)} {config['name']}"

    @property
    def icon(self):
        config = get_heating_switch_config(self._state)
        return config["icon"]

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._entry.entry_id}_heating_{self._heating_key[-1]}_switch"

    @property
    def device_info(self):
        return self._device_info
