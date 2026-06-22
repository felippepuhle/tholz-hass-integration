from homeassistant.components.select import SelectEntity

from ...utils.const import DOMAIN, CONF_NAME_KEY, ENTITIES_SCAN_INTERVAL
from ...utils.device import get_device_info
from ...utils.dict import get_in, set_in
from .const import HEATING_TYPE, HEATING_FAN_MODE
from .utils import get_heating_type, get_valid_heatings


FAN_MODE_THOLZ_TO_HA = {
    HEATING_FAN_MODE.SILENCIOSO: "Silencioso",
    HEATING_FAN_MODE.INTELIGENTE: "Inteligente",
}
FAN_MODE_HA_TO_THOLZ = {ha: tholz for tholz, ha in FAN_MODE_THOLZ_TO_HA.items()}


def get_heating_fan_mode_selects(hass, entry, manager, data):
    device_info = get_device_info(entry, data)
    fan_mode_selects = []

    for heating_key, state in get_valid_heatings(data):
        if get_heating_type(state) != HEATING_TYPE.TROCADOR_CALOR_FAIRLAND:
            continue

        fan_mode_selects.append(
            HeatingFanModeSelect(
                hass,
                entry,
                manager,
                device_info,
                heating_key,
                state,
            )
        )

    return fan_mode_selects


class HeatingFanModeSelect(SelectEntity):
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

    async def async_select_option(self, option):
        if option not in FAN_MODE_HA_TO_THOLZ:
            return

        self._state["fanMode"] = int(FAN_MODE_HA_TO_THOLZ[option])
        await self._manager.set_status(set_in({}, self._heating_key, self._state))

    @property
    def options(self):
        return list(FAN_MODE_THOLZ_TO_HA.values())

    @property
    def current_option(self):
        return FAN_MODE_THOLZ_TO_HA.get(self._state.get("fanMode"))

    @property
    def name(self):
        return f"{self._entry.data.get(CONF_NAME_KEY)} Modo Ventilador"

    @property
    def icon(self):
        return "mdi:fan"

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._entry.entry_id}_heating_{self._heating_key[-1]}_fan_mode_select"

    @property
    def device_info(self):
        return self._device_info
