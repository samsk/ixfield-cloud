DOMAIN = "ixfield"

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .coordinator import IxfieldCoordinator
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    """Set up the ixfield component."""
    return True 

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up ixfield from a config entry."""
    from .api import IxfieldApi
    from .const import CONF_EMAIL, CONF_PASSWORD, CONF_DEVICES
    import aiohttp

    try:
        email = entry.data[CONF_EMAIL]
        password = entry.data[CONF_PASSWORD]
        device_ids = [d.strip() for d in entry.data[CONF_DEVICES].split(",") if d.strip()]
        
        session = aiohttp.ClientSession()
        api = IxfieldApi(email, password, session)
        await api.async_login()
        
        coordinator = IxfieldCoordinator(hass, api, device_ids)
        await coordinator.async_config_entry_first_refresh()

        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}
        hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

        # Set up platforms
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "sensor")
        )
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "switch")
        )
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "binary_sensor")
        )
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "climate")
        )
        
        return True
    except Exception as ex:
        _LOGGER.error(f"Failed to set up IXField integration: {ex}")
        return False

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "switch", "binary_sensor", "climate"])
    
    if unload_ok and DOMAIN in hass.data:
        # Clean up coordinator and session
        if entry.entry_id in hass.data[DOMAIN]:
            coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
            if hasattr(coordinator.api, '_session'):
                await coordinator.api._session.close()
            del hass.data[DOMAIN][entry.entry_id]
        
        if not hass.data[DOMAIN]:
            del hass.data[DOMAIN]
    
    return unload_ok 