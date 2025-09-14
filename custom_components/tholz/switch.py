from .entities.heating.heating_switch import HEATING_SWITCH_CONFIG, HeatingSwitch
from .entities.output.output_switch import OutputSwitch
from .utils.const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    manager = hass.data[DOMAIN][entry.entry_id]["manager"]
    data = await manager.get_status()
    if not data:
        return

    model = data["response"].get("firmwareSec")

    entities = []
    if "heatings" in data["response"]:
        for heating_key, state in data["response"]["heatings"].items():
            HEATING_TYPE = state.get("type")
            if HEATING_TYPE not in HEATING_SWITCH_CONFIG:
                continue

            entities.append(
                HeatingSwitch(
                    hass,
                    entry,
                    manager,
                    model,
                    heating_key,
                    state,
                )
            )
    if "outputs" in data["response"]:
        for output_key, state in data["response"]["outputs"].items():
            entities.append(
                OutputSwitch(
                    hass,
                    entry,
                    manager,
                    model,
                    output_key,
                    state,
                )
            )

    async_add_entities(entities, update_before_add=True)
