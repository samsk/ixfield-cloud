import logging
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, IXFIELD_DEVICE_URL
from .device_info_sensor import create_device_info_sensors
from .entity_helper import (
    EntityCommonAttrsMixin,
    EntityNamingMixin,
    EntityValueMixin,
    create_unique_id,
    get_operating_values,
)
from .sensor_config import apply_sensor_overrides, should_skip_sensor_for_platform

_LOGGER = logging.getLogger(__name__)

# Comprehensive mapping from API units/sensor types to HA units and device classes
SENSOR_MAPPINGS = {
    # API units (from options.unit)
    "TEMP_CELSIUS": (UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
    "TEMP_FAHRENHEIT": (UnitOfTemperature.FAHRENHEIT, SensorDeviceClass.TEMPERATURE),
    "LITER": ("L", SensorDeviceClass.VOLUME),
    "PERCENT": ("%", None),
    "PH": ("pH", None),
    "ORP": ("mV", None),
    "SALINITY": ("%", None),
    "TIME": ("min", None),
    "DISTANCE": ("m", None),
    "PRESSURE": ("bar", SensorDeviceClass.PRESSURE),
    "FLOW": ("L/min", None),
    "POWER": ("W", SensorDeviceClass.POWER),
    "ENERGY": ("kWh", SensorDeviceClass.ENERGY),
    "CURRENT": ("A", SensorDeviceClass.CURRENT),
    "VOLTAGE": ("V", SensorDeviceClass.VOLTAGE),
    "FREQUENCY": ("Hz", SensorDeviceClass.FREQUENCY),
    "RPM": ("rpm", None),
    "COUNT": ("", None),
    "BOOLEAN": (None, None),
    "STRING": (None, None),
    # Sensor types (fallback when unit is not specified)
    "VOLUME": ("L", SensorDeviceClass.VOLUME),
}


def generate_human_readable_name(sensor_name):
    """Generate a human readable name from sensor name."""
    # Remove common suffixes
    name = sensor_name.replace("WithSettings", "")
    name = name.replace("target", "")

    # Convert camelCase to spaces
    import re

    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)

    # Capitalize first letter of each word
    name = name.title()

    return name


def get_sensor_config(sensor_name, sensor_data):
    """Get sensor configuration from sensor data with overrides applied."""
    # Apply any overrides to the sensor data first
    modified_sensor_data = apply_sensor_overrides(sensor_name, sensor_data)

    # Start with default configuration from modified sensor data
    sensor_type = modified_sensor_data.get("type", "STRING")
    options = modified_sensor_data.get("options", {})

    # Get the unit from options and map it to proper HA unit and device class
    api_unit = options.get("unit")

    # Get unit and device class from mapping, fallback to default if not found
    if api_unit in SENSOR_MAPPINGS:
        unit, device_class = SENSOR_MAPPINGS[api_unit]
    else:
        # Fallback to default mapping based on sensor type
        default_config = SENSOR_MAPPINGS.get(sensor_type, SENSOR_MAPPINGS["STRING"])
        unit = default_config[0]
        device_class = default_config[1]

    config = {
        "_name": sensor_name,
        "name": modified_sensor_data.get("label")
        or generate_human_readable_name(sensor_name),
        "unit": unit,
        "device_class": device_class,
        "settable": modified_sensor_data.get("settable", False),
        "show_desired": modified_sensor_data.get("showDesired", False),
        "min_value": options.get("min"),
        "max_value": options.get("max"),
        "step": options.get("step", 1),
        "value": modified_sensor_data.get("value"),
        "desired_value": modified_sensor_data.get("desiredValue"),
        "show_desired_as_sensor": modified_sensor_data.get("show_desired_as_sensor", False),
        "options": options,  # Include the full options object for select entities
    }

    return config


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up IXField sensors from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    device_ids = coordinator.device_ids

    sensors = []
    created_unique_ids = set()
    all_sensor_names = []

    for device_id in device_ids:
        device_info = coordinator.get_device_info(device_id)
        device_name = coordinator.get_device_name(device_id)
        _LOGGER.info(
            f"Device info for {device_id}: {device_name} - {device_info.get('type', 'Unknown')}"
        )

        operating_values = get_operating_values(coordinator, device_id)

        _LOGGER.debug(
            f"Processing {len(operating_values)} operating values for device {device_id}"
        )

        # Add device information sensors only if enabled
        if coordinator.should_extract_device_info_sensors():
            sensors.extend(
                create_device_info_sensors(
                    coordinator, device_id, device_name, device_info
                )
            )
            _LOGGER.debug(f"Created device info sensors for device {device_id}")
        else:
            _LOGGER.debug(
                f"Skipping device info sensors for device {device_id} - disabled in configuration"
            )

        # Process operating values (existing sensors)
        for sensor_data in operating_values:
            sensor_name = sensor_data.get("name")
            if not sensor_name:
                continue

            config = get_sensor_config(sensor_name, sensor_data)

            # Use global configuration to determine if this sensor should be skipped
            if should_skip_sensor_for_platform(sensor_name, sensor_data, "sensor"):
                _LOGGER.debug(
                    f"Skipping sensor {sensor_name} - will be handled by other platforms"
                )
                continue

            # Create main sensor - for all non-settable sensors
            main_sensor = IxfieldSensor(
                coordinator, device_id, device_name, sensor_name, config
            )
            if main_sensor.unique_id not in created_unique_ids:
                sensors.append(main_sensor)
                created_unique_ids.add(main_sensor.unique_id)
                all_sensor_names.append(main_sensor.name)
                _LOGGER.debug(f"Created sensor: {main_sensor.name}")

            # Create target sensor if this sensor has showDesired=True
            if config.get("show_desired_as_sensor", False):
                target_sensor = IxfieldTargetSensor(
                    coordinator, device_id, device_name, sensor_name, config
                )
                if target_sensor.unique_id not in created_unique_ids:
                    sensors.append(target_sensor)
                    created_unique_ids.add(target_sensor.unique_id)
                    all_sensor_names.append(target_sensor.name)
                    _LOGGER.debug(f"Created target sensor: {target_sensor.name}")

    _LOGGER.info(f"Created {len(sensors)} sensors: {all_sensor_names}")
    async_add_entities(sensors)


