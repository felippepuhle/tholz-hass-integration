from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import UnitOfTemperature

from ...utils.const import CONF_NAME_KEY, ENTITIES_SCAN_INTERVAL
from ...utils.dict import get_in
from .utils import get_heating_sensor_type, get_native_temperature


class HeatingReadSensor(SensorEntity):
    """A read-only native heating value backed by a fresh device snapshot."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self, hass, entry, manager, device_info, heating_key, sensor_key, state, name
    ):
        self._hass = hass
        self._entry = entry
        self._manager = manager
        self._device_info = device_info
        self._id = id
        self._heating_key = heating_key
        self._sensor_key = sensor_key

        self._state = state
        self._name = f"{entry.data.get(CONF_NAME_KEY)} {name}"
        self._heating_type = get_heating_sensor_type(state)

        self._attr_should_poll = True
        self._attr_scan_interval = ENTITIES_SCAN_INTERVAL

    async def async_update(self):
        data = await self._manager.get_sensor_status()
        state = get_in(data, self._heating_key)
        self._state = state if isinstance(state, dict) else {}

    @property
    def available(self):
        return (
            self._manager.is_fresh
            and get_heating_sensor_type(self._state) == self._heating_type
            and get_native_temperature(self._state.get(self._sensor_key)) is not None
        )

    @property
    def native_value(self):
        if not self.available:
            return None
        return get_native_temperature(self._state.get(self._sensor_key))

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return "mdi:thermometer"

    @property
    def device_info(self):
        return self._device_info
