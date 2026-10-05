from .const import MONITOR_TYPE


def get_valid_monitors(data):
    """
    Retorna os monitoradores de cloradores como tuplas (path, state).
    """
    monitors = []
    for monitor_key, state in (data.get("monitors") or {}).items():
        if not isinstance(state, dict):
            continue
        if state.get("type") not in tuple(MONITOR_TYPE):
            continue
        monitors.append((["monitors", monitor_key], state))
    return monitors
