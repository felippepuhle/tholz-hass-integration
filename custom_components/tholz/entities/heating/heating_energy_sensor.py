from datetime import datetime, timezone

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy, UnitOfPower

from ...utils.const import (
    DOMAIN,
    CONF_NAME_KEY,
    CONF_ELECTRIC_POWER_PREFIX,
    CONF_ELECTRIC_POWER_DEFAULT_VALUE,
    ENTITIES_SCAN_INTERVAL,
)
from ...utils.device import get_device_info
from ...utils.dict import get_in
from .const import ELECTRIC_HEATING_TYPES
from .utils import get_heating_type, get_valid_heatings


def get_electric_power(entry, heating_key):
    """Potência configurada para a resistência deste circuito, em watts.

    A potência é declarada pelo usuário nas opções da integração, porque o
    controlador não a informa. Zero significa não configurada, e nesse caso
    nenhum sensor de consumo é criado.
    """
    option = f"{CONF_ELECTRIC_POWER_PREFIX}{heating_key[-1]}"
    options = entry.options or {}
    return options.get(
        option, entry.data.get(option, CONF_ELECTRIC_POWER_DEFAULT_VALUE)
    )


def get_electric_heatings(entry, data):
    """Circuitos elétricos que têm potência configurada."""
    result = []
    for heating_key, state in get_valid_heatings(data):
        if get_heating_type(state) not in ELECTRIC_HEATING_TYPES:
            continue
        power = get_electric_power(entry, heating_key)
        if not power or power <= 0:
            continue
        result.append((heating_key, state, power))
    return result


def get_heating_energy_sensors(hass, entry, manager, data):
    device_info = get_device_info(entry, data)
    sensors = []
    for heating_key, state, power in get_electric_heatings(entry, data):
        sensors.append(
            HeatingPowerSensor(
                hass, entry, manager, device_info, heating_key, state, power
            )
        )
        sensors.append(
            HeatingEnergySensor(
                hass, entry, manager, device_info, heating_key, state, power
            )
        )
    return sensors


class HeatingPowerSensor(SensorEntity):
    """Potência instantânea da resistência: a nominal quando o relé está
    acionado, zero quando não está."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def __init__(self, hass, entry, manager, device_info, heating_key, state, power):
        self._hass = hass
        self._entry = entry
        self._manager = manager
        self._device_info = device_info
        self._heating_key = heating_key
        self._state = state
        self._power = power

        self._attr_should_poll = True
        self._attr_scan_interval = ENTITIES_SCAN_INTERVAL

    async def async_update(self):
        data = await self._manager.get_status()
        if data:
            self._state = get_in(data, self._heating_key)

    @property
    def native_value(self):
        if self._state is None:
            return None
        return self._power if self._state.get("on") else 0

    @property
    def name(self):
        return f"{self._entry.data.get(CONF_NAME_KEY)} Potência Apoio Elétrico"

    @property
    def icon(self):
        return "mdi:flash"

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._entry.entry_id}_heating_{self._heating_key[-1]}_power"

    @property
    def device_info(self):
        return self._device_info


class HeatingEnergySensor(RestoreSensor):
    """Energia acumulada da resistência, em kWh.

    O controlador não mede consumo, então a energia é integrada a partir do
    tempo em que o relé fica acionado, multiplicado pela potência nominal.
    O valor é restaurado após reinício para não zerar o histórico.

    Com `state_class` total_increasing, o Painel de Energia do Home Assistant
    deriva sozinho as visões diária, mensal e anual.
    """

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_suggested_display_precision = 3

    def __init__(self, hass, entry, manager, device_info, heating_key, state, power):
        self._hass = hass
        self._entry = entry
        self._manager = manager
        self._device_info = device_info
        self._heating_key = heating_key
        self._state = state
        self._power = power

        self._energy = 0.0
        self._last_seen = None
        self._was_on = False

        self._attr_should_poll = True
        self._attr_scan_interval = ENTITIES_SCAN_INTERVAL

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last = await self.async_get_last_sensor_data()
        if last is not None and last.native_value is not None:
            try:
                self._energy = float(last.native_value)
            except (TypeError, ValueError):
                self._energy = 0.0

    async def async_update(self):
        data = await self._manager.get_status()
        now = datetime.now(timezone.utc)

        if data:
            self._state = get_in(data, self._heating_key)

        # Integra o intervalo que acabou de passar usando o estado com que ele
        # começou, e só depois registra o estado novo. Contar o intervalo com o
        # estado do fim antecipa ou atrasa o consumo em uma amostra.
        if self._last_seen is not None and self._was_on:
            elapsed = (now - self._last_seen).total_seconds()
            if 0 < elapsed < 3600:
                self._energy += self._power * elapsed / 3_600_000

        self._last_seen = now
        self._was_on = bool(self._state and self._state.get("on"))

    @property
    def native_value(self):
        return round(self._energy, 6)

    @property
    def name(self):
        return f"{self._entry.data.get(CONF_NAME_KEY)} Energia Apoio Elétrico"

    @property
    def icon(self):
        return "mdi:lightning-bolt"

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._entry.entry_id}_heating_{self._heating_key[-1]}_energy"

    @property
    def device_info(self):
        return self._device_info
