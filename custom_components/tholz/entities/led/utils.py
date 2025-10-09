def get_valid_leds(data):
    """
    Retorna uma lista de leds válidos.

    Cada item do retorno é uma tupla (path, state).
    """
    leds = []

    # formato atual (v2)
    if "leds" in data:
        for led_key, state in data["leds"].items():
            leds.append((["leds", led_key], state))

    # formato legacy (v1)
    if "light" in data:
        leds.append((["light"], data["light"]))

    return leds
