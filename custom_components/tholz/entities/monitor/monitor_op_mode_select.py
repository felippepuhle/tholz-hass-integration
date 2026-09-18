from homeassistant.components.select import SelectEntity

from ...utils.const import DOMAIN, ENTITIES_SCAN_INTERVAL
from ...utils.device import get_device_info
from ...utils.dict import get_in, set_in
from .const import MONITOR_OP_MODE_NAMES
from .utils import get_monitor_entity_name, get_valid_chlorinators

OP_MODE_HA_TO_THOLZ = {ha: tholz for tholz, ha in MONITOR_OP_MODE_NAMES.items()}


def get_monitor_op_mode_selects(hass, entry, manager, data):
    device_info = get_device_info(entry, data)
    return [
        MonitorOpModeSelect(hass, entry, manager, device_info, monitor_key, state)
        for monitor_key, state in get_valid_chlorinators(data)
        if state.get("opMode") is not None
    ]

class MonitorOpModeSelect(SelectEntity):
    """Modo de operação do clorador (chave editável "opMode")."""

    def __init__(self, hass, entry, manager, device_info, monitor_key, state):
        self._hass = hass
        self._entry = entry
        self._manager = manager
        self._monitor_key = monitor_key
        self._state = state

        self._attr_device_info = device_info
        self._attr_should_poll = True
        self._attr_scan_interval = ENTITIES_SCAN_INTERVAL
        self._attr_name = get_monitor_entity_name(
            entry, monitor_key, "Modo Gerador de Cloro"
        )
        self._attr_icon = "mdi:cog-outline"
        self._attr_options = list(MONITOR_OP_MODE_NAMES.values())
        self._attr_unique_id = (
            f"{DOMAIN}_{entry.entry_id}_monitor_{monitor_key[-1]}_op_mode_select"
        )

    async def async_update(self):
        data = await self._manager.get_status()
        if data:
            state = get_in(data, self._monitor_key)
            if state is not None:
                self._state = state

    async def async_select_option(self, option):
        if option not in OP_MODE_HA_TO_THOLZ:
            return

        op_mode = int(OP_MODE_HA_TO_THOLZ[option])
        # Envia somente a chave editável; as demais são apenas informativas.
        await self._manager.set_status(
            set_in({}, [*self._monitor_key, "opMode"], op_mode)
        )
        self._state["opMode"] = op_mode

    @property
    def current_option(self):
        return MONITOR_OP_MODE_NAMES.get(self._state.get("opMode"))
