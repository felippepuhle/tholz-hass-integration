from ...utils.const import CONF_NAME_KEY
from .const import CHLORINATOR_TYPES


def get_valid_monitors(data):
    """
    Retorna uma lista de monitoradores válidos.

    Cada item do retorno é uma tupla (path, state).
    """
    monitors = []

    if "monitors" in data:
        for monitor_key, state in data["monitors"].items():
            if not isinstance(state, dict):
                continue
            monitors.append((["monitors", monitor_key], state))

    return monitors

def get_valid_chlorinators(data):
    """Retorna somente os monitoradores do tipo clorador (normal ou turbo)."""
    return [
        (monitor_key, state)
        for monitor_key, state in get_valid_monitors(data)
        if state.get("type") in CHLORINATOR_TYPES
    ]

def get_monitor_entity_name(entry, monitor_key, suffix):
    """
    Monta o nome da entidade.

    O índice só é adicionado quando não for o primeiro monitorador,
    mantendo nomes limpos no caso comum de um único gerador de cloro.
    """
    base = entry.data.get(CONF_NAME_KEY)
    index = monitor_key[-1].removeprefix("monitor")
    if index in ("", "0"):
        return f"{base} {suffix}"
    return f"{base} {suffix} {int(index) + 1}"
