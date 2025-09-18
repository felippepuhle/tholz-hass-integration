from homeassistant.components.binary_sensor import BinarySensorEntity

from ...utils.const import DOMAIN, CONF_NAME_KEY, ENTITIES_SCAN_INTERVAL


HEADER_BINARY_SENSOR_CONFIG = {
    "updating": {
        "name": "Atualizando",
        "icon": "mdi:download",
        "device_class": "update",
    },
    "error": {
        "name": "Erro",
        "icon": "mdi:alert-outline",
        "device_class": "problem",
    },
}


class HeaderBinarySensor(BinarySensorEntity):
    def __init__(self, hass, entry, manager, device_info, sensor_key, state):
        self._hass = hass
        self._entry = entry
        self._manager = manager
        self._device_info = device_info
        self._id = id
        self._sensor_key = sensor_key

        self._state = state

        self._attr_should_poll = True
        self._attr_scan_interval = ENTITIES_SCAN_INTERVAL

    async def async_update(self):
        data = await self._manager.get_status()
        if data:
            self._state = data["response"].get(self._sensor_key)

    @property
    def is_on(self):
        return bool(self._state)

    @property
    def name(self):
        config = HEADER_BINARY_SENSOR_CONFIG[self._sensor_key]
        return f"{self._entry.data.get(CONF_NAME_KEY)} {config['name']}"

    @property
    def icon(self):
        config = HEADER_BINARY_SENSOR_CONFIG[self._sensor_key]
        return config["icon"]

    @property
    def device_class(self):
        config = HEADER_BINARY_SENSOR_CONFIG[self._sensor_key]
        return config["device_class"]

    @property
    def unique_id(self):
        return (
            f"{DOMAIN}_{self._entry.entry_id}_header_{self._sensor_key}_binary_sensor"
        )

    @property
    def device_info(self):
        return self._device_info
