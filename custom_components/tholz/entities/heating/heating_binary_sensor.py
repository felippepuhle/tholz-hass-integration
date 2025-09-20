from homeassistant.components.binary_sensor import BinarySensorEntity

from ...utils.const import DOMAIN, CONF_NAME_KEY, ENTITIES_SCAN_INTERVAL
from ...utils.dict import get_in
from .const import HEATING_TYPE
from .utils import get_heating_type


HEATING_BINARY_SENSOR_CONFIG = {
    HEATING_TYPE.SOLAR_PISCINA: {
        "on": {
            "name": "Solar",
            "icon": "mdi:weather-sunset",
        }
    },
}


def get_heating_binary_sensor_config(state):
    heating_type = get_heating_type(state)
    return HEATING_BINARY_SENSOR_CONFIG.get(heating_type)


class HeatingBinarySensor(BinarySensorEntity):
    def __init__(
        self, hass, entry, manager, device_info, heating_key, sensor_key, state
    ):
        self._hass = hass
        self._entry = entry
        self._manager = manager
        self._device_info = device_info
        self._id = id
        self._heating_key = heating_key
        self._sensor_key = sensor_key

        self._state = state

        self._attr_should_poll = True
        self._attr_scan_interval = ENTITIES_SCAN_INTERVAL

    async def async_update(self):
        data = await self._manager.get_status()
        if data:
            self._state = get_in(data, self._heating_key)

    @property
    def is_on(self):
        return bool(self._state.get(self._sensor_key))

    @property
    def name(self):
        config = get_heating_binary_sensor_config(self._state)[self._sensor_key]
        return f"{self._entry.data.get(CONF_NAME_KEY)} {config['name']}"

    @property
    def icon(self):
        config = get_heating_binary_sensor_config(self._state)[self._sensor_key]
        return config["icon"]

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._entry.entry_id}_heating_{self._heating_key[-1]}_{self._sensor_key}_binary_sensor"

    @property
    def device_info(self):
        return self._device_info
