"""Global sensor configuration for IXField integration."""
import logging

_LOGGER = logging.getLogger(__name__)

# Override configurations for sensors
# This allows overriding any sensor attribute from the API
SENSOR_OVERRIDES = {
    # Make specific sensors non-settable (override API settable=True)
    "AgentA": {
        "settable": False,  # Force this sensor to be non-settable
        "reason": "Agent A should be read-only",
    },
    "remainingAgentA": {
        "settable": False,  # Force this sensor to be non-settable
        "reason": "Remaining Agent A should be read-only",
    },
    "targetORP": {
        "settable": False,
        "show_desired_as_sensor": True,
        "reason": "Target ORP should be settable only via WEB",
    },
    "targetpH": {
        "settable": False,
        "show_desired_as_sensor": True,
        "reason": "Target PH should be settable only via WEB",
    },
    # Example of overriding other sensor properties:
    # "poolTempWithSettings": {
    #     "name": "Pool Temperature",  # Override the display name
    #     "unit": "°C",  # Override the unit
    #     "device_class": "temperature",  # Override device class
    #     "min_value": 10,  # Override min value
    #     "max_value": 40,  # Override max value
    #     "step": 0.5,  # Override step value
    #     "settable": True,  # Force settable
    #     "reason": "Pool temperature should be settable with custom range",
    #     "show_desired_as_sensor": True,  # Show desired value as sensor
    # },
    # You can add more overrides here:
    # "sensorName": {
    #     "name": "Custom Name",  # Override display name
    #     "unit": "custom_unit",  # Override unit
    #     "device_class": "device_class",  # Override device class
    #     "min_value": 0,  # Override min value
    #     "max_value": 100,  # Override max value
    #     "step": 1,  # Override step value
    #     "settable": True/False,  # Override settable status
    #     "reason": "Explanation of why this override exists"
    # }
}


def is_sensor_settable(sensor_name, sensor_data):
    """
    Determine if a sensor should be settable based on API data and overrides.

    Args:
        sensor_name: The name of the sensor
        sensor_data: The sensor data from the API

    Returns:
        bool: True if the sensor should be settable, False otherwise
    """
    # Check if there's an override for this sensor
    if sensor_name in SENSOR_OVERRIDES:
        override = SENSOR_OVERRIDES[sensor_name]
        if "settable" in override:
            api_settable = sensor_data.get("settable", False)
            override_settable = override["settable"]
            reason = override.get("reason", "No reason provided")

            if api_settable != override_settable:
                _LOGGER.info(
                    f"Override applied to {sensor_name}: API settable={api_settable}, Override settable={override_settable}, Reason: {reason}"
                )

            return override["settable"]

    # If no override, use the API's settable attribute
    return sensor_data.get("settable", False)


def get_sensor_override(sensor_name):
    """
    Get the override configuration for a sensor.

    Args:
        sensor_name: The name of the sensor

    Returns:
        dict: The override configuration or None if no override exists
    """
    return SENSOR_OVERRIDES.get(sensor_name)


def apply_sensor_overrides(sensor_name, sensor_data):
    """
    Apply any overrides to the sensor data.

    Args:
        sensor_name: The name of the sensor
        sensor_data: The sensor data from the API

    Returns:
        dict: The sensor data with overrides applied
    """
    if sensor_name not in SENSOR_OVERRIDES:
        return sensor_data

    override = SENSOR_OVERRIDES[sensor_name]
    reason = override.get("reason", "No reason provided")

    # Create a copy of the sensor data to avoid modifying the original
    modified_data = sensor_data.copy()

    # Apply overrides
    for key, value in override.items():
        if key != "reason":  # Skip the reason field
            original_value = sensor_data.get(key)
            if original_value != value:
                _LOGGER.info(
                    f"Override applied to {sensor_name}.{key}: API={original_value}, Override={value}, Reason: {reason}"
                )
                modified_data[key] = value

    return modified_data


def should_skip_sensor_for_platform(sensor_name, sensor_data, platform):
    """
    Determine if a sensor should be skipped for a specific platform.

    Args:
        sensor_name: The name of the sensor
        sensor_data: The sensor data from the API
        platform: The platform name ("sensor", "number", "select")

    Returns:
        bool: True if the sensor should be skipped for this platform
    """
    # Apply overrides before checking
    modified_data = apply_sensor_overrides(sensor_name, sensor_data)

    is_settable = is_sensor_settable(sensor_name, modified_data)
    is_enum = modified_data.get("type") == "ENUM"
    is_desired = modified_data.get("showDesired", False)

    if platform == "sensor":
        # Skip settable sensors (except desired sensors, but enum sensors should go to select platform)
        # Also skip settable sensors that will be handled by number platform
        return is_settable and (not is_desired or is_enum)

    elif platform == "number":
        # Skip non-settable sensors and enum sensors (enum sensors should go to select platform)
        return not is_settable or is_enum

    elif platform == "select":
        # Skip non-settable sensors and non-enum sensors
        return not is_settable or not is_enum

    return False
