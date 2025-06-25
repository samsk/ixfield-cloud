"""Common entity naming utilities for IXField integration."""

def create_entity_name(device_name: str, sensor_name: str, platform: str, is_target: bool = False) -> str:
    """
    Create a standardized entity name with device prefix.
    
    Args:
        device_name: The device name (e.g., "pool", "pool1")
        sensor_name: The sensor/control name from API
        platform: The platform type ("sensor", "climate", "select", "number", "switch")
        is_target: Whether this is a target entity (for number platform)
    
    Returns:
        Entity name with device prefix (e.g., "pool_temperature", "pool1_ph_select")
    """
    # Base entity name with device prefix
    entity_name = f"{device_name}_{sensor_name}"
    
    # Add platform-specific suffix
    if platform == "climate":
        entity_name = f"{entity_name}_climate"
    elif platform == "select":
        entity_name = f"{entity_name}_select"
    elif platform == "number":
        entity_name = f"{entity_name}_number"
        if is_target:
            entity_name = f"{entity_name}_target"
    elif platform == "switch":
        entity_name = f"{entity_name}_switch"
    # sensor platform doesn't need suffix
    
    return entity_name


def create_unique_id(device_id: str, sensor_name: str, platform: str, is_target: bool = False) -> str:
    """
    Create a standardized unique ID for entities.
    
    Args:
        device_id: The device ID
        sensor_name: The sensor/control name from API
        platform: The platform type
        is_target: Whether this is a target entity
    
    Returns:
        Unique ID string
    """
    unique_id = f"{device_id}_{sensor_name}"
    
    # Add target suffix for target entities
    if is_target:
        unique_id = f"{unique_id}_target"
    
    return unique_id


class EntityNamingMixin:
    """Mixin class to provide standardized entity naming for IXField entities."""
    
    def setup_entity_naming(self, device_name: str, sensor_name: str, platform: str, friendly_name: str, is_target: bool = False):
        """
        Setup entity naming.
        
        Args:
            device_name: The device name
            sensor_name: The sensor/control name from API
            platform: The platform type
            friendly_name: Human-friendly name for UI display
            is_target: Whether this is a target entity
        """
        # Create entity name with device prefix for entity_id generation
        entity_name = create_entity_name(device_name, sensor_name, platform, is_target)
        self._attr_name = entity_name
        
        # Store human-friendly name for UI display
        self._friendly_name = friendly_name
        
        # Set has_entity_name to False so we can control the display name
        self._attr_has_entity_name = False


class EntityCommonAttrsMixin:
    """Mixin to set common Home Assistant entity attributes from config/meta."""
    def set_common_attrs(self, config: dict, platform: str = None):
        # Device class - don't override for climate entities
        if "device_class" in config and platform != "climate":
            self._attr_device_class = config["device_class"]
        # Unit of measurement
        if "unit" in config:
            self._attr_native_unit_of_measurement = config["unit"]
        
        # Handle options based on platform
        if "options" in config and config["options"]:
            options = config["options"].get("options", [])
            if platform == "select":
                # For select entities, set the options
                self._attr_options = options
            elif platform == "sensor" and options:
                # For sensors with options, set enum device class
                self._attr_device_class = "enum"
        
        # Min/max/step/mode (for number)
        if "min_value" in config:
            self._attr_native_min_value = config["min_value"]
        if "max_value" in config:
            self._attr_native_max_value = config["max_value"]
        if "step" in config:
            self._attr_native_step = config["step"]
        if "mode" in config:
            self._attr_mode = config["mode"]


class EntityValueMixin:
    """Mixin to handle common value property logic for IXField entities."""
    
    def get_sensor_value(self, sensor_name: str, value_key: str = "value", fallback_value=None):
        """
        Get sensor value from coordinator data.
        
        Args:
            sensor_name: The sensor name to look for
            value_key: The key to get from sensor data ("value", "desiredValue", etc.)
            fallback_value: Value to return if sensor not found
            
        Returns:
            The sensor value or fallback_value
        """
        device_data = self.coordinator.data.get(self._device_id, {})
        if not device_data or "data" not in device_data:
            return fallback_value
        
        device = device_data.get("data", {}).get("device", {})
        operating_values = device.get("liveDeviceData", {}).get("operatingValues", [])
        
        for sensor in operating_values:
            if sensor.get("name") == sensor_name:
                value = sensor.get(value_key)
                # Try to convert to float if numeric
                if value is not None:
                    try:
                        return float(value)
                    except (TypeError, ValueError):
                        return value
                return value
        
        return fallback_value
    
    def get_control_value(self, control_name: str, value_key: str = "value", fallback_value=None):
        """
        Get control value from coordinator data.
        
        Args:
            control_name: The control name to look for
            value_key: The key to get from control data
            fallback_value: Value to return if control not found
            
        Returns:
            The control value or fallback_value
        """
        device_data = self.coordinator.data.get(self._device_id, {})
        if not device_data or "data" not in device_data:
            return fallback_value
        
        device = device_data.get("data", {}).get("device", {})
        controls = device.get("liveDeviceData", {}).get("controls", [])
        
        for control in controls:
            if control.get("name") == control_name:
                value = control.get(value_key)
                return value
        
        return fallback_value 