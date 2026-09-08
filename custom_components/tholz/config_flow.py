from homeassistant import config_entries
import voluptuous as vol

from .entities.heating.const import ELECTRIC_HEATING_TYPES
from .entities.heating.utils import get_heating_type, get_valid_heatings
from .utils.const import (
    DOMAIN,
    CONF_NAME_KEY,
    CONF_HOST_KEY,
    CONF_PORT_KEY,
    CONF_PORT_DEFAULT_VALUE,
    CONF_POLLING_INTERVAL_KEY,
    CONF_POLLING_INTERVAL_DEFAULT_VALUE,
    CONF_ELECTRIC_POWER_PREFIX,
    CONF_ELECTRIC_POWER_DEFAULT_VALUE,
)


def get_electric_power_schema(hass, config_entry):
    """One power field per heating circuit driven by an electric element.

    The controller does not report the element rating, so it is declared here.
    Zero keeps the consumption sensors disabled.
    """
    stored = hass.data.get(DOMAIN, {}).get(config_entry.entry_id)
    if not stored:
        return {}

    data = stored["manager"].last_data
    if not data:
        return {}

    options = config_entry.options or {}
    schema = {}
    for heating_key, state in get_valid_heatings(data):
        if get_heating_type(state) not in ELECTRIC_HEATING_TYPES:
            continue
        option = f"{CONF_ELECTRIC_POWER_PREFIX}{heating_key[-1]}"
        schema[
            vol.Optional(
                option,
                default=options.get(option, CONF_ELECTRIC_POWER_DEFAULT_VALUE),
            )
        ] = int
    return schema


class TholzConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME_KEY],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME_KEY): str,
                    vol.Required(CONF_HOST_KEY): str,
                    vol.Optional(CONF_PORT_KEY, default=CONF_PORT_DEFAULT_VALUE): int,
                    vol.Optional(
                        CONF_POLLING_INTERVAL_KEY,
                        default=CONF_POLLING_INTERVAL_DEFAULT_VALUE,
                    ): int,
                }
            ),
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return TholzConfigFlowOptionsFlowHandler()


class TholzConfigFlowOptionsFlowHandler(config_entries.OptionsFlow):
    # config_entry is provided by Home Assistant and is read-only. Assigning it
    # here raises AttributeError on current releases.

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_options = self.config_entry.options or {}
        current_data = self.config_entry.data or {}

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST_KEY,
                        default=current_options.get(
                            CONF_HOST_KEY, current_data.get(CONF_HOST_KEY)
                        ),
                    ): str,
                    vol.Optional(
                        CONF_PORT_KEY,
                        default=current_options.get(
                            CONF_PORT_KEY, current_data.get(CONF_PORT_KEY)
                        ),
                    ): int,
                    vol.Optional(
                        CONF_POLLING_INTERVAL_KEY,
                        default=current_options.get(
                            CONF_POLLING_INTERVAL_KEY,
                            current_data.get(CONF_POLLING_INTERVAL_KEY),
                        ),
                    ): int,
                    **get_electric_power_schema(self.hass, self.config_entry),
                }
            ),
        )
