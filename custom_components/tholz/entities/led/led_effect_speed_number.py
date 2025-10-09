from homeassistant.components.number import NumberEntity

from ...utils.const import DOMAIN, CONF_NAME_KEY, ENTITIES_SCAN_INTERVAL
from ...utils.device import get_device_info
from ...utils.dict import get_in, set_in
from .utils import get_valid_leds


def get_led_effect_speed_numbers(hass, entry, manager, data):
    device_info = get_device_info(entry, data)
    led_effect_speed_numbers = []
    for led_key, state in get_valid_leds(data):
        led_effect_speed_numbers.append(
            LedEffectSpeedNumber(
                hass,
                entry,
                manager,
                device_info,
                led_key,
                state,
            )
        )
    return led_effect_speed_numbers


class LedEffectSpeedNumber(NumberEntity):
    def __init__(self, hass, entry, manager, device_info, led_key, state):
        self._hass = hass
        self._entry = entry
        self._manager = manager
        self._device_info = device_info
        self._led_key = led_key

        self._state = state

        self._attr_should_poll = True
        self._attr_scan_interval = ENTITIES_SCAN_INTERVAL

    async def async_update(self):
        data = await self._manager.get_status()
        if data:
            self._state = get_in(data, self._led_key)

    async def async_set_native_value(self, value: float):
        self._state["speed"] = int(value)
        await self._manager.set_status(set_in({}, self._led_key, self._state))

    @property
    def native_value(self):
        return self._state.get("speed")

    @property
    def native_unit_of_measurement(self):
        return "%"

    @property
    def native_min_value(self):
        return 0

    @property
    def native_max_value(self):
        return 100

    @property
    def native_step(self):
        return 1

    @property
    def name(self):
        return f"{self._entry.data.get(CONF_NAME_KEY)} Velocidade de Efeito Led"

    @property
    def icon(self):
        return "mdi:speedometer"

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._entry.entry_id}_led_{self._led_key[-1]}_effect_speed_number"

    @property
    def device_info(self):
        return self._device_info
