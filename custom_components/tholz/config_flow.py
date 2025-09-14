from homeassistant import config_entries
import voluptuous as vol

from .utils.const import (
    DOMAIN,
    CONF_NAME_KEY,
    CONF_HOST_KEY,
    CONF_PORT_KEY,
    CONF_PORT_DEFAULT_VALUE,
    CONF_POLLING_INTERVAL_KEY,
    CONF_POLLING_INTERVAL_DEFAULT_VALUE,
)


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
        return TholzConfigFlowOptionsFlowHandler(config_entry)


class TholzConfigFlowOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

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
                }
            ),
        )
