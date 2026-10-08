from ...utils.const import DOMAIN
from ...utils.device import get_device_info
from .const import HEATING_TYPE
from .heating_read_sensor import HeatingReadSensor
from .utils import get_heating_sensor_channels, get_heating_sensor_type


HEATING_SETPOINT_SENSOR_NAMES = {
    HEATING_TYPE.APOIO_ELETRICO: "Temperatura Alvo Apoio Elétrico",
    HEATING_TYPE.APOIO_GAS: "Temperatura Alvo Apoio a Gás",
}


def get_heating_setpoint_sensors(hass, entry, manager, data):
    """Publish each backup channel's native sp, never the solar target."""
    device_info = get_device_info(entry, data)
    sensors = []
    for heating_key, state in get_heating_sensor_channels(data):
        name = HEATING_SETPOINT_SENSOR_NAMES.get(get_heating_sensor_type(state))
        if name is not None:
            sensors.append(
                HeatingSetpointSensor(
                    hass, entry, manager, device_info, heating_key, "sp", state, name
                )
            )
    return sensors


class HeatingSetpointSensor(HeatingReadSensor):
    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._entry.entry_id}_heating_{self._heating_key[-1]}_sp_setpoint"
