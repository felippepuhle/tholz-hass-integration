from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)

from ...utils.const import DOMAIN, ENTITIES_SCAN_INTERVAL
from ...utils.device import get_device_info
from ...utils.dict import get_in
from .const import MONITOR_STATUS
from .utils import get_monitor_entity_name, get_valid_chlorinators

MONITOR_BINARY_SENSOR_CONFIG = {
    # "on" reflete o estado comandado (ligado/desligado), não a geração
    # efetiva: o firmware reporta on=true mesmo com a bomba (out0) desligada.
    "on": {
        "name": "Ligado",
        "icon": "mdi:flask-outline",
        "device_class": BinarySensorDeviceClass.POWER,
        "value": lambda state: bool(state.get("on")),
    },
    "onAut": {
        "name": "Programação Ativa",
        "icon": "mdi:calendar-clock",
        "device_class": BinarySensorDeviceClass.RUNNING,
        "value": lambda state: bool(state.get("onAut")),
    },
    # Derivado de "status": qualquer coisa diferente de "Sal ok" é problema.
    # Útil para automações/notificações sem precisar comparar strings.
    "status": {
        "name": "Problema no Sal",
        "icon": "mdi:alert-circle-outline",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "value": lambda state: (
            None
            if state.get("status") not in iter(MONITOR_STATUS)
            else state.get("status") != MONITOR_STATUS.SAL_OK
        ),
    },
}

def get_monitor_binary_sensors(hass, entry, manager, data):
    device_info = get_device_info(entry, data)
    binary_sensors = []
    for monitor_key, state in get_valid_chlorinators(data):
        for sensor_key in MONITOR_BINARY_SENSOR_CONFIG:
            if state.get(sensor_key) is None:
                continue
            binary_sensors.append(
                MonitorBinarySensor(
                    hass, entry, manager, device_info, monitor_key, sensor_key, state
                )
            )
    return binary_sensors


class MonitorBinarySensor(BinarySensorEntity):
    def __init__(
        self, hass, entry, manager, device_info, monitor_key, sensor_key, state
    ):
        self._hass = hass
        self._entry = entry
        self._manager = manager
        self._monitor_key = monitor_key
        self._sensor_key = sensor_key
        self._config = MONITOR_BINARY_SENSOR_CONFIG[sensor_key]
        self._state = state

        self._attr_device_info = device_info
        self._attr_should_poll = True
        self._attr_scan_interval = ENTITIES_SCAN_INTERVAL
        self._attr_name = get_monitor_entity_name(
            entry, monitor_key, self._config["name"]
        )
        self._attr_icon = self._config["icon"]
        self._attr_device_class = self._config["device_class"]
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_monitor_{monitor_key[-1]}_{sensor_key}_binary_sensor"

    async def async_update(self):
        data = await self._manager.get_status()
        if data:
            state = get_in(data, self._monitor_key)
            if state is not None:
                self._state = state

    @property
    def is_on(self):
        return self._config["value"](self._state)