class IxfieldSensor(
    CoordinatorEntity,
    SensorEntity,
    EntityNamingMixin,
    EntityCommonAttrsMixin,
    EntityValueMixin,
):
    def __init__(
        self, coordinator, device_id, device_name, value, config, is_target=False
    ):
        self.setup_entity_naming(
            device_name, value, "sensor", config["name"], is_target
        )
        self.set_common_attrs(config, "sensor")
        super().__init__(coordinator)

        self._device_id = device_id
        self._device_name = device_name
        self._value_name = value
        self._label = config["name"]
        self._value_key = "value"
        self._initial_value = config.get("value")  # Store the initial value from config
        self._attr_unique_id = create_unique_id(device_id, value, "sensor", is_target)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    @property
    def native_value(self):
        # Try to get value from coordinator data first
        value = self.get_sensor_value(self._value_name, "value")
        if value is not None:
            return value

        # Fallback to initial value from config
        if self._initial_value is not None:
            try:
                return (
                    float(self._initial_value)
                    if self._initial_value is not None
                    else None
                )
            except (TypeError, ValueError):
                return self._initial_value

        return None

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug(f"Coordinator update for {self._value_name}")
        super()._handle_coordinator_update()
        # Force a state update
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

    async def async_set_native_value(self, value):
        """Set the value."""
        api = self.coordinator.api
        success = await api.async_set_control(
            self._device_id, self._value_name, str(value)
        )
        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error(f"Failed to set {self._attr_name} to {value}")


class IxfieldTargetSensor(
    CoordinatorEntity,
    SensorEntity,
    EntityNamingMixin,
    EntityCommonAttrsMixin,
    EntityValueMixin,
):
    """Representation of an IXField target sensor that shows the desired/target value."""

    def __init__(
        self, coordinator, device_id, device_name, sensor_name, config
    ):
        # Create a target-specific config
        target_config = config.copy()
        target_config["name"] = f"{config['name']} Target"
        
        self.setup_entity_naming(
            device_name, sensor_name, "sensor", target_config["name"], is_target=True
        )
        self.set_common_attrs(target_config, "sensor")
        super().__init__(coordinator)

        self._device_id = device_id
        self._device_name = device_name
        self._value_name = sensor_name
        self._label = target_config["name"]
        self._value_key = "desiredValue"  # Use desiredValue instead of value
        self._initial_value = config.get("desired_value")  # Store the initial desired value
        self._attr_unique_id = create_unique_id(device_id, sensor_name, "sensor", is_target=True)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    @property
    def native_value(self):
        # Try to get desired value from coordinator data first
        value = self.get_sensor_value(self._value_name, "desiredValue")
        if value is not None:
            return value

        # Fallback to initial desired value from config
        if self._initial_value is not None:
            try:
                return (
                    float(self._initial_value)
                    if self._initial_value is not None
                    else None
                )
            except (TypeError, ValueError):
                return self._initial_value

        return None

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug(f"Coordinator update for target sensor {self._value_name}")
        super()._handle_coordinator_update()
        # Force a state update
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
