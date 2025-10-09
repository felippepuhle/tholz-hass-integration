from homeassistant.components.light import (
    LightEntity,
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_EFFECT,
    ColorMode,
    LightEntityFeature,
)

from ...utils.const import DOMAIN, CONF_NAME_KEY, ENTITIES_SCAN_INTERVAL
from ...utils.device import get_device_info
from ...utils.dict import get_in, set_in
from .const import STATIC_EFFECT, EFFECT_MAP, REVERSE_EFFECT_MAP, LED_TYPE
from .utils import get_valid_leds


def get_led_lights(hass, entry, manager, data):
    device_info = get_device_info(entry, data)
    led_lights = []
    for led_key, state in get_valid_leds(data):
        led_lights.append(
            LedLight(
                hass,
                entry,
                manager,
                device_info,
                led_key,
                state,
            )
        )
    return led_lights


def get_color_mode(state):
    return {
        LED_TYPE.RGBW: ColorMode.RGBW,
        LED_TYPE.RGB: ColorMode.RGB,
        LED_TYPE.MONO: ColorMode.BRIGHTNESS,
    }.get(state.get("type"), ColorMode.UNKNOWN)


def can_pick_led_color(state):
    """
    Verifica se é possível alterar as configurações de cor do led.

    As cores só podem ser ajustadas quando o efeito atual for o modo estático (255).
    Qualquer outro efeito tem suas configurações controladas diretamente pelo aplicativo da Tholz.
    """
    return state.get("effect") == STATIC_EFFECT


class LedLight(LightEntity):
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

    async def async_turn_on(self, **kwargs):
        self._state["on"] = True
        if ATTR_EFFECT in kwargs:
            effect = kwargs[ATTR_EFFECT]
            if effect in REVERSE_EFFECT_MAP:
                self._state["effect"] = REVERSE_EFFECT_MAP[effect]
        if can_pick_led_color(self._state):
            if ATTR_BRIGHTNESS in kwargs:
                self._state["brightness"] = int(kwargs[ATTR_BRIGHTNESS] / 2.55)
            if ATTR_RGB_COLOR in kwargs:
                self._state["color"] = list(kwargs[ATTR_RGB_COLOR])
            if ATTR_RGBW_COLOR in kwargs:
                rgbw = kwargs[ATTR_RGBW_COLOR]
                self._state["color"] = list(rgbw[:3])
                self._state["saturation"] = rgbw[3]
        await self._manager.set_status(set_in({}, self._led_key, self._state))

    async def async_turn_off(self):
        self._state["on"] = False
        await self._manager.set_status(set_in({}, self._led_key, self._state))

    @property
    def is_on(self):
        return self._state.get("on", False)

    @property
    def brightness(self):
        if can_pick_led_color(self._state):
            return int(self._state.get("brightness", 100) * 2.55)
        return None

    @property
    def rgb_color(self):
        if can_pick_led_color(self._state):
            return tuple(self._state.get("color", [255, 255, 255]))
        return None

    @property
    def rgbw_color(self):
        if can_pick_led_color(self._state):
            rgb = self._state.get("color", [255, 255, 255])
            w = self._state.get("saturation", 0)
            return (*rgb[:3], w)
        return None

    @property
    def supported_color_modes(self):
        if can_pick_led_color(self._state):
            return {get_color_mode(self._state)}
        return set()

    @property
    def color_mode(self):
        if can_pick_led_color(self._state):
            return get_color_mode(self._state)
        return None

    @property
    def effect(self):
        return EFFECT_MAP.get(self._state.get("effect"))

    @property
    def effect_list(self):
        return list(REVERSE_EFFECT_MAP.keys())

    @property
    def supported_features(self):
        return LightEntityFeature.EFFECT

    @property
    def name(self):
        return f"{self._entry.data.get(CONF_NAME_KEY)} Led"

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._entry.entry_id}_led_{self._led_key[-1]}_light"

    @property
    def device_info(self):
        return self._device_info
