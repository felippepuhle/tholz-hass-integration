from homeassistant.components.sensor import SensorEntity

from ...utils.const import DOMAIN, CONF_NAME_KEY, ENTITIES_SCAN_INTERVAL
from ...utils.device import MANUFACTURER, DEVICE_MODEL_NAMES

ERROR_TRANSFORM = {
    0: "0: Sem erro ou aviso.",
    1: "1: Sobreaquecimento - O sensor de temperatura do coletor solar identificou um valor elevado. A circulação de água será evitada.",
    2: "2: Anticongelamento - Temperatura muito baixa. A circulação será ativada.",
    3: "3: Falta de Água - Sem água detectada. Hidromassagem desativada.",
    4: "4: Resfriamento da Resistência - Esperando a resistência esfriar.",
    5: "5: Erro de Temperatura - Sensor com leitura inadequada.",
    6: "6: Termostato Desarmado - Sobreaquecimento detectado. Aquecimento desativado.",
    8: "8: Pressão Alta - Verifique a vazão do sistema.",
    9: "9: Pressão Baixa - Baixa pressão no gás refrigerante.",
    10: "10: Baixo Fluxo de Água - Verifique bomba, filtros e registros.",
    11: "11: Ciclo de Degelo - Ciclo de degelo ativado.",
    12: "12: Erro de Alimentação - Alimentação fora da faixa.",
    13: "13: Parâmetro Inconsistente - Verifique setpoints configurados.",
    14: "14: Erro sensor 1 - Verifique o sensor de temperatura T1.",
    15: "15: Erro sensor 2 - Verifique o sensor de temperatura T2.",
    16: "16: Erro sensor 3 - Verifique o sensor de temperatura T3.",
    17: "17: Erro sensor 4 - Verifique o sensor de temperatura T4.",
    18: "18: Erro sensor 5 - Verifique o sensor de temperatura T5.",
    19: "19: Erro sensor 6 - Verifique o sensor de temperatura T6.",
    20: "20: Dados Inconsistentes - Comportamento inesperado. Contate o suporte.",
}

HEADER_SENSOR_CONFIG = {
    "id": {
        "name": "ID",
        "icon": "mdi:identifier",
    },
    "reset": {
        "name": "Reset",
        "icon": "mdi:restart",
    },
    "error": {
        "name": "Erro",
        "icon": "mdi:message-alert-outline",
        "transform": ERROR_TRANSFORM,
    },
    "firmware": {
        "name": "Firmware Controlador Conectividade",
        "icon": "mdi:chip",
    },
    "firmwareSec": {
        "name": "Firmware Controlador Principal",
        "icon": "mdi:chip",
    },
    "timezone": {
        "name": "Fuso Horário",
        "icon": "mdi:earth",
    },
}


class HeaderSensor(SensorEntity):
    def __init__(self, hass, entry, manager, model, sensor_key, state):
        self._hass = hass
        self._entry = entry
        self._manager = manager
        self._model = model
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
    def state(self):
        config = HEADER_SENSOR_CONFIG[self._sensor_key]
        transform = config.get("transform")
        if transform and self._state in transform:
            return transform[self._state]
        return self._state

    @property
    def name(self):
        config = HEADER_SENSOR_CONFIG[self._sensor_key]
        return f"{self._entry.data.get(CONF_NAME_KEY)} {config['name']}"

    @property
    def icon(self):
        config = HEADER_SENSOR_CONFIG[self._sensor_key]
        return config["icon"]

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._entry.entry_id}_header_{self._sensor_key}_sensor"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.data.get(CONF_NAME_KEY),
            "manufacturer": MANUFACTURER,
            "model": DEVICE_MODEL_NAMES.get(self._model),
        }
