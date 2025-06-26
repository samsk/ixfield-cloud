from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN, IXFIELD_DEVICE_URL
from .entity_helper import EntityNamingMixin, create_unique_id
import logging

_LOGGER = logging.getLogger(__name__)

def create_device_info_sensors(coordinator, device_id, device_name, device_info):
    """Create sensors for device information like address, contact, etc."""
    sensors = []
    
    # Address information sensors
    address_info = device_info.get("address", {})
    if address_info:
        if address_info.get("address"):
            sensors.append(DeviceInfoSensor(
                coordinator, device_id, device_name,
                "device_address", "Device Address",
                address_info.get("address"), "mdi:map-marker"
            ))
        
        if address_info.get("city"):
            sensors.append(DeviceInfoSensor(
                coordinator, device_id, device_name,
                "device_address_city", "Device Address City",
                address_info.get("city"), "mdi:city"
            ))
        
        if address_info.get("postal_code"):
            sensors.append(DeviceInfoSensor(
                coordinator, device_id, device_name,
                "device_address_postal_code", "Device Address Postal Code",
                address_info.get("postal_code"), "mdi:mailbox"
            ))
        
        # Address location sensors
        if address_info.get("lat") and address_info.get("lng"):
            lat = address_info.get("lat")
            lng = address_info.get("lng")
            location_value = f"{lat}, {lng}"
            sensors.append(DeviceInfoSensor(
                coordinator, device_id, device_name,
                "device_address_location", "Device Address Location",
                location_value, "mdi:map-marker"
            ))
    
    # Contact information sensors
    contact_info = device_info.get("contact_info", {})
    if contact_info:
        if contact_info.get("name"):
            sensors.append(DeviceInfoSensor(
                coordinator, device_id, device_name,
                "device_contact_name", "Contact Name",
                contact_info.get("name"), "mdi:account"
            ))
        
        if contact_info.get("email"):
            sensors.append(DeviceInfoSensor(
                coordinator, device_id, device_name,
                "device_contact_email", "Contact Email",
                contact_info.get("email"), "mdi:email"
            ))
        
        if contact_info.get("phone"):
            sensors.append(DeviceInfoSensor(
                coordinator, device_id, device_name,
                "device_contact_phone", "Contact Phone",
                contact_info.get("phone"), "mdi:phone"
            ))
    
    # Company information sensors
    company_info = device_info.get("company", {})
    if company_info and company_info.get("name"):
        sensors.append(DeviceInfoSensor(
            coordinator, device_id, device_name,
            "device_company", "Company",
            company_info.get("name"), "mdi:office-building"
        ))
    
    # Controller information sensors
    if device_info.get("controller"):
        sensors.append(DeviceInfoSensor(
            coordinator, device_id, device_name,
            "device_controller", "Controller",
            device_info.get("controller"), "mdi:controller"
        ))
    
    # Device status sensors
    if device_info.get("connection_status"):
        sensors.append(DeviceInfoSensor(
            coordinator, device_id, device_name,
            "device_connection_status", "Connection Status",
            device_info.get("connection_status"), "mdi:wifi"
        ))
    
    if device_info.get("operating_mode"):
        sensors.append(DeviceInfoSensor(
            coordinator, device_id, device_name,
            "device_operating_mode", "Operating Mode",
            device_info.get("operating_mode"), "mdi:cog"
        ))
    
    if device_info.get("in_operation_since"):
        sensors.append(DeviceInfoSensor(
            coordinator, device_id, device_name,
            "device_in_operation_since", "In Operation Since",
            device_info.get("in_operation_since"), "mdi:clock-start"
        ))
    
    return sensors

class DeviceInfoSensor(CoordinatorEntity, SensorEntity, EntityNamingMixin):
    """Sensor for displaying device information like address, contact, etc."""
    
    def __init__(self, coordinator, device_id, device_name, sensor_id, sensor_name, value, icon):
        # Setup entity naming before super().__init__()
        self.setup_entity_naming(device_name, sensor_id, "sensor", sensor_name)
        super().__init__(coordinator)
        
        self._device_id = device_id
        self._device_name = device_name
        self._sensor_id = sensor_id
        self._value = value
        self._attr_icon = icon
        self._attr_unique_id = create_unique_id(device_id, sensor_id, "sensor")
        
        # Device info sensors are read-only
        self._attr_should_poll = False
        
        # Set device class and state class for proper grouping
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
    
    @property
    def unique_id(self):
        return self._attr_unique_id
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        # Update value from current device info
        self._update_value_from_device_info()
        return self._value
    
    def _update_value_from_device_info(self):
        """Update the sensor value from current device info."""
        device_info = self.coordinator.get_device_info(self._device_id)
        
        if self._sensor_id == "device_address":
            self._value = device_info.get("address", {}).get("address")
        elif self._sensor_id == "device_address_city":
            self._value = device_info.get("address", {}).get("city")
        elif self._sensor_id == "device_address_postal_code":
            self._value = device_info.get("address", {}).get("postal_code")
        elif self._sensor_id == "device_address_location":
            lat = device_info.get("address", {}).get("lat")
            lng = device_info.get("address", {}).get("lng")
            if lat and lng:
                self._value = f"{lat}, {lng}"
            else:
                self._value = None
        elif self._sensor_id == "device_contact_name":
            self._value = device_info.get("contact_info", {}).get("name")
        elif self._sensor_id == "device_contact_email":
            self._value = device_info.get("contact_info", {}).get("email")
        elif self._sensor_id == "device_contact_phone":
            self._value = device_info.get("contact_info", {}).get("phone")
        elif self._sensor_id == "device_company":
            self._value = device_info.get("company", {}).get("name")
        elif self._sensor_id == "device_controller":
            self._value = device_info.get("controller")
        elif self._sensor_id == "device_connection_status":
            self._value = device_info.get("connection_status")
        elif self._sensor_id == "device_operating_mode":
            self._value = device_info.get("operating_mode")
        elif self._sensor_id == "device_in_operation_since":
            # Use string value directly since we're not using timestamp device class
            self._value = device_info.get("in_operation_since")
        else:
            self._value = None
    
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        super()._handle_coordinator_update()
        # Update the value and force a state update
        self._update_value_from_device_info()
        self.async_write_ha_state()
    
    @property
    def device_info(self):
        """Return device info."""
        device_info = self.coordinator.get_device_info(self._device_id)
        company = device_info.get("company", {})
        thing_type = device_info.get("thing_type", {})
        
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._device_name,
            "manufacturer": company.get("name", "IXField"),
            "model": device_info.get("type", "Unknown"),
            "sw_version": device_info.get("controller", "Unknown"),
            "hw_version": thing_type.get("name", "Unknown"),
            "configuration_url": f"{IXFIELD_DEVICE_URL}/{self._device_id}",
        } 