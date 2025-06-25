"""Services for IXField integration."""
import logging
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.const import CONF_ENTITY_ID
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up IXField services."""
    
    async def device_control(call: ServiceCall) -> None:
        """Control all aspects of an IXField device."""
        device_id = call.data["device_id"]
        controls = call.data.get("controls", {})
        
        _LOGGER.info(f"Controlling device {device_id} with settings: {controls}")
        
        # Find the coordinator for this device
        coordinator = None
        for entry_id, data in hass.data[DOMAIN].items():
            coord = data["coordinator"]
            if device_id in coord.device_ids:
                coordinator = coord
                break
        
        if not coordinator:
            _LOGGER.error(f"Could not find coordinator for device {device_id}")
            return
        
        # Control mapping
        control_mapping = {
            "circulation_pump": "filtrationState",
            "lighting": "lightsState",
            "counterflow": "jetstreamState",
            "target_temperature": "poolTempWithSettings",
            "target_orp": "targetORP",
            "target_ph": "targetpH",
            "agent_volume": "remainingAgentA",
            "heater_mode": "targetHeaterMode"
        }
        
        success_count = 0
        total_controls = 0
        
        for control_name, value in controls.items():
            if control_name in control_mapping:
                api_control_name = control_mapping[control_name]
                total_controls += 1
                
                try:
                    # Convert boolean values to strings for API
                    if isinstance(value, bool):
                        value = "true" if value else "false"
                    else:
                        value = str(value)
                    
                    success = await coordinator.api.async_set_control(device_id, api_control_name, value)
                    if success:
                        _LOGGER.info(f"Successfully set {control_name} to {value}")
                        success_count += 1
                    else:
                        _LOGGER.error(f"Failed to set {control_name} to {value}")
                except Exception as e:
                    _LOGGER.error(f"Error setting {control_name}: {e}")
        
        if total_controls > 0:
            _LOGGER.info(f"Device control completed: {success_count}/{total_controls} controls set successfully")
            # Trigger a coordinator refresh to update the UI
            await coordinator.async_request_refresh()
    
    async def device_service_sequence(call: ServiceCall) -> None:
        """Start a service sequence on an IXField device."""
        device_id = call.data["device_id"]
        sequence_name = call.data["sequence_name"]
        
        _LOGGER.info(f"Starting service sequence {sequence_name} on device {device_id}")
        
        # Find the coordinator for this device
        coordinator = None
        for entry_id, data in hass.data[DOMAIN].items():
            coord = data["coordinator"]
            if device_id in coord.device_ids:
                coordinator = coord
                break
        
        if not coordinator:
            _LOGGER.error(f"Could not find coordinator for device {device_id}")
            return
        
        try:
            success = await coordinator.api.async_set_control(device_id, sequence_name, "true")
            if success:
                _LOGGER.info(f"Successfully started service sequence {sequence_name}")
                # Trigger a coordinator refresh to update the UI
                await coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"Failed to start service sequence {sequence_name}")
        except Exception as e:
            _LOGGER.error(f"Error starting service sequence {sequence_name}: {e}")
    
    async def device_status(call: ServiceCall) -> None:
        """Get comprehensive status of an IXField device."""
        device_id = call.data["device_id"]
        
        _LOGGER.info(f"Getting status for device {device_id}")
        
        # Find the coordinator for this device
        coordinator = None
        for entry_id, data in hass.data[DOMAIN].items():
            coord = data["coordinator"]
            if device_id in coord.device_ids:
                coordinator = coord
                break
        
        if not coordinator:
            _LOGGER.error(f"Could not find coordinator for device {device_id}")
            return
        
        try:
            # Get current device data
            device_data = coordinator.data.get(device_id, {})
            device = device_data.get("data", {}).get("device", {})
            
            if not device:
                _LOGGER.error(f"No device data found for {device_id}")
                return
            
            # Extract status information
            status = {
                "device_id": device_id,
                "name": device.get("name", "Unknown"),
                "type": device.get("type", "Unknown"),
                "controller": device.get("controller", "Unknown"),
                "operating_mode": device.get("operatingMode", "Unknown"),
                "connection_status": device.get("connectionStatus", "Unknown"),
                "controls_enabled": device.get("controlsEnabled", False),
                "sensors": {},
                "controls": {},
                "service_sequences": []
            }
            
            # Extract sensor values
            operating_values = device.get("liveDeviceData", {}).get("operatingValues", [])
            for value in operating_values:
                name = value.get("name")
                if name:
                    status["sensors"][name] = {
                        "value": value.get("value"),
                        "desired_value": value.get("desiredValue"),
                        "label": value.get("label"),
                        "type": value.get("type"),
                        "settable": value.get("settable", False)
                    }
            
            # Extract control states
            controls = device.get("liveDeviceData", {}).get("controls", [])
            for control in controls:
                name = control.get("name")
                if name:
                    status["controls"][name] = {
                        "value": control.get("value"),
                        "label": control.get("label"),
                        "type": control.get("type"),
                        "settable": control.get("settable", False),
                        "forbidden_by_user": control.get("forbiddenByUser", False),
                        "forbidden_by_technology": control.get("forbiddenByTechnology", False)
                    }
            
            # Extract service sequences
            service_sequences = device.get("liveDeviceData", {}).get("serviceSequences", [])
            for sequence in service_sequences:
                name = sequence.get("name")
                if name:
                    status["service_sequences"].append({
                        "name": name,
                        "label": sequence.get("label"),
                        "settable": sequence.get("settable", False),
                        "forbidden_by_user": sequence.get("forbiddenByUser", False),
                        "forbidden_by_technology": sequence.get("forbiddenByTechnology", False)
                    })
            
            _LOGGER.info(f"Device status retrieved for {device_id}: {status}")
            
            # Store status in hass.data for potential use by other components
            if DOMAIN not in hass.data:
                hass.data[DOMAIN] = {}
            if "device_status" not in hass.data[DOMAIN]:
                hass.data[DOMAIN]["device_status"] = {}
            hass.data[DOMAIN]["device_status"][device_id] = status
            
        except Exception as e:
            _LOGGER.error(f"Error getting device status for {device_id}: {e}")
    
    async def device_refresh(call: ServiceCall) -> None:
        """Manually refresh data for an IXField device."""
        device_id = call.data["device_id"]
        
        _LOGGER.info(f"Manually refreshing data for device {device_id}")
        
        # Find the coordinator for this device
        coordinator = None
        for entry_id, data in hass.data[DOMAIN].items():
            coord = data["coordinator"]
            if device_id in coord.device_ids:
                coordinator = coord
                break
        
        if not coordinator:
            _LOGGER.error(f"Could not find coordinator for device {device_id}")
            return
        
        try:
            await coordinator.async_request_refresh()
            _LOGGER.info(f"Successfully refreshed data for device {device_id}")
        except Exception as e:
            _LOGGER.error(f"Error refreshing data for device {device_id}: {e}")
    
    async def get_device_info(call: ServiceCall) -> None:
        """Get comprehensive device information including address and contact details."""
        device_id = call.data["device_id"]
        
        _LOGGER.info(f"Getting comprehensive info for device {device_id}")
        
        # Find the coordinator for this device
        coordinator = None
        for entry_id, data in hass.data[DOMAIN].items():
            coord = data["coordinator"]
            if device_id in coord.device_ids:
                coordinator = coord
                break
        
        if not coordinator:
            _LOGGER.error(f"Could not find coordinator for device {device_id}")
            return
        
        try:
            # Get comprehensive device information
            device_info = coordinator.get_device_info(device_id)
            device_name = coordinator.get_device_name(device_id)
            
            if not device_info:
                _LOGGER.error(f"No device info found for {device_id}")
                return
            
            # Extract and log detailed information
            address_info = device_info.get("address", {})
            contact_info = device_info.get("contact_info", {})
            company_info = device_info.get("company", {})
            
            _LOGGER.info(f"=== Device Information for {device_name} ({device_id}) ===")
            _LOGGER.info(f"Device Type: {device_info.get('type', 'Unknown')}")
            _LOGGER.info(f"Controller: {device_info.get('controller', 'Unknown')}")
            _LOGGER.info(f"Connection Status: {device_info.get('connection_status', 'Unknown')}")
            _LOGGER.info(f"Operating Mode: {device_info.get('operating_mode', 'Unknown')}")
            _LOGGER.info(f"In Operation Since: {device_info.get('in_operation_since', 'Unknown')}")
            
            if address_info:
                _LOGGER.info(f"=== Address Information ===")
                _LOGGER.info(f"Address: {address_info.get('address', 'N/A')}")
                _LOGGER.info(f"City: {address_info.get('city', 'N/A')}")
                _LOGGER.info(f"Postal Code: {address_info.get('postal_code', 'N/A')}")
                _LOGGER.info(f"Coordinates: {address_info.get('lat', 'N/A')}, {address_info.get('lng', 'N/A')}")
            
            if contact_info:
                _LOGGER.info(f"=== Contact Information ===")
                _LOGGER.info(f"Contact Name: {contact_info.get('name', 'N/A')}")
                _LOGGER.info(f"Contact Email: {contact_info.get('email', 'N/A')}")
                _LOGGER.info(f"Contact Phone: {contact_info.get('phone', 'N/A')}")
                if contact_info.get('note'):
                    _LOGGER.info(f"Contact Note: {contact_info.get('note')}")
            
            if company_info:
                _LOGGER.info(f"=== Company Information ===")
                _LOGGER.info(f"Company: {company_info.get('name', 'N/A')}")
                _LOGGER.info(f"Company ID: {company_info.get('id', 'N/A')}")
            
            # Store comprehensive info in hass.data for potential use by other components
            if DOMAIN not in hass.data:
                hass.data[DOMAIN] = {}
            if "device_info" not in hass.data[DOMAIN]:
                hass.data[DOMAIN]["device_info"] = {}
            hass.data[DOMAIN]["device_info"][device_id] = {
                "device_info": device_info,
                "device_name": device_name,
                "address_info": address_info,
                "contact_info": contact_info,
                "company_info": company_info
            }
            
        except Exception as e:
            _LOGGER.error(f"Error getting device info for {device_id}: {e}")

    async def reload_sensors(call: ServiceCall) -> None:
        """Reload all sensors for all IXField integrations."""
        _LOGGER.info("Reloading all IXField sensors")
        
        try:
            # Reload all coordinators
            for entry_id, data in hass.data[DOMAIN].items():
                if "coordinator" in data:
                    coordinator = data["coordinator"]
                    await coordinator.async_request_refresh()
            
            _LOGGER.info("Successfully reloaded all IXField sensors")
            
        except Exception as e:
            _LOGGER.error(f"Error reloading sensors: {e}")

    async def reenumerate_sensors(call: ServiceCall) -> None:
        """Re-enumerate all sensors for all IXField integrations."""
        _LOGGER.info("Re-enumerating all IXField sensors")
        
        try:
            # Get all config entries for this integration
            config_entries = hass.config_entries.async_entries(DOMAIN)
            
            for config_entry in config_entries:
                # Reload the entire integration
                await hass.config_entries.async_reload(config_entry.entry_id)
            
            _LOGGER.info("Successfully re-enumerated all IXField sensors")
            
        except Exception as e:
            _LOGGER.error(f"Error re-enumerating sensors: {e}")

    async def reload_integration(call: ServiceCall) -> None:
        """Reload a specific IXField integration."""
        entry_id = call.data.get("entry_id")
        
        if not entry_id:
            _LOGGER.error("No entry_id provided for integration reload")
            return
        
        _LOGGER.info(f"Reloading IXField integration with entry_id: {entry_id}")
        
        try:
            # Find the config entry
            config_entry = None
            for entry in hass.config_entries.async_entries(DOMAIN):
                if entry.entry_id == entry_id:
                    config_entry = entry
                    break
            
            if not config_entry:
                _LOGGER.error(f"Config entry {entry_id} not found")
                return
            
            # Reload the integration
            await hass.config_entries.async_reload(config_entry.entry_id)
            _LOGGER.info(f"Successfully reloaded IXField integration {entry_id}")
            
        except Exception as e:
            _LOGGER.error(f"Error reloading integration {entry_id}: {e}")
    
    # Register the services
    hass.services.async_register(DOMAIN, "device_control", device_control)
    hass.services.async_register(DOMAIN, "device_service_sequence", device_service_sequence)
    hass.services.async_register(DOMAIN, "device_status", device_status)
    hass.services.async_register(DOMAIN, "device_refresh", device_refresh)
    hass.services.async_register(DOMAIN, "get_device_info", get_device_info)
    hass.services.async_register(DOMAIN, "reload_sensors", reload_sensors)
    hass.services.async_register(DOMAIN, "reenumerate_sensors", reenumerate_sensors)
    hass.services.async_register(DOMAIN, "reload_integration", reload_integration)

async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload IXField services."""
    hass.services.async_remove(DOMAIN, "device_control")
    hass.services.async_remove(DOMAIN, "device_service_sequence")
    hass.services.async_remove(DOMAIN, "device_status")
    hass.services.async_remove(DOMAIN, "device_refresh")
    hass.services.async_remove(DOMAIN, "get_device_info")
    hass.services.async_remove(DOMAIN, "reload_sensors")
    hass.services.async_remove(DOMAIN, "reenumerate_sensors")
    hass.services.async_remove(DOMAIN, "reload_integration") 