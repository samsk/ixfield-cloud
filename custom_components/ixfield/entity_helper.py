"""Common entity naming utilities for IXField integration."""

import logging

_LOGGER = logging.getLogger(__name__)


def create_unique_id(
    device_id: str, sensor_name: str, platform: str, is_target: bool = False
) -> str:
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


def get_operating_values(coordinator, device_id: str) -> list:
    """
    Get operating values (sensors) for a device from coordinator data.

    Args:
        coordinator: The IXField coordinator
        device_id: The device ID

    Returns:
        List of operating values (sensors) for the device
    """
    device_data = coordinator.data.get(device_id, {})
    if not device_data or "data" not in device_data:
        return []

    device = device_data.get("data", {}).get("device", {})
    operating_values = device.get("liveDeviceData", {}).get("operatingValues", [])
    
    return operating_values


def get_controls(coordinator, device_id: str) -> list:
    """
    Get controls for a device from coordinator data.

    Args:
        coordinator: The IXField coordinator
        device_id: The device ID

    Returns:
        List of controls for the device
    """
    device_data = coordinator.data.get(device_id, {})
    if not device_data or "data" not in device_data:
        return []

    device = device_data.get("data", {}).get("device", {})
    controls = device.get("liveDeviceData", {}).get("controls", [])
    
    return controls


def create_device_info(coordinator, device_id: str, device_name: str):
    """
    Create standardized device info dictionary for all IXField entities.
    
    Args:
        coordinator: The IXField coordinator
        device_id: The device ID
        device_name: The device name
        
    Returns:
        Device info dictionary
    """
    from .const import DOMAIN, IXFIELD_DEVICE_URL
    
    device_info = coordinator.get_device_info(device_id)
    company = device_info.get("company", {})
    thing_type = device_info.get("thing_type", {})
    
    return {
        "identifiers": {(DOMAIN, device_id)},
        "name": device_name,
        "manufacturer": company.get("name", "IXField"),
        "model": device_info.get("type", "Unknown"),
        "sw_version": device_info.get("controller", "Unknown"),
        "hw_version": thing_type.get("name", "Unknown"),
        "configuration_url": f"{IXFIELD_DEVICE_URL}/{device_id}",
    }


def setup_entity_common(
    entity,
    coordinator,
    device_id: str,
    device_name: str,
    sensor_name: str,
    platform: str,
    config: dict,
    unique_id_suffix: str = None,
):
    """
    Setup common entity attributes and properties.
    
    Args:
        entity: The entity instance
        coordinator: The IXField coordinator
        device_id: The device ID
        device_name: The device name
        sensor_name: The sensor/control name
        platform: The platform type
        config: The entity configuration
        unique_id_suffix: Optional suffix for unique ID
    """
    # Setup entity naming
    entity.setup_entity_naming(device_name, sensor_name, platform, config["name"])
    
    # Setup common attributes
    entity.set_common_attrs(config, platform)
    
    # Store common properties
    entity._device_id = device_id
    entity._device_name = device_name
    entity._sensor_name = sensor_name
    entity._config = config
    
    # Create unique ID
    unique_id = create_unique_id(device_id, sensor_name, platform)
    if unique_id_suffix:
        unique_id = f"{unique_id}_{unique_id_suffix}"
    entity._attr_unique_id = unique_id


class EntityNamingMixin:
    """Mixin class to provide standardized entity naming for IXField entities."""

    def setup_entity_naming(
        self,
        device_name: str,
        sensor_name: str,
        platform: str,
        friendly_name: str,
        is_target: bool = False,
    ):
        """
        Setup entity naming using the new Home Assistant entity naming convention.

        This method implements the new Home Assistant entity naming standard:
        - Sets has_entity_name = True
        - Stores the friendly name for the name property
        - The name property will return only the data point name
        - Home Assistant automatically generates friendly_name by combining entity name with device name

        Args:
            device_name: The device name
            sensor_name: The sensor/control name from API
            platform: The platform type
            friendly_name: Human-friendly name for UI display (data point name only)
            is_target: Whether this is a target entity
        """
        # Set has_entity_name to True for new Home Assistant naming convention
        self._attr_has_entity_name = True
        self._attr_name = friendly_name

        # Store additional info for backward compatibility if needed
        self._device_name = device_name
        self._sensor_name = sensor_name
        self._platform = platform
        self._is_target = is_target


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
            if platform == "select":
                # For select entities, extract options from options.values array
                # Each item has 'value' and 'label' attributes
                values = config["options"].get("values", [])
                if values:
                    # Extract the 'value' from each option for Home Assistant select
                    self._attr_options = [
                        item.get("value", "") for item in values if item.get("value")
                    ]
                    _LOGGER.debug(
                        f"Extracted select options from values: {self._attr_options}"
                    )
                else:
                    # Fallback to old format if values not found
                    options = config["options"].get("options", [])
                    self._attr_options = options
                    _LOGGER.debug(
                        f"Using fallback select options: {self._attr_options}"
                    )
            elif platform == "sensor":
                # For sensors with options, set enum device class
                values = config["options"].get("values", [])
                options = config["options"].get("options", [])
                if values or options:
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

    def get_sensor_value(
        self, sensor_name: str, value_key: str = "value", fallback_value=None
    ):
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

    def get_control_value(
        self, control_name: str, value_key: str = "value", fallback_value=None
    ):
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


class BaseIxfieldEntity:
    """Base class for IXField entities with common functionality."""
    
    def __init__(
        self,
        coordinator,
        device_id: str,
        device_name: str,
        sensor_name: str,
        platform: str,
        config: dict,
        unique_id_suffix: str = None,
    ):
        """
        Initialize the base entity with common properties.
        
        Args:
            coordinator: The IXField coordinator
            device_id: The device ID
            device_name: The device name
            sensor_name: The sensor/control name
            platform: The platform type
            config: The entity configuration
            unique_id_suffix: Optional suffix for unique ID
        """
        # Setup entity naming
        self.setup_entity_naming(device_name, sensor_name, platform, config["name"])
        
        # Setup common attributes
        self.set_common_attrs(config, platform)
        
        # Store common properties
        self._device_id = device_id
        self._device_name = device_name
        self._sensor_name = sensor_name
        self._config = config
        
        # Create unique ID
        unique_id = create_unique_id(device_id, sensor_name, platform)
        if unique_id_suffix:
            unique_id = f"{unique_id}_{unique_id_suffix}"
        self._attr_unique_id = unique_id
    
    @property
    def device_info(self):
        """Return device info."""
        return create_device_info(self.coordinator, self._device_id, self._device_name)
