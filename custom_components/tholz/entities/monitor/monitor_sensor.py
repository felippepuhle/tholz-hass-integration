from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfMass,
    UnitOfTemperature,
    UnitOfVolume,
)

from ...utils.const import DOMAIN, ENTITIES_SCAN_INTERVAL
from ...utils.device import get_device_info
from ...utils.dict import get_in
from .const import MONITOR_STATUS_NAMES
from .utils import get_monitor_entity_name, get_valid_chlorinators

class MonitorBaseSensor(SensorEntity):
    def __init__(self, hass, entry, manager, device_info, monitor_key, state):
        self._hass = hass
        self._entry = entry
        self._manager = manager
        self._monitor_key = monitor_key
        self._state = state

        self._attr_device_info = device_info
        self._attr_should_poll = True
        self._attr_scan_interval = ENTITIES_SCAN_INTERVAL

    async def async_update(self):
        data = await self._manager.get_status()
        if data:
            state = get_in(data, self._monitor_key)
            if state is not None:
                self._state = state

class MonitorMeasureSensor(MonitorBaseSensor):
    def __init__(
        self, hass, entry, manager, device_info, monitor_key, sensor_key, state
    ):
        super().__init__(hass, entry, manager, device_info, monitor_key, state)
        self._sensor_key = sensor_key
        self._config = CHLORINATOR_SENSOR_CONFIG[sensor_key]

        self._attr_name = get_monitor_entity_name(
            entry, monitor_key, self._config["name"]
        )
        self._attr_icon = self._config["icon"]
        self._attr_native_unit_of_measurement = self._config["unit"]
        self._attr_device_class = self._config.get("device_class")
        self._attr_state_class = self._config.get("state_class")
        self._attr_entity_category = self._config.get("entity_category")
        self._attr_suggested_display_precision = self._config.get("precision", 0)
        self._attr_unique_id = (
            f"{DOMAIN}_{entry.entry_id}_monitor_{monitor_key[-1]}_{sensor_key}_sensor"
        )

    @property
    def native_value(self):
        raw = self._state.get(self._sensor_key)
        if raw is None:
            return None
        value = raw * self._config["scale"]
        precision = self._config.get("precision", 0)
        return round(value, precision) if precision else round(value)

class MonitorRawMeasureSensor(MonitorBaseSensor):
    def __init__(
        self, hass, entry, manager, device_info, monitor_key, sensor_key, state
    ):
        super().__init__(hass, entry, manager, device_info, monitor_key, state)
        self._sensor_key = sensor_key
        index = sensor_key.removeprefix("measure")
        self._attr_name = get_monitor_entity_name(
            entry, monitor_key, f"Medida {index} (bruta)"
        )
        self._attr_icon = "mdi:help-circle-outline"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_entity_registry_enabled_default = False
        self._attr_unique_id = (
            f"{DOMAIN}_{entry.entry_id}_monitor_{monitor_key[-1]}_{sensor_key}_sensor"
        )

    @property
    def native_value(self):
        return self._state.get(self._sensor_key)

class MonitorStatusSensor(MonitorBaseSensor):
    def __init__(self, hass, entry, manager, device_info, monitor_key, state):
        super().__init__(hass, entry, manager, device_info, monitor_key, state)
        self._attr_name = get_monitor_entity_name(entry, monitor_key, "Status do Sal")
        self._attr_icon = "mdi:shaker"
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_options = list(MONITOR_STATUS_NAMES.values())
        self._attr_unique_id = (
            f"{DOMAIN}_{entry.entry_id}_monitor_{monitor_key[-1]}_status_sensor"
        )

    @property
    def native_value(self):
        # Valores fora da tabela são tratados como desconhecidos,
        # conforme a documentação ("erros de construção").
        return MONITOR_STATUS_NAMES.get(self._state.get("status"))

    @property
    def extra_state_attributes(self):
        return {"status_code": self._state.get("status")}

# Escalas conforme a documentação da Tholz (Monitoradores / Clorador):
#   measure0 -> ppm            (x1)
#   measure1 -> °C             (/10)
#   measure2 -> volume em L    (x1000)
#   measure3 -> kg             (/10)
#   measure4 -> L              (x100)
CHLORINATOR_SENSOR_CONFIG = {
    "measure0": {
        "name": "Nível de Sal",
        "icon": "mdi:shaker-outline",
        "unit": "ppm",
        "scale": 1,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "measure1": {
        "name": "Temperatura da Água",
        "icon": "mdi:thermometer-water",
        "unit": UnitOfTemperature.CELSIUS,
        "scale": 0.1,
        "precision": 1,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "measure2": {
        "name": "Volume da Piscina",
        "icon": "mdi:pool",
        "unit": UnitOfVolume.LITERS,
        "scale": 1000,
        "device_class": SensorDeviceClass.VOLUME_STORAGE,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    "measure3": {
        "name": "Sal a Adicionar",
        "icon": "mdi:basket-plus-outline",
        "unit": UnitOfMass.KILOGRAMS,
        "scale": 0.1,
        "precision": 1,
        "device_class": SensorDeviceClass.WEIGHT,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "measure4": {
        "name": "Água a Substituir",
        "icon": "mdi:water-sync",
        "unit": UnitOfVolume.LITERS,
        "scale": 100,
        "device_class": SensorDeviceClass.VOLUME_STORAGE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
}

def get_monitor_sensors(hass, entry, manager, data):
    device_info = get_device_info(entry, data)
    sensors = []
    for monitor_key, state in get_valid_chlorinators(data):
        for sensor_key in CHLORINATOR_SENSOR_CONFIG:
            if state.get(sensor_key) is None:
                continue
            sensors.append(
                MonitorMeasureSensor(
                    hass, entry, manager, device_info, monitor_key, sensor_key, state
                )
            )
        # Medidas não documentadas (ex.: measure5, measure6 no THC45) viram
        # sensores de diagnóstico desabilitados por padrão, com o valor bruto,
        # para facilitar descobrir o significado comparando com o app.
        for index in range(12):
            sensor_key = f"measure{index}"
            if sensor_key in CHLORINATOR_SENSOR_CONFIG:
                continue
            if state.get(sensor_key) is None:
                continue
            sensors.append(
                MonitorRawMeasureSensor(
                    hass, entry, manager, device_info, monitor_key, sensor_key, state
                )
            )
        if state.get("status") is not None:
            sensors.append(
                MonitorStatusSensor(
                    hass, entry, manager, device_info, monitor_key, state
                )
            )
    return sensors
