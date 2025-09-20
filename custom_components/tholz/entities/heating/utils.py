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
