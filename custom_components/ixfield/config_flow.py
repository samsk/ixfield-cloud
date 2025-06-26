import aiohttp
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .api import IxfieldApi
from .const import CONF_DEVICE_DICT, CONF_EXTRACT_DEVICE_INFO_SENSORS, DOMAIN

_LOGGER = logging.getLogger(__name__)


class IxfieldConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for IXField Cloud."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._email = None
        self._password = None
        self._extract_device_info_sensors = None

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step - credentials and device discovery."""
        errors = {}

        if user_input is not None:
            self._email = user_input[CONF_EMAIL]
            self._password = user_input[CONF_PASSWORD]
            self._extract_device_info_sensors = user_input.get(
                CONF_EXTRACT_DEVICE_INFO_SENSORS, True
            )

            # Check if already configured
            await self.async_set_unique_id(self._email)
            self._abort_if_unique_id_configured()

            # Validate credentials and get available devices
            session = None
            try:
                session = aiohttp.ClientSession()
                api = IxfieldApi(self._email, self._password, session)
                await api.async_login()

                # Get available devices
                devices_response = await api.async_get_user_devices()
                if devices_response is None:
                    errors["base"] = "failed_to_fetch_devices"
                    return self.async_show_form(
                        step_id="user",
                        data_schema=self._get_data_schema(),
                        errors=errors,
                    )

                # Extract devices from response
                devices_data = (
                    devices_response.get("data", {}).get("me", {}).get("devices", [])
                )
                if not devices_data:
                    errors["base"] = "no_devices_found"
                    return self.async_show_form(
                        step_id="user",
                        data_schema=self._get_data_schema(),
                        errors=errors,
                    )

                await session.close()

                # Create device dictionary with all discovered devices
                device_dict = {}
                for device in devices_data:
                    device_id = device.get("id")
                    if device_id:
                        device_dict[device_id] = {
                            "id": device_id,
                            "name": device.get("name", "Unknown Device"),
                            "custom_name": device.get("customName"),
                            "connection_status": device.get(
                                "connectionStatus", "Unknown"
                            ),
                            "controller": device.get("controller"),
                            "operating_mode": device.get("operatingMode"),
                            "connection_status_changed_time": device.get(
                                "connectionStatusChangedTime"
                            ),
                            "company": device.get("company", {}),
                            "connection_type": device.get("connectionType", {}).get(
                                "formattedValue", "Unknown"
                            ),
                        }

                # Create the config entry
                return self.async_create_entry(
                    title=f"IXField Cloud ({self._email})",
                    data={
                        CONF_EMAIL: self._email,
                        CONF_PASSWORD: self._password,
                        CONF_DEVICE_DICT: device_dict,
                        CONF_EXTRACT_DEVICE_INFO_SENSORS: self._extract_device_info_sensors,
                    },
                )

            except Exception as ex:
                _LOGGER.error(f"Authentication failed: {ex}")
                errors["base"] = "invalid_auth"
                if session:
                    await session.close()

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_data_schema(),
            errors=errors,
            description_placeholders={
                "docs_url": "https://github.com/yourusername/ixfield-homeassistant"
            },
        )

    def _get_data_schema(self):
        """Get the data schema for the form."""
        return vol.Schema(
            {
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_EXTRACT_DEVICE_INFO_SENSORS, default=True): bool,
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return IxfieldOptionsFlow()


class IxfieldOptionsFlow(config_entries.OptionsFlow):
    """Handle IXField options."""

    def __init__(self):
        """Initialize options flow."""
        self._reload_result = None

    async def async_step_init(self, user_input=None):
        """Manage the IXField options."""
        if user_input is not None:
            if user_input.get("action") == "reload_sensors":
                return await self.async_step_reload_sensors()
            elif user_input.get("action") == "reenumerate_sensors":
                return await self.async_step_reenumerate_sensors()
            elif user_input.get("action") == "reenumerate_devices":
                return await self.async_step_reenumerate_devices()
            elif user_input.get("action") == "update_devices":
                return await self.async_step_update_devices()
            else:
                # Update devices configuration
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("action"): vol.In(
                        {
                            "update_devices": "Update Device Configuration",
                            "reenumerate_devices": "Re-enumerate Devices (Discover New Devices)",
                            "reload_sensors": "Reload Sensors (Refresh Data)",
                            "reenumerate_sensors": "Re-enumerate Sensors (Rediscover)",
                        }
                    )
                }
            ),
            description_placeholders={
                "reload_help": "Refresh sensor data without rediscovery",
                "reenumerate_help": "Rediscover all sensors and devices",
                "reenumerate_devices_help": "Fetch fresh device list from IXField API",
            },
        )

    async def async_step_reload_sensors(self, user_input=None):
        """Handle sensor reload."""
        if user_input is not None:
            if user_input.get("confirm"):
                try:
                    # Get the coordinator and trigger a refresh
                    hass = self.hass
                    if (
                        DOMAIN in hass.data
                        and self.config_entry.entry_id in hass.data[DOMAIN]
                    ):
                        coordinator = hass.data[DOMAIN][self.config_entry.entry_id][
                            "coordinator"
                        ]
                        await coordinator.async_request_refresh()
                        _LOGGER.info("Sensors reloaded successfully")
                        return self.async_create_entry(
                            title="", data=self.config_entry.data
                        )
                    else:
                        return self.async_abort(reason="integration_not_loaded")
                except Exception as e:
                    _LOGGER.error(f"Failed to reload sensors: {e}")
                    return self.async_abort(reason="reload_failed")
            else:
                return self.async_create_entry(title="", data=self.config_entry.data)

        return self.async_show_form(
            step_id="reload_sensors",
            data_schema=vol.Schema({vol.Required("confirm"): bool}),
            description_placeholders={
                "action": "reload sensors",
                "description": "This will refresh all sensor data from the IXField API without rediscovering sensors.",
            },
        )

    async def async_step_reenumerate_sensors(self, user_input=None):
        """Handle sensor re-enumeration."""
        if user_input is not None:
            if user_input.get("confirm"):
                try:
                    # Get the coordinator and trigger a full refresh
                    hass = self.hass
                    if (
                        DOMAIN in hass.data
                        and self.config_entry.entry_id in hass.data[DOMAIN]
                    ):
                        coordinator = hass.data[DOMAIN][self.config_entry.entry_id][
                            "coordinator"
                        ]

                        # Force a full refresh
                        await coordinator.async_request_refresh()

                        # Trigger entity reload for all platforms
                        await hass.config_entries.async_reload(
                            self.config_entry.entry_id
                        )

                        _LOGGER.info("Sensors re-enumerated successfully")
                        return self.async_create_entry(
                            title="", data=self.config_entry.data
                        )
                    else:
                        return self.async_abort(reason="integration_not_loaded")
                except Exception as e:
                    _LOGGER.error(f"Failed to re-enumerate sensors: {e}")
                    return self.async_abort(reason="reenumerate_failed")
            else:
                return self.async_create_entry(title="", data=self.config_entry.data)

        return self.async_show_form(
            step_id="reenumerate_sensors",
            data_schema=vol.Schema({vol.Required("confirm"): bool}),
            description_placeholders={
                "action": "re-enumerate sensors",
                "description": "This will rediscover all sensors, switches, and other entities from your IXField devices. This may take a moment.",
            },
        )

    async def async_step_reenumerate_devices(self, user_input=None):
        """Handle device re-enumeration."""
        if user_input is not None:
            if user_input.get("confirm"):
                try:
                    # Get fresh device data from API
                    email = self.config_entry.data["email"]
                    password = self.config_entry.data["password"]

                    session = aiohttp.ClientSession()
                    api = IxfieldApi(email, password, session)
                    await api.async_login()

                    devices_response = await api.async_get_user_devices()
                    await session.close()

                    if devices_response is None:
                        return self.async_abort(reason="failed_to_fetch_devices")

                    devices_data = (
                        devices_response.get("data", {})
                        .get("me", {})
                        .get("devices", [])
                    )

                    # Create device dictionary with all discovered devices
                    device_dict = {}
                    for device in devices_data:
                        device_id = device.get("id")
                        if device_id:
                            device_dict[device_id] = {
                                "id": device_id,
                                "name": device.get("name", "Unknown Device"),
                                "custom_name": device.get("customName"),
                                "connection_status": device.get(
                                    "connectionStatus", "Unknown"
                                ),
                                "controller": device.get("controller"),
                                "operating_mode": device.get("operatingMode"),
                                "connection_status_changed_time": device.get(
                                    "connectionStatusChangedTime"
                                ),
                                "company": device.get("company", {}),
                                "connection_type": device.get("connectionType", {}).get(
                                    "formattedValue", "Unknown"
                                ),
                            }

                    # Update the config entry with new device data
                    hass = self.hass
                    hass.config_entries.async_update_entry(
                        self.config_entry,
                        data={
                            "email": self.config_entry.data["email"],
                            "password": self.config_entry.data["password"],
                            CONF_DEVICE_DICT: device_dict,
                            CONF_EXTRACT_DEVICE_INFO_SENSORS: self.config_entry.data.get(
                                CONF_EXTRACT_DEVICE_INFO_SENSORS, True
                            ),
                        },
                    )

                    # Reload the integration with new configuration
                    await hass.config_entries.async_reload(self.config_entry.entry_id)

                    _LOGGER.info(
                        f"Devices re-enumerated successfully. Found {len(device_dict)} devices."
                    )
                    return self.async_create_entry(
                        title="",
                        data={
                            "email": self.config_entry.data["email"],
                            "password": self.config_entry.data["password"],
                            CONF_DEVICE_DICT: device_dict,
                            CONF_EXTRACT_DEVICE_INFO_SENSORS: self.config_entry.data.get(
                                CONF_EXTRACT_DEVICE_INFO_SENSORS, True
                            ),
                        },
                    )

                except Exception as e:
                    _LOGGER.error(f"Failed to re-enumerate devices: {e}")
                    return self.async_abort(reason="reenumerate_devices_failed")
            else:
                return self.async_create_entry(title="", data=self.config_entry.data)

        return self.async_show_form(
            step_id="reenumerate_devices",
            data_schema=vol.Schema({vol.Required("confirm"): bool}),
            description_placeholders={
                "action": "re-enumerate devices",
                "description": "This will fetch the latest device list from IXField API and update your configuration. This is useful when you add new devices to your IXField account.",
            },
        )

    async def async_step_update_devices(self, user_input=None):
        """Handle device configuration update."""
        if user_input is not None:
            extract_device_info_sensors = user_input.get(
                CONF_EXTRACT_DEVICE_INFO_SENSORS, True
            )

            # Get available devices
            try:
                email = self.config_entry.data[CONF_EMAIL]
                password = self.config_entry.data[CONF_PASSWORD]

                session = aiohttp.ClientSession()
                api = IxfieldApi(email, password, session)
                await api.async_login()

                devices_response = await api.async_get_user_devices()
                await session.close()

                if devices_response is None:
                    return self.async_abort(reason="failed_to_fetch_devices")

                devices_data = (
                    devices_response.get("data", {}).get("me", {}).get("devices", [])
                )

                # Create device dictionary with all discovered devices
                device_dict = {}
                for device in devices_data:
                    device_id = device.get("id")
                    if device_id:
                        device_dict[device_id] = {
                            "id": device_id,
                            "name": device.get("name", "Unknown Device"),
                            "custom_name": device.get("customName"),
                            "connection_status": device.get(
                                "connectionStatus", "Unknown"
                            ),
                            "controller": device.get("controller"),
                            "operating_mode": device.get("operatingMode"),
                            "connection_status_changed_time": device.get(
                                "connectionStatusChangedTime"
                            ),
                            "company": device.get("company", {}),
                            "connection_type": device.get("connectionType", {}).get(
                                "formattedValue", "Unknown"
                            ),
                        }

                # Update the config entry
                hass = self.hass
                hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={
                        CONF_EMAIL: self.config_entry.data[CONF_EMAIL],
                        CONF_PASSWORD: self.config_entry.data[CONF_PASSWORD],
                        CONF_DEVICE_DICT: device_dict,
                        CONF_EXTRACT_DEVICE_INFO_SENSORS: extract_device_info_sensors,
                    },
                )

                # Reload the integration with new configuration
                await hass.config_entries.async_reload(self.config_entry.entry_id)

                _LOGGER.info("Device configuration updated successfully")
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_EMAIL: self.config_entry.data[CONF_EMAIL],
                        CONF_PASSWORD: self.config_entry.data[CONF_PASSWORD],
                        CONF_DEVICE_DICT: device_dict,
                        CONF_EXTRACT_DEVICE_INFO_SENSORS: extract_device_info_sensors,
                    },
                )

            except Exception as e:
                _LOGGER.error(f"Failed to update device configuration: {e}")
                return self.async_abort(reason="update_failed")

        return self.async_show_form(
            step_id="update_devices",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_EXTRACT_DEVICE_INFO_SENSORS,
                        default=self.config_entry.data.get(
                            CONF_EXTRACT_DEVICE_INFO_SENSORS, True
                        ),
                    ): bool,
                }
            ),
            description_placeholders={
                "description": "Update device configuration. All available devices will be automatically selected."
            },
        )
