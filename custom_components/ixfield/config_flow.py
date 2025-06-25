import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN, CONF_DEVICES, CONF_DEVICE_NAMES
from .api import IxfieldApi
import aiohttp
import logging
import json

_LOGGER = logging.getLogger(__name__)

class IxfieldConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for IXField Cloud."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._email = None
        self._password = None
        self._devices = None
        self._device_names = None

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self._email = user_input[CONF_EMAIL]
            self._password = user_input[CONF_PASSWORD]
            self._devices = user_input[CONF_DEVICES]
            self._device_names = user_input.get(CONF_DEVICE_NAMES, "")

            # Check if already configured
            await self.async_set_unique_id(self._email)
            self._abort_if_unique_id_configured()

            # Validate credentials and get device information
            session = None
            try:
                session = aiohttp.ClientSession()
                api = IxfieldApi(self._email, self._password, session)
                await api.async_login()
                
                # Parse device IDs and validate them
                device_ids = [d.strip() for d in self._devices.split(",") if d.strip()]
                if not device_ids:
                    errors["base"] = "no_devices"
                    return self.async_show_form(
                        step_id="user",
                        data_schema=self._get_data_schema(),
                        errors=errors
                    )
                
                # Test access to devices and get their types
                device_types = {}
                for device_id in device_ids:
                    try:
                        device_data = await api.async_get_device(device_id)
                        if device_data and "data" in device_data and "device" in device_data["data"]:
                            device_type = device_data["data"]["device"].get("type", "Unknown")
                            device_types[device_id] = device_type
                        else:
                            errors["base"] = f"invalid_device_{device_id}"
                            return self.async_show_form(
                                step_id="user",
                                data_schema=self._get_data_schema(),
                                errors=errors
                            )
                    except Exception as e:
                        _LOGGER.error(f"Error accessing device {device_id}: {e}")
                        errors["base"] = f"device_access_error_{device_id}"
                        return self.async_show_form(
                            step_id="user",
                            data_schema=self._get_data_schema(),
                            errors=errors
                        )
                
                # If we get here, credentials and devices are valid
                return self.async_create_entry(
                    title=f"IXField Cloud ({self._email})",
                    data={
                        CONF_EMAIL: self._email,
                        CONF_PASSWORD: self._password,
                        CONF_DEVICES: self._devices,
                        CONF_DEVICE_NAMES: self._device_names,
                    }
                )
            except Exception as ex:
                _LOGGER.error(f"Authentication failed: {ex}")
                errors["base"] = "invalid_auth"
            finally:
                if session:
                    await session.close()

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_data_schema(),
            errors=errors,
            description_placeholders={
                "docs_url": "https://github.com/yourusername/ixfield-homeassistant",
                "devices_help": "Comma-separated device IDs",
                "names_help": "Optional JSON mapping of device IDs to custom names (e.g., {\"device1\": \"Pool Controller\", \"device2\": \"Garden System\"})"
            }
        )

    def _get_data_schema(self):
        """Get the data schema for the form."""
        return vol.Schema({
            vol.Required(CONF_EMAIL): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Required(CONF_DEVICES): str,
            vol.Optional(CONF_DEVICE_NAMES, default=""): str,
        })

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
        self._reload_result = None

    async def async_step_init(self, user_input=None):
        """Manage the IXField options."""
        if user_input is not None:
            if user_input.get("action") == "reload_sensors":
                return await self.async_step_reload_sensors()
            elif user_input.get("action") == "reenumerate_sensors":
                return await self.async_step_reenumerate_sensors()
            elif user_input.get("action") == "update_devices":
                return await self.async_step_update_devices()
            else:
                # Update devices configuration
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_DEVICES,
                    default=self.config_entry.data.get(CONF_DEVICES, "")
                ): str,
                vol.Optional(
                    CONF_DEVICE_NAMES,
                    default=self.config_entry.data.get(CONF_DEVICE_NAMES, "")
                ): str,
                vol.Required("action"): vol.In({
                    "update_devices": "Update Device Configuration",
                    "reload_sensors": "Reload Sensors (Refresh Data)",
                    "reenumerate_sensors": "Re-enumerate Sensors (Rediscover)"
                })
            }),
            description_placeholders={
                "devices_help": "Comma-separated device IDs",
                "names_help": "Optional JSON mapping of device IDs to custom names",
                "reload_help": "Refresh sensor data without rediscovery",
                "reenumerate_help": "Rediscover all sensors and devices"
            }
        )

    async def async_step_reload_sensors(self, user_input=None):
        """Handle sensor reload."""
        if user_input is not None:
            if user_input.get("confirm"):
                try:
                    # Get the coordinator and trigger a refresh
                    hass = self.hass
                    if DOMAIN in hass.data and self.config_entry.entry_id in hass.data[DOMAIN]:
                        coordinator = hass.data[DOMAIN][self.config_entry.entry_id]["coordinator"]
                        await coordinator.async_request_refresh()
                        _LOGGER.info("Sensors reloaded successfully")
                        return self.async_create_entry(title="", data=self.config_entry.data)
                    else:
                        return self.async_abort(reason="integration_not_loaded")
                except Exception as e:
                    _LOGGER.error(f"Failed to reload sensors: {e}")
                    return self.async_abort(reason="reload_failed")
            else:
                return self.async_create_entry(title="", data=self.config_entry.data)

        return self.async_show_form(
            step_id="reload_sensors",
            data_schema=vol.Schema({
                vol.Required("confirm"): bool
            }),
            description_placeholders={
                "action": "reload sensors",
                "description": "This will refresh all sensor data from the IXField API without rediscovering sensors."
            }
        )

    async def async_step_reenumerate_sensors(self, user_input=None):
        """Handle sensor re-enumeration."""
        if user_input is not None:
            if user_input.get("confirm"):
                try:
                    # Get the coordinator and trigger a full refresh
                    hass = self.hass
                    if DOMAIN in hass.data and self.config_entry.entry_id in hass.data[DOMAIN]:
                        coordinator = hass.data[DOMAIN][self.config_entry.entry_id]["coordinator"]
                        
                        # Force a full refresh
                        await coordinator.async_request_refresh()
                        
                        # Trigger entity reload for all platforms
                        await hass.config_entries.async_reload(self.config_entry.entry_id)
                        
                        _LOGGER.info("Sensors re-enumerated successfully")
                        return self.async_create_entry(title="", data=self.config_entry.data)
                    else:
                        return self.async_abort(reason="integration_not_loaded")
                except Exception as e:
                    _LOGGER.error(f"Failed to re-enumerate sensors: {e}")
                    return self.async_abort(reason="reenumerate_failed")
            else:
                return self.async_create_entry(title="", data=self.config_entry.data)

        return self.async_show_form(
            step_id="reenumerate_sensors",
            data_schema=vol.Schema({
                vol.Required("confirm"): bool
            }),
            description_placeholders={
                "action": "re-enumerate sensors",
                "description": "This will rediscover all sensors, switches, and other entities from your IXField devices. This may take a moment."
            }
        )

    async def async_step_update_devices(self, user_input=None):
        """Handle device configuration update."""
        if user_input is not None:
            # Validate the new device configuration
            new_devices = user_input.get(CONF_DEVICES, "")
            new_device_names = user_input.get(CONF_DEVICE_NAMES, "")
            device_ids = [d.strip() for d in new_devices.split(",") if d.strip()]
            
            if not device_ids:
                return self.async_show_form(
                    step_id="update_devices",
                    data_schema=vol.Schema({
                        vol.Optional(
                            CONF_DEVICES,
                            default=new_devices
                        ): str,
                        vol.Optional(
                            CONF_DEVICE_NAMES,
                            default=new_device_names
                        ): str,
                    }),
                    errors={"base": "no_devices"}
                )
            
            # Validate device names JSON if provided
            if new_device_names:
                try:
                    json.loads(new_device_names)
                except json.JSONDecodeError:
                    return self.async_show_form(
                        step_id="update_devices",
                        data_schema=vol.Schema({
                            vol.Optional(
                                CONF_DEVICES,
                                default=new_devices
                            ): str,
                            vol.Optional(
                                CONF_DEVICE_NAMES,
                                default=new_device_names
                            ): str,
                        }),
                        errors={"base": "invalid_device_names_json"}
                )
            
            # Test the new configuration
            try:
                email = self.config_entry.data[CONF_EMAIL]
                password = self.config_entry.data[CONF_PASSWORD]
                
                session = aiohttp.ClientSession()
                api = IxfieldApi(email, password, session)
                await api.async_login()
                
                # Test access to at least one device
                if device_ids:
                    test_device = device_ids[0]
                    test_data = await api.async_get_device(test_device)
                    if test_data is None:
                        raise Exception(f"Cannot access device {test_device}")
                
                await session.close()
                
                # Update the config entry
                hass = self.hass
                hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: password,
                        CONF_DEVICES: new_devices,
                        CONF_DEVICE_NAMES: new_device_names,
                    }
                )
                
                # Reload the integration with new configuration
                await hass.config_entries.async_reload(self.config_entry.entry_id)
                
                _LOGGER.info("Device configuration updated successfully")
                return self.async_create_entry(title="", data={
                    CONF_EMAIL: email,
                    CONF_PASSWORD: password,
                    CONF_DEVICES: new_devices,
                    CONF_DEVICE_NAMES: new_device_names,
                })
                
            except Exception as e:
                _LOGGER.error(f"Failed to update device configuration: {e}")
                await session.close()
                return self.async_show_form(
                    step_id="update_devices",
                    data_schema=vol.Schema({
                        vol.Optional(
                            CONF_DEVICES,
                            default=new_devices
                        ): str,
                        vol.Optional(
                            CONF_DEVICE_NAMES,
                            default=new_device_names
                        ): str,
                    }),
                    errors={"base": "update_failed"}
                )

        return self.async_show_form(
            step_id="update_devices",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_DEVICES,
                    default=self.config_entry.data.get(CONF_DEVICES, "")
                ): str,
                vol.Optional(
                    CONF_DEVICE_NAMES,
                    default=self.config_entry.data.get(CONF_DEVICE_NAMES, "")
                ): str,
            }),
            description_placeholders={
                "devices_help": "Comma-separated device IDs",
                "names_help": "Optional JSON mapping of device IDs to custom names (e.g., {\"device1\": \"Pool Controller\", \"device2\": \"Garden System\"})",
                "description": "Update the list of devices to monitor and their custom names. This will reload the integration with the new configuration."
            }
        ) 