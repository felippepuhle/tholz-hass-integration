from math import isfinite


def get_native_temperature(raw):
    """Convert a finite native tenths-of-a-degree number, never a missing zero."""
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return None
    try:
        value = raw / 10
    except OverflowError:
        return None
    return value if isfinite(value) else None


def get_heating_sensor_channels(data):
    """Discover read-only channels without treating numeric zero as missing."""
    if not isinstance(data, dict):
        return []
    channels = []
    heatings = data.get("heatings")
    if isinstance(heatings, dict):
        channels.extend(
            (["heatings", key], state)
            for key, state in heatings.items()
            if isinstance(state, dict)
        )
    if isinstance(data.get("heating"), dict):
        channels.append((["heating"], data["heating"]))
    return channels


def get_heating_sensor_type(state):
    """Require a native integer channel type (with the legacy mode fallback)."""
    if not isinstance(state, dict):
        return None
    heating_type = get_heating_type(state)
    if isinstance(heating_type, bool) or not isinstance(heating_type, int):
        return None
    return heating_type


def get_heating_type(state):
    """
    Obtém o tipo de aquecimento do state.

    Devices mais antigos usam o campo "mode" em vez de "type",
    Neste caso, se "type" não estiver presente é feito o fallback para "mode".
    """
    heating_type = state.get("type")
    if heating_type is None:
        heating_type = state.get("mode")
    return heating_type


def heating_has_valid_temperatures(state):
    """
    Verifica se o dispositivo possui pelo menos uma temperatura válida.

    A entidade só é considerada válida se ao menos um dos sensores
    de temperatura (t1..t5) retornar um valor diferente de 0 ou None.
    """
    keys = ["t1", "t2", "t3", "t4", "t5"]
    values = [state.get(k) for k in keys]
    return any(v not in (0, None) for v in values)


def get_valid_heatings(data):
    """
    Retorna uma lista de aquecimentos válidos.

    Um aquecimento é considerado válido se possuir ao menos uma temperatura válida.

    Cada item do retorno é uma tupla (path, state).
    """
    heatings = []

    # formato atual (v2)
    if "heatings" in data:
        for heating_key, state in data["heatings"].items():
            if not heating_has_valid_temperatures(state):
                continue
            heatings.append((["heatings", heating_key], state))

    # formato legacy (v1)
    if "heating" in data and heating_has_valid_temperatures(data["heating"]):
        heatings.append((["heating"], data["heating"]))

    return heatings
