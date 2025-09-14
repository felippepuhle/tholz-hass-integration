from enum import StrEnum

MANUFACTURER = "Tholz"


class DEVICE_MODEL(StrEnum):
    SMART_HEAT_V2 = "P863V0"
    SMART_POOL_V2 = "P844V1"


DEVICE_MODEL_NAMES = {
    DEVICE_MODEL.SMART_HEAT_V2: "Smart Heat V2",
    DEVICE_MODEL.SMART_POOL_V2: "Smart Pool V2",
}
