from homeassistant.components.switch import SwitchEntity

from ...utils.const import DOMAIN, CONF_NAME_KEY, ENTITIES_SCAN_INTERVAL
from .const import OUTPUT_TYPE

OUTPUT_TYPE_NAMES = {
    OUTPUT_TYPE.FILTRO: "Filtro",
    OUTPUT_TYPE.APOIO_ELETRICO: "Apoio Elétrico",
    OUTPUT_TYPE.APOIO_GAS: "Apoio a Gás",
    OUTPUT_TYPE.RECIRCULACAO: "Recirculação",
    OUTPUT_TYPE.BORBULHADOR: "Borbulhador",
    OUTPUT_TYPE.CIRCULACAO: "Circulação",
}
for i in range(10, 20):
    OUTPUT_TYPE_NAMES[OUTPUT_TYPE(i)] = f"Auxiliar {i - 9}"
for i in range(20, 30):
    OUTPUT_TYPE_NAMES[OUTPUT_TYPE(i)] = f"Cascata {i - 19}"
for i in range(30, 40):
    OUTPUT_TYPE_NAMES[OUTPUT_TYPE(i)] = f"Hidro {i - 29}"
for i in range(40, 60):
    OUTPUT_TYPE_NAMES[OUTPUT_TYPE(i)] = f"Interruptor {i - 39}"


class OutputSwitch(SwitchEntity):
    def __init__(self, hass, entry, manager, device_info, output_key, state):
        self._hass = hass
        self._entry = entry
        self._manager = manager
        self._device_info = device_info
        self._output_key = output_key

        self._state = state

        self._attr_should_poll = True
        self._attr_scan_interval = ENTITIES_SCAN_INTERVAL

    async def async_update(self):
        data = await self._manager.get_status()
        if data:
            self._state = data["response"]["outputs"][self._output_key]

    async def async_turn_on(self):
        self._state["on"] = True
        await self._manager.set_status({"outputs": {self._output_key: self._state}})

    async def async_turn_off(self):
        self._state["on"] = False
        await self._manager.set_status({"outputs": {self._output_key: self._state}})

    @property
    def is_on(self):
        return self._state.get("on", False)

    @property
    def name(self):
        type_name = OUTPUT_TYPE_NAMES.get(OUTPUT_TYPE(self._state.get("id")))
        return f"{self._entry.data.get(CONF_NAME_KEY)} {type_name}"

    @property
    def icon(self):
        return "mdi:engine"

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._entry.entry_id}_output_{self._output_key}_switch"

    @property
    def device_info(self):
        return self._device_info
