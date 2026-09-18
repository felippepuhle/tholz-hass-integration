from homeassistant.components.number import NumberEntity, NumberMode

from ...utils.const import DOMAIN, ENTITIES_SCAN_INTERVAL
from ...utils.device import get_device_info
from ...utils.dict import get_in, set_in
from .utils import get_monitor_entity_name, get_valid_chlorinators

# Valores de fallback caso o dispositivo não informe min/max/step.
DEFAULT_MIN_PRESET = 20
DEFAULT_MAX_PRESET = 100
DEFAULT_STEP = 1


def get_monitor_preset_numbers(hass, entry, manager, data):
    device_info = get_device_info(entry, data)
    return [
        MonitorPresetNumber(hass, entry, manager, device_info, monitor_key, state)
        for monitor_key, state in get_valid_chlorinators(data)
        if state.get("preset") is not None
    ]

class MonitorPresetNumber(NumberEntity):
    """Percentual de geração de cloro (chave editável "preset")."""

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
            entry, monitor_key, "Geração de Cloro"
        )
        self._attr_icon = "mdi:water-percent"
        self._attr_native_unit_of_measurement = "%"
        self._attr_mode = NumberMode.SLIDER
        self._attr_unique_id = (
            f"{DOMAIN}_{entry.entry_id}_monitor_{monitor_key[-1]}_preset_number"
        )

    async def async_update(self):
        data = await self._manager.get_status()
        if data:
            state = get_in(data, self._monitor_key)
            if state is not None:
                self._state = state

    async def async_set_native_value(self, value: float):
        value = int(
            max(self.native_min_value, min(self.native_max_value, round(value)))
        )
        # Envia somente a chave editável; as demais são apenas informativas.
        await self._manager.set_status(
            set_in({}, [*self._monitor_key, "preset"], value)
        )
        self._state["preset"] = value

    @property
    def native_value(self):
        return self._state.get("preset")

    @property
    def native_min_value(self):
        return self._state.get("minPreset", DEFAULT_MIN_PRESET)

    @property
    def native_max_value(self):
        return self._state.get("maxPreset", DEFAULT_MAX_PRESET)

    @property
    def native_step(self):
        return self._state.get("step") or DEFAULT_STEP
