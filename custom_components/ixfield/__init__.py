DOMAIN = "ixfield"

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .coordinator import IxfieldCoordinator
from .services import async_setup_services, async_unload_services
from .const import CONF_EMAIL, CONF_PASSWORD, CONF_DEVICES, CONF_DEVICE_NAMES, IXFIELD_DEVICE_URL
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    """Set up the ixfield component."""
    # Set up services
    await async_setup_services(hass)
    return True 

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up ixfield from a config entry."""
    from .api import IxfieldApi
    import aiohttp

    try:
        email = entry.data[CONF_EMAIL]
        password = entry.data[CONF_PASSWORD]
        device_ids = [d.strip() for d in entry.data[CONF_DEVICES].split(",") if d.strip()]
        device_names_config = entry.data.get(CONF_DEVICE_NAMES, "")
        
        session = aiohttp.ClientSession()
        api = IxfieldApi(email, password, session)
        await api.async_login()
        
        coordinator = IxfieldCoordinator(hass, api, device_ids, device_names_config=device_names_config)
        await coordinator.async_config_entry_first_refresh()

        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}
        hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

        # Register devices in device registry
        await _register_devices(hass, coordinator, device_ids, entry)

        # Set up platforms
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setups(entry, ["sensor", "switch", "climate"])
        )
        
        return True
    except Exception as ex:
        _LOGGER.error(f"Failed to set up IXField integration: {ex}")
        return False

async def _register_devices(hass: HomeAssistant, coordinator, device_ids, config_entry):
    """Register devices in Home Assistant's device registry."""
    from homeassistant.helpers.device_registry import async_get as async_get_device_registry
    
    device_registry = async_get_device_registry(hass)
    
    for device_id in device_ids:
        device_info = coordinator.get_device_info(device_id)
        if not device_info:
            continue
            
        # Use the new naming system for device registration
        device_name = coordinator.get_device_name(device_id)
        
        # Extract address and contact information
        address_info = device_info.get("address", {})
        contact_info = device_info.get("contact_info", {})
        company_info = device_info.get("company", {})
        thing_type_info = device_info.get("thing_type", {})
        
        # Build suggested area from address information
        suggested_area = None
        if address_info.get("city"):
            suggested_area = address_info.get("city")
        elif address_info.get("address"):
            # Try to extract area from address
            address_parts = address_info.get("address", "").split(",")
            if len(address_parts) > 1:
                suggested_area = address_parts[-1].strip()
        
        # Create device registry entry with enhanced information
        device_registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            manufacturer=company_info.get("name", "IXField"),
            model=device_info.get("type", "Unknown"),
            sw_version=device_info.get("controller", "Unknown"),
            hw_version=thing_type_info.get("name", "Unknown"),
            configuration_url=f"{IXFIELD_DEVICE_URL}/{device_id}",
            suggested_area=suggested_area,
            # Add additional metadata that will be displayed in device card
            entry_type="service",  # Indicates this is a service-based device
        )
        
        # Log device registration details for debugging
        _LOGGER.info(f"Registered device {device_id} ({device_name}) with area suggestion: {suggested_area}")
        if address_info:
            _LOGGER.debug(f"Device {device_id} address: {address_info.get('address', 'N/A')}, {address_info.get('city', 'N/A')}, {address_info.get('postal_code', 'N/A')}")
        if contact_info:
            _LOGGER.debug(f"Device {device_id} contact: {contact_info.get('name', 'N/A')}, {contact_info.get('email', 'N/A')}, {contact_info.get('phone', 'N/A')}")

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "switch", "climate"])
    
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