from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from datetime import timedelta
import logging
import json

_LOGGER = logging.getLogger(__name__)

class IxfieldCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, api, device_dict, update_interval=timedelta(minutes=2), extract_device_info_sensors=True):
        super().__init__(
            hass,
            _LOGGER,
            name="IXField Device Data",
            update_interval=update_interval,
        )
        self.api = api
        self.device_dict = device_dict
        self.device_ids = list(device_dict.keys())
        self._device_info = {}
        self._device_names = {}
        self._extract_device_info_sensors = extract_device_info_sensors
        self._construct_device_names()

    def _construct_device_names(self):
        """Construct device names based on device dictionary and type."""
        # If device info is not yet available, use device dictionary as fallback
        if not self._device_info:
            for device_id, device_data in self.device_dict.items():
                # Use custom name if available, otherwise use device name
                custom_name = device_data.get("custom_name")
                device_name = device_data.get("name", device_id)
                
                if custom_name:
                    self._device_names[device_id] = custom_name
                else:
                    self._device_names[device_id] = device_name
            _LOGGER.debug(f"Constructed device names (fallback): {self._device_names}")
            return
        
        # Group devices by type for numbering
        type_counts = {}
        type_devices = {}
        
        # First pass: collect device types
        for device_id in self.device_ids:
            device_info = self._device_info.get(device_id, {})
            device_type = device_info.get("type", "Unknown")
            
            if device_type not in type_counts:
                type_counts[device_type] = 0
                type_devices[device_type] = []
            type_counts[device_type] += 1
            type_devices[device_type].append(device_id)
        
        # Second pass: construct names
        for device_id in self.device_ids:
            # Check if device has custom name in device dictionary
            device_data = self.device_dict.get(device_id, {})
            custom_name = device_data.get("custom_name")
            
            if custom_name:
                self._device_names[device_id] = custom_name
                continue
            
            device_info = self._device_info.get(device_id, {})
            device_type = device_info.get("type", "Unknown")
            
            # Use device type as base name
            base_name = device_type.lower().replace(" ", "_")
            
            # If multiple devices of same type, add number
            if type_counts[device_type] > 1:
                # Find position of this device in the list for this type
                device_index = type_devices[device_type].index(device_id) + 1
                self._device_names[device_id] = f"{base_name}{device_index}"
            else:
                self._device_names[device_id] = base_name
        
        _LOGGER.debug(f"Constructed device names: {self._device_names}")

    @property
    def device_info(self):
        """Get device information for all devices."""
        return self._device_info

    def get_device_info(self, device_id):
        """Get device information for a specific device."""
        return self._device_info.get(device_id, {})

    def get_device_name(self, device_id):
        """Get the display name for a device."""
        # Return user-defined name if available
        if device_id in self._device_names:
            return self._device_names[device_id]
        
        # Fallback to device info name or device ID
        device_info = self.get_device_info(device_id)
        return device_info.get("name", device_id)

    def get_device_type(self, device_id):
        """Get the device type."""
        device_info = self.get_device_info(device_id)
        return device_info.get("type", "Unknown")

    def get_device_address(self, device_id):
        """Get the device address information."""
        device_info = self.get_device_info(device_id)
        return device_info.get("address", {})

    def get_device_contact(self, device_id):
        """Get the device contact information."""
        device_info = self.get_device_info(device_id)
        return device_info.get("contact_info", {})

    def get_device_company(self, device_id):
        """Get the device company information."""
        device_info = self.get_device_info(device_id)
        return device_info.get("company", {})

    def get_device_status_summary(self, device_id):
        """Get a summary of device status information."""
        device_info = self.get_device_info(device_id)
        return {
            "name": device_info.get("name", device_id),
            "type": device_info.get("type", "Unknown"),
            "connection_status": device_info.get("connection_status", "Unknown"),
            "operating_mode": device_info.get("operating_mode", "Unknown"),
            "controls_enabled": device_info.get("controls_enabled", False),
            "in_operation_since": device_info.get("in_operation_since"),
            "address": device_info.get("address", {}).get("address", "Unknown"),
            "city": device_info.get("address", {}).get("city", "Unknown"),
        }

    def get_all_devices_status(self):
        """Get status summary for all devices."""
        return {
            device_id: self.get_device_status_summary(device_id)
            for device_id in self.device_ids
        }

    def get_entity_name(self, device_id, entity_type, entity_id=None):
        """Get the name for an entity (sensor, switch, etc.)."""
        device_name = self.get_device_name(device_id)
        
        if entity_id:
            # For specific entities, use device_name_entity_id format
            return f"{device_name}_{entity_id}"
        else:
            # For entity types, use device_name_entity_type format
            return f"{device_name}_{entity_type}"

    def should_extract_device_info_sensors(self):
        """Check if device info sensors should be extracted."""
        return self._extract_device_info_sensors

    def _extract_device_info(self, device_data, device_id):
        """Extract device information from API response."""
        if not device_data or "data" not in device_data:
            return {}
        
        device = device_data.get("data", {}).get("device", {})
        if not device:
            return {}
        
        # Extract basic device information
        device_info = {
            "id": device.get("id"),
            "name": device.get("name"),
            "type": device.get("type"),
            "controller": device.get("controller"),
            "operating_mode": device.get("operatingMode"),
            "in_operation_since": device.get("inOperationSince"),
            "connection_status": device.get("connectionStatus"),
            "connection_status_changed": device.get("connectionStatusChangedTime"),
            "controls_enabled": device.get("controlsEnabled"),
            "controls_override_enabled": device.get("isControlsOverrideEnabled"),
            "control_override_start": device.get("controlOverrideStart"),
            "configuration_in_progress": device.get("isConfigurationJobInProgress"),
            "data_propagation_failed": device.get("dataPropagationFailed"),
            "need_propagate_device_data": device.get("needPropagateDeviceData"),
            "grafana_link": device.get("grafanaLink"),
        }
        
        # Extract address information
        address = device.get("address", {})
        if address:
            device_info["address"] = {
                "id": address.get("id"),
                "address": address.get("address"),
                "code": address.get("code"),
                "city": address.get("city"),
                "lat": address.get("lat"),
                "lng": address.get("lng"),
                "approximate_lat": address.get("approximateLat"),
                "approximate_lng": address.get("approximateLng"),
                "place_id": address.get("placeId"),
                "postal_code": address.get("postalCode"),
            }
        
        # Extract contact information
        contact_info = device.get("contactInfo", {})
        if contact_info:
            device_info["contact_info"] = {
                "name": contact_info.get("name"),
                "phone": contact_info.get("phone"),
                "email": contact_info.get("email"),
                "note": contact_info.get("note"),
            }
        
        # Extract company information
        company = device.get("company", {})
        if company:
            device_info["company"] = {
                "id": company.get("id"),
                "name": company.get("name"),
                "uses_new_eligibility_system": company.get("usesNewEligibilitySystem"),
            }
        
        # Extract thing type information
        thing_type = device.get("thingType", {})
        if thing_type:
            device_info["thing_type"] = {
                "name": thing_type.get("name"),
                "business_name": thing_type.get("businessName"),
                "family": thing_type.get("thingTypeFamily", {}).get("name") if thing_type.get("thingTypeFamily") else None,
            }
        
        return device_info

    async def _async_update_data(self):
        data = {}
        device_info = {}
        
        for device_id in self.device_ids:
            try:
                device_data = await self.api.async_get_device(device_id)
                _LOGGER.debug(f"Received device data for {device_id}: {device_data}")
                if device_data is None:
                    _LOGGER.error(f"API returned None for device {device_id}")
                    continue
                
                data[device_id] = device_data
                # Extract and store device info
                device_info[device_id] = self._extract_device_info(device_data, device_id)
                
            except Exception as err:
                _LOGGER.error(f"Error updating device {device_id}: {err}")
                raise UpdateFailed(f"Error updating device {device_id}: {err}")
        
        # Update the device info cache
        self._device_info = device_info
        
        # Reconstruct device names based on updated device info
        self._construct_device_names()
        
        _LOGGER.debug(f"Final coordinator data: {data}")
        _LOGGER.debug(f"Final device info: {device_info}")
        _LOGGER.debug(f"Final device names: {self._device_names}")
        return data 