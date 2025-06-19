import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN, CONF_DEVICES
from .api import IxfieldApi
import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

class IxfieldConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for IXField Cloud."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._email = None
        self._password = None
        self._devices = None

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self._email = user_input[CONF_EMAIL]
            self._password = user_input[CONF_PASSWORD]
            self._devices = user_input[CONF_DEVICES]

            # Check if already configured
            await self.async_set_unique_id(self._email)
            self._abort_if_unique_id_configured()

            # Validate credentials
            session = None
            try:
                session = aiohttp.ClientSession()
                api = IxfieldApi(self._email, self._password, session)
                await api.async_login()
                
                # If we get here, credentials are valid
                return self.async_create_entry(
                    title=f"IXField Cloud ({self._email})",
                    data={
                        CONF_EMAIL: self._email,
                        CONF_PASSWORD: self._password,
                        CONF_DEVICES: self._devices,
                    }
                )
            except Exception as ex:
                _LOGGER.error(f"Authentication failed: {ex}")
                errors["base"] = "invalid_auth"
            finally:
                if session:
                    await session.close()

        data_schema = vol.Schema({
            vol.Required(CONF_EMAIL): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Required(CONF_DEVICES, description="Comma-separated device IDs"): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "docs_url": "https://github.com/yourusername/ixfield-homeassistant"
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return IxfieldOptionsFlow(config_entry)


class IxfieldOptionsFlow(config_entries.OptionsFlow):
    """Handle IXField options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the IXField options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_DEVICES,
                    default=self.config_entry.data.get(CONF_DEVICES, "")
                ): str,
            })
        ) 