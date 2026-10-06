from enum import IntEnum


class MONITOR_TYPE(IntEnum):
    CLORADOR = 0
    CLORADOR_TURBO = 1


class MONITOR_OP_MODE(IntEnum):
    DESLIGADO = 0
    LIGADO = 1
    AUTOMATICO = 2


class MONITOR_STATUS(IntEnum):
    SEM_SAL = 0
    SAL_BAIXO = 1
    SAL_OK = 2
    SAL_ALTO = 3
    NIVEL_CRITICO_SAL = 4
