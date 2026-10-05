from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfMass,
    UnitOfTemperature,
    UnitOfVolume,
)

from ...utils.const import DOMAIN, CONF_NAME_KEY, ENTITIES_SCAN_INTERVAL
from ...utils.device import get_device_info
from ...utils.dict import get_in
from .const import MONITOR_STATUS
from .utils import get_valid_monitors

MONITOR_STATUS_NAMES = {
    MONITOR_STATUS.SEM_SAL: "Sem sal",
    MONITOR_STATUS.SAL_BAIXO: "Sal baixo",
    MONITOR_STATUS.SAL_OK: "Sal ok",
    MONITOR_STATUS.SAL_ALTO: "Sal alto",
    MONITOR_STATUS.NIVEL_CRITICO_SAL: "Nível crítico de sal",
}

# Escalas conforme a documentação dos monitores (measure2 vem em m³ inteiros).
MONITOR_SENSOR_CONFIG = {
    "measure0": {
        "name": "Nível de Sal",
        "icon": "mdi:shaker-outline",
        "unit": "ppm",
        "convert": lambda raw: raw,
    },
    "measure1": {
        "name": "Temperatura",
        "icon": "mdi:thermometer",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "convert": lambda raw: raw / 10,
    },
    "measure2": {
        "name": "Volume da Piscina",
        "icon": "mdi:pool",
        "unit": UnitOfVolume.CUBIC_METERS,
        "convert": lambda raw: raw,
    },
    "measure3": {
        "name": "Sal Necessário",
        "icon": "mdi:shaker",
        "unit": UnitOfMass.KILOGRAMS,
        "convert": lambda raw: raw / 10,
    },
    "measure4": {
        "name": "Água a Substituir",
        "icon": "mdi:water-minus",
        "unit": UnitOfVolume.LITERS,
        "convert": lambda raw: raw * 100,
    },
}


def get_monitor_sensors(hass, entry, manager, data):
    device_info = get_device_info(entry, data)
    sensors = []
    for monitor_key, state in get_valid_monitors(data):
        for measure_key in MONITOR_SENSOR_CONFIG:
            if state.get(measure_key) is None:
                continue
            sensors.append(
                MonitorMeasureSensor(
                    hass, entry, manager, device_info, monitor_key, measure_key, state
                )
            )
        sensors.append(
            MonitorStatusSensor(hass, entry, manager, device_info, monitor_key, state)
        )
    return sensors


class MonitorMeasureSensor(SensorEntity):
    def __init__(
        self, hass, entry, manager, device_info, monitor_key, measure_key, state
    ):
        self._hass = hass
        self._entry = entry
        self._manager = manager
        self._device_info = device_info
        self._monitor_key = monitor_key
        self._measure_key = measure_key

        self._state = state

        self._attr_should_poll = True
        self._attr_scan_interval = ENTITIES_SCAN_INTERVAL

    async def async_update(self):
        data = await self._manager.get_status()
        if data:
            self._state = get_in(data, self._monitor_key, self._state)

    @property
    def _config(self):
        return MONITOR_SENSOR_CONFIG[self._measure_key]

    @property
    def native_value(self):
        raw = self._state.get(self._measure_key)
        return self._config["convert"](raw) if raw is not None else None

    @property
    def native_unit_of_measurement(self):
        return self._config["unit"]

    @property
    def device_class(self):
        return self._config.get("device_class")

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    @property
    def name(self):
        return f"{self._entry.data.get(CONF_NAME_KEY)} {self._config['name']}"

    @property
    def icon(self):
        return self._config["icon"]

    @property
    def unique_id(self):
        return (
            f"{DOMAIN}_{self._entry.entry_id}_{self._monitor_key[-1]}"
            f"_{self._measure_key}_sensor"
        )

    @property
    def device_info(self):
        return self._device_info


class MonitorStatusSensor(SensorEntity):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(MONITOR_STATUS_NAMES.values())

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

    @property
    def native_value(self):
        return MONITOR_STATUS_NAMES.get(self._state.get("status"))

    @property
    def name(self):
        return f"{self._entry.data.get(CONF_NAME_KEY)} Estado do Sal"

    @property
    def icon(self):
        return "mdi:gauge"

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._entry.entry_id}_{self._monitor_key[-1]}_status_sensor"

    @property
    def device_info(self):
        return self._device_info
