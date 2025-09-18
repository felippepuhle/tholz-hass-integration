from .entities.heating.heating_switch import HEATING_SWITCH_CONFIG, HeatingSwitch
from .entities.output.output_switch import OUTPUT_TYPE_NAMES, OutputSwitch
from .utils.const import DOMAIN
from .utils.device import get_device_info


async def async_setup_entry(hass, entry, async_add_entities):
    manager = hass.data[DOMAIN][entry.entry_id]["manager"]
    data = await manager.get_status()
    if not data:
        return

    device_info = get_device_info(entry, data["response"])

    entities = []
    if "heatings" in data["response"]:
        for heating_key, state in data["response"]["heatings"].items():
            heating_type = state.get("type")
            if heating_type not in HEATING_SWITCH_CONFIG:
                continue

            entities.append(
                HeatingSwitch(
                    hass,
                    entry,
                    manager,
                    device_info,
                    heating_key,
                    state,
                )
            )
    if "outputs" in data["response"]:
        for output_key, state in data["response"]["outputs"].items():
            if state is None:
                continue

            output_type = state.get("id")
            if output_type not in OUTPUT_TYPE_NAMES:
                continue

            entities.append(
                OutputSwitch(
                    hass,
                    entry,
                    manager,
                    device_info,
                    output_key,
                    state,
                )
            )

    async_add_entities(entities, update_before_add=True)
