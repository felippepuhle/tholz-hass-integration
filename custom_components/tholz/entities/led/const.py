from enum import IntEnum

STATIC_EFFECT = 255

EFFECT_MAP = {
    **{i: f"Efeito {i + 1}" for i in range(8)},
    STATIC_EFFECT: "Estático",
}

REVERSE_EFFECT_MAP = {v: k for k, v in EFFECT_MAP.items()}


class LED_TYPE(IntEnum):
    MONO = 0
    RGB = 1
    RGBW = 2
