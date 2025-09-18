from enum import IntEnum

from .const import DOMAIN, CONF_NAME_KEY


class DEVICE_MODEL(IntEnum):
    SMART_PLUS_V1 = 1356
    BASIC_SMART_POOL_V1 = 1354
    SMART_POOL_V1 = 11355
    SMART_HEAT_V1 = 21392
    TLZ_SMART_V2 = 31516
    TROCADOR_CALOR_LUX_POOL = 1527
    TROCADOR_THOLZ_TURBO_SILENCE = 1537
    THC30 = 51524
    THC45 = 51528
    THC60 = 51529
    THC80 = 51530
    SMART_HEAT_V2 = 21505
    BASIC_SMART_HEAT = 21534
    BASIC_SMART_HEAT_PAINEL = 21562
    TLS_SMART = 31569
    SMART_LUX = 1551
    BASIC_SMART_POOL_V2 = 1512
    SMART_POOL_V2 = 11462


DEVICE_MODEL_NAMES = {
    DEVICE_MODEL.SMART_PLUS_V1: "SmartPlus 1ª Geração",
    DEVICE_MODEL.BASIC_SMART_POOL_V1: "Basic SmartPool 1ª Geração",
    DEVICE_MODEL.SMART_POOL_V1: "SmartPool 1ª Geração",
    DEVICE_MODEL.SMART_HEAT_V1: "SmartHeat 1ª Geração",
    DEVICE_MODEL.TLZ_SMART_V2: "TLZ Smart 2ª Geração",
    DEVICE_MODEL.TROCADOR_CALOR_LUX_POOL: "Trocador de Calor LuxPool",
    DEVICE_MODEL.TROCADOR_THOLZ_TURBO_SILENCE: "Trocador Tholz TurboSilence",
    DEVICE_MODEL.THC30: "THC30",
    DEVICE_MODEL.THC45: "THC45",
    DEVICE_MODEL.THC60: "THC60",
    DEVICE_MODEL.THC80: "THC80",
    DEVICE_MODEL.SMART_HEAT_V2: "SmartHeat 2ª Geração",
    DEVICE_MODEL.BASIC_SMART_HEAT: "Basic SmartHeat",
    DEVICE_MODEL.BASIC_SMART_HEAT_PAINEL: "Basic SmartHeat Porta de Painel",
    DEVICE_MODEL.TLS_SMART: "TLS Smart",
    DEVICE_MODEL.SMART_LUX: "SmartLux",
    DEVICE_MODEL.BASIC_SMART_POOL_V2: "Basic SmartPool 2ª Geração",
    DEVICE_MODEL.SMART_POOL_V2: "SmartPool 2ª Geração",
}


def get_device_info(entry, data):
    return {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "name": entry.data.get(CONF_NAME_KEY),
        "manufacturer": "Tholz",
        "model": DEVICE_MODEL_NAMES.get(data.get("id")),
    }
