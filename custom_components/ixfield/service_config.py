"""Service configuration for IXField integration."""
import logging
from typing import Dict, List, Optional, Any

_LOGGER = logging.getLogger(__name__)

# Default control mappings - these can be overridden by user configuration
DEFAULT_CONTROL_MAPPINGS = {
    "circulation_pump": {
        "sensor_patterns": ["filtrationState", "pumpState", "circulationState"],
        "description": "Circulation pump control",
        "type": "boolean"
    },
    "lighting": {
        "sensor_patterns": ["lightsState", "lightingState", "lightState"],
        "description": "Lighting control",
        "type": "boolean"
    },
    "counterflow": {
        "sensor_patterns": ["jetstreamState", "counterflowState", "jetsState"],
        "description": "Counterflow/jet stream control",
        "type": "boolean"
    },
    "target_temperature": {
        "sensor_patterns": ["*WithSettings", "targetTemp", "setpointTemp"],
        "description": "Target temperature setting",
        "type": "temperature",
        "unit": "°C"
    },
    "target_orp": {
        "sensor_patterns": ["targetORP", "setpointORP", "orpSetpoint"],
        "description": "Target ORP setting",
        "type": "number",
        "unit": "mV"
    },
    "target_ph": {
        "sensor_patterns": ["targetpH", "setpointpH", "phSetpoint"],
        "description": "Target pH setting",
        "type": "number",
        "unit": "pH"
    },
    "agent_volume": {
        "sensor_patterns": ["remainingAgentA", "agentVolume", "agentLevel"],
        "description": "Agent volume/level",
        "type": "number",
        "unit": "L"
    },
    "heater_mode": {
        "sensor_patterns": ["targetHeaterMode", "heaterMode", "heatingMode"],
        "description": "Heater mode setting",
        "type": "enum"
    }
}

# User-defined control mappings (can be set via configuration)
USER_CONTROL_MAPPINGS: Dict[str, Dict[str, Any]] = {}

def set_user_control_mappings(mappings: Dict[str, Dict[str, Any]]) -> None:
    """Set user-defined control mappings."""
    global USER_CONTROL_MAPPINGS
    USER_CONTROL_MAPPINGS = mappings
    _LOGGER.info(f"User control mappings updated: {list(mappings.keys())}")

def get_control_mappings() -> Dict[str, Dict[str, Any]]:
    """Get combined control mappings (default + user)."""
    combined = DEFAULT_CONTROL_MAPPINGS.copy()
    combined.update(USER_CONTROL_MAPPINGS)
    return combined

def find_matching_sensor(control_name: str, available_sensors: List[Dict[str, Any]]) -> Optional[str]:
    """
    Find the best matching sensor for a control name.
    
    Args:
        control_name: The control name to find a sensor for
        available_sensors: List of available sensors from the device
        
    Returns:
        The sensor name if found, None otherwise
    """
    mappings = get_control_mappings()
    
    if control_name not in mappings:
        _LOGGER.warning(f"No mapping found for control: {control_name}")
        return None
    
    control_config = mappings[control_name]
    sensor_patterns = control_config.get("sensor_patterns", [])
    
    # Create a list of available sensor names
    sensor_names = [sensor.get("name", "") for sensor in available_sensors if sensor.get("name")]
    
    # Try exact matches first
    for pattern in sensor_patterns:
        if pattern in sensor_names:
            _LOGGER.debug(f"Found exact match for {control_name}: {pattern}")
            return pattern
    
    # Try pattern matching (for wildcard patterns)
    for pattern in sensor_patterns:
        if "*" in pattern:
            # Convert wildcard pattern to regex-like matching
            pattern_parts = pattern.split("*")
            for sensor_name in sensor_names:
                if (len(pattern_parts) == 2 and 
                    sensor_name.startswith(pattern_parts[0]) and 
                    sensor_name.endswith(pattern_parts[1])):
                    _LOGGER.debug(f"Found pattern match for {control_name}: {sensor_name} matches {pattern}")
                    return sensor_name
    
    # Try fuzzy matching (case-insensitive)
    control_lower = control_name.lower()
    for sensor_name in sensor_names:
        sensor_lower = sensor_name.lower()
        if control_lower in sensor_lower or sensor_lower in control_lower:
            _LOGGER.debug(f"Found fuzzy match for {control_name}: {sensor_name}")
            return sensor_name
    
    _LOGGER.warning(f"No matching sensor found for control: {control_name}")
    return None

def get_available_controls(available_sensors: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Get available controls based on device sensors.
    
    Args:
        available_sensors: List of available sensors from the device
        
    Returns:
        Dictionary of available controls with their configurations
    """
    mappings = get_control_mappings()
    available_controls = {}
    
    for control_name, control_config in mappings.items():
        matching_sensor = find_matching_sensor(control_name, available_sensors)
        if matching_sensor:
            # Find the actual sensor data
            sensor_data = next((s for s in available_sensors if s.get("name") == matching_sensor), None)
            if sensor_data:
                available_controls[control_name] = {
                    "sensor_name": matching_sensor,
                    "sensor_data": sensor_data,
                    "config": control_config
                }
    
    return available_controls

def validate_control_value(control_name: str, value: Any) -> tuple[bool, str]:
    """
    Validate a control value based on its type.
    
    Args:
        control_name: The control name
        value: The value to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    mappings = get_control_mappings()
    
    if control_name not in mappings:
        return False, f"Unknown control: {control_name}"
    
    control_config = mappings[control_name]
    control_type = control_config.get("type", "string")
    
    if control_type == "boolean":
        if isinstance(value, bool):
            return True, ""
        if isinstance(value, str):
            if value.lower() in ["true", "false", "1", "0", "on", "off"]:
                return True, ""
        return False, f"Boolean control requires boolean or string value, got {type(value)}"
    
    elif control_type == "temperature":
        try:
            float_val = float(value)
            # Reasonable temperature range
            if -50 <= float_val <= 100:
                return True, ""
            return False, f"Temperature value {float_val} is outside reasonable range (-50 to 100)"
        except (ValueError, TypeError):
            return False, f"Temperature control requires numeric value, got {type(value)}"
    
    elif control_type == "number":
        try:
            float_val = float(value)
            return True, ""
        except (ValueError, TypeError):
            return False, f"Number control requires numeric value, got {type(value)}"
    
    elif control_type == "enum":
        # For enum types, we'll validate against available options if sensor data is provided
        return True, ""
    
    # Default to string validation
    return True, ""

def format_control_value(control_name: str, value: Any) -> str:
    """
    Format a control value for the API.
    
    Args:
        control_name: The control name
        value: The value to format
        
    Returns:
        Formatted string value for the API
    """
    mappings = get_control_mappings()
    
    if control_name not in mappings:
        return str(value)
    
    control_config = mappings[control_name]
    control_type = control_config.get("type", "string")
    
    if control_type == "boolean":
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, str):
            if value.lower() in ["true", "1", "on"]:
                return "true"
            if value.lower() in ["false", "0", "off"]:
                return "false"
        return str(value)
    
    # For other types, convert to string
    return str(value) 