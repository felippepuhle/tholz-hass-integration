from homeassistant.components.switch import SwitchEntity

from ...utils.const import DOMAIN, CONF_NAME_KEY, ENTITIES_SCAN_INTERVAL
from ...utils.device import get_device_info
from ...utils.dict import get_in, set_in
from .const import MONITOR_OP_MODE
from .utils import get_valid_monitors


def get_monitor_switches(hass, entry, manager, data):
    device_info = get_device_info(entry, data)
    return [
        MonitorSwitch(hass, entry, manager, device_info, monitor_key, state)
        for monitor_key, state in get_valid_monitors(data)
    ]


class MonitorSwitch(SwitchEntity):
    def __init__(self, hass, entry, manager, device_info, monitor_key, state):
        self._hass = hass
        self._entry = entry
        self._manager = manager
        self._device_info = device_info
        self._monitor_key = monitor_key

        self._state = state

        self._attr_should_poll = True
        self._attr_scan_interval = ENTITIES_SCAN_INTERVAL

    async def async_update(self):
        data = await self._manager.get_status()
        if data:
            self._state = get_in(data, self._monitor_key, self._state)

    async def async_turn_on(self):
        await self._async_set_op_mode(MONITOR_OP_MODE.LIGADO)

    async def async_turn_off(self):
        await self._async_set_op_mode(MONITOR_OP_MODE.DESLIGADO)

    async def _async_set_op_mode(self, op_mode):
        data = await self._manager.set_status(
            set_in({}, self._monitor_key, {"opMode": int(op_mode)})
        )
        if data and isinstance(data, dict):
            self._state = get_in(data, self._monitor_key, self._state)

    @property
    def is_on(self):
        # "on" do aparelho atrasa alguns segundos e fica falso em Automático.
        return self._state.get("opMode", MONITOR_OP_MODE.DESLIGADO) != (
            MONITOR_OP_MODE.DESLIGADO
        )

    @property
    def name(self):
        return f"{self._entry.data.get(CONF_NAME_KEY)} Clorador"

    @property
    def icon(self):
        return "mdi:power"

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._entry.entry_id}_{self._monitor_key[-1]}_switch"

    @property
    def device_info(self):
        return self._device_info
