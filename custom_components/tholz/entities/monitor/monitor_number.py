from homeassistant.components.number import NumberEntity

from ...utils.const import DOMAIN, CONF_NAME_KEY, ENTITIES_SCAN_INTERVAL
from ...utils.device import get_device_info
from ...utils.dict import get_in, set_in
from .utils import get_valid_monitors


def get_monitor_preset_numbers(hass, entry, manager, data):
    device_info = get_device_info(entry, data)
    return [
        MonitorPresetNumber(hass, entry, manager, device_info, monitor_key, state)
        for monitor_key, state in get_valid_monitors(data)
    ]


class MonitorPresetNumber(NumberEntity):
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

    async def async_set_native_value(self, value: float):
        # Só preset é enviado; os demais campos do monitor são somente leitura.
        data = await self._manager.set_status(
            set_in({}, self._monitor_key, {"preset": int(value)})
        )
        if data and isinstance(data, dict):
            self._state = get_in(data, self._monitor_key, self._state)

    @property
    def native_value(self):
        return self._state.get("preset")

    @property
    def native_unit_of_measurement(self):
        return "%"

    @property
    def native_min_value(self):
        return self._state.get("minPreset", 0)

    @property
    def native_max_value(self):
        return self._state.get("maxPreset", 100)

    @property
    def native_step(self):
        return self._state.get("step", 1)

    @property
    def name(self):
        return f"{self._entry.data.get(CONF_NAME_KEY)} Geração de Cloro"

    @property
    def icon(self):
        return "mdi:water-percent"

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._entry.entry_id}_{self._monitor_key[-1]}_preset_number"

    @property
    def device_info(self):
        return self._device_info
