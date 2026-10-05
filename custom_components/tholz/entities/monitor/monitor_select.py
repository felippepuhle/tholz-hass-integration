from homeassistant.components.select import SelectEntity

from ...utils.const import DOMAIN, CONF_NAME_KEY, ENTITIES_SCAN_INTERVAL
from ...utils.device import get_device_info
from ...utils.dict import get_in, set_in
from .const import MONITOR_OP_MODE
from .utils import get_valid_monitors

OP_MODE_THOLZ_TO_HA = {
    MONITOR_OP_MODE.DESLIGADO: "Desligado",
    MONITOR_OP_MODE.LIGADO: "Ligado",
    MONITOR_OP_MODE.AUTOMATICO: "Automático",
}
OP_MODE_HA_TO_THOLZ = {ha: tholz for tholz, ha in OP_MODE_THOLZ_TO_HA.items()}


def get_monitor_op_mode_selects(hass, entry, manager, data):
    device_info = get_device_info(entry, data)
    return [
        MonitorOpModeSelect(hass, entry, manager, device_info, monitor_key, state)
        for monitor_key, state in get_valid_monitors(data)
    ]


class MonitorOpModeSelect(SelectEntity):
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

    async def async_select_option(self, option):
        if option not in OP_MODE_HA_TO_THOLZ:
            return

        data = await self._manager.set_status(
            set_in({}, self._monitor_key, {"opMode": int(OP_MODE_HA_TO_THOLZ[option])})
        )
        if data and isinstance(data, dict):
            self._state = get_in(data, self._monitor_key, self._state)

    @property
    def options(self):
        return list(OP_MODE_THOLZ_TO_HA.values())

    @property
    def current_option(self):
        return OP_MODE_THOLZ_TO_HA.get(self._state.get("opMode"))

    @property
    def name(self):
        return f"{self._entry.data.get(CONF_NAME_KEY)} Modo de Operação"

    @property
    def icon(self):
        return "mdi:cog"

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._entry.entry_id}_{self._monitor_key[-1]}_op_mode_select"

    @property
    def device_info(self):
        return self._device_info
