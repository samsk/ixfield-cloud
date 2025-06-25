from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from .const import DOMAIN, IXFIELD_DEVICE_URL
import logging

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

# Override configurations - can override name, unit, device_class, and settable properties
SENSOR_MAP = {
    # Example overrides for main sensors:
    # "poolTempWithSettings": {
    #     "name": "Pool Temperature",
    #     "unit": UnitOfTemperature.CELSIUS,
    #     "device_class": SensorDeviceClass.TEMPERATURE,
    #     "settable": True,
    #     "min_value": 10,
    #     "max_value": 40,
    #     "step": 0.5
    # },
    # "heaterMode": {
    #     "name": "Heater Status",
    #     "unit": None,
    #     "device_class": None
    # },
    # "filtrationState": {
    #     "name": "Filtration System",
    #     "unit": None,
    #     "device_class": None
    # },
    
    # Example overrides for target sensors (use .desired suffix):
    # "poolTempWithSettings.desired": {
    #     "name": "Target Pool Temperature",
    #     "settable": True,
    #     "min_value": 10,
    #     "max_value": 40,
    #     "step": 0.5
    # },
    
    # You can override any sensor by its exact name from the API
    # "sensorNameFromAPI": {
    #     "name": "Your Custom Name",
    #     "unit": "°C",  # or UnitOfTemperature.CELSIUS
    #     "device_class": SensorDeviceClass.TEMPERATURE,
    #     "settable": True,  # Make it settable
    #     "min_value": 0,
    #     "max_value": 100,
    #     "step": 1
    # }
}

def generate_human_readable_name(sensor_name):
    """Generate a human readable name from sensor name."""
    # Remove common suffixes
    name = sensor_name.replace("WithSettings", "")
    name = name.replace("target", "")
    
    # Convert camelCase to spaces
    import re
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
    
    # Capitalize first letter of each word
    name = name.title()
    
    return name

def get_sensor_config(sensor_name, sensor_data):
    """Get sensor configuration with overrides from SENSOR_MAP."""
    # Start with default configuration from sensor data
    sensor_type = sensor_data.get("type", "STRING")
    options = sensor_data.get("options", {})
    
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
        "name": sensor_data.get("label") or generate_human_readable_name(sensor_name),
        "unit": unit,
        "device_class": device_class,
        "settable": sensor_data.get("settable", False),
        "show_desired": sensor_data.get("showDesired", False),
        "min_value": options.get("min"),
        "max_value": options.get("max"),
        "step": options.get("step", 1),
        "value": sensor_data.get("value"),
        "desired_value": sensor_data.get("desiredValue")
    }
    
    # Apply overrides from SENSOR_MAP
    if sensor_name in SENSOR_MAP:
        override = SENSOR_MAP[sensor_name]
        config.update({k: v for k, v in override.items() if v is not None})
    
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
        _LOGGER.info(f"Device info for {device_id}: {device_name} - {device_info.get('type', 'Unknown')}")
        
        device_data = coordinator.data.get(device_id, {})
        device = device_data.get("data", {}).get("device", {})
        operating_values = device.get("liveDeviceData", {}).get("operatingValues", [])
        
        _LOGGER.debug(f"Processing {len(operating_values)} operating values for device {device_id}")
        
        for sensor_data in operating_values:
            sensor_name = sensor_data.get("name")
            if not sensor_name:
                continue
                
            config = get_sensor_config(sensor_name, sensor_data)
            all_sensor_names.append(sensor_name)
            
            # Create main sensor (always shows current value, never settable)
            main_sensor = IxfieldSensor(
                coordinator, device_id, device_name, sensor_name, config
            )
            
            if main_sensor.unique_id not in created_unique_ids:
                sensors.append(main_sensor)
                created_unique_ids.add(main_sensor.unique_id)
                _LOGGER.debug(f"Created main sensor: {main_sensor.name} (regular sensor, settable: {config['settable']}, show_desired: {config['show_desired']})")
                _LOGGER.debug(f"  - Unique ID: {main_sensor.unique_id}")
                _LOGGER.debug(f"  - Sensor name: {sensor_name}")
                _LOGGER.debug(f"  - Config: {config}")
            else:
                _LOGGER.warning(f"Duplicate sensor found: {main_sensor.name} with unique_id: {main_sensor.unique_id}")
            
            # Create target sensor if needed (settable for desired values)
            if config["show_desired"] and config["desired_value"] is not None:
                target_config = config.copy()
                target_config["name"] = f"Target {config['name']}"
                target_config["value"] = config["desired_value"]
                
                # Check for specific override for target sensor
                target_key = f"{sensor_name}.desired"
                if target_key in SENSOR_MAP:
                    target_config.update({k: v for k, v in SENSOR_MAP[target_key].items() if v is not None})
                
                # Target sensors are always settable (for setting desired values)
                target_sensor = IxfieldSettableSensor(
                    coordinator, device_id, device_name, sensor_name, target_config, is_target=True
                )
                
                if target_sensor.unique_id not in created_unique_ids:
                    sensors.append(target_sensor)
                    created_unique_ids.add(target_sensor.unique_id)
                    _LOGGER.debug(f"Created target sensor: {target_sensor.name} (settable for desired value)")
    
    _LOGGER.info(f"Created {len(sensors)} sensors")
    _LOGGER.debug(f"All sensor names: {all_sensor_names}")
    _LOGGER.debug(f"Sensors being added to Home Assistant: {[s.name for s in sensors]}")
    async_add_entities(sensors)

class IxfieldSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, device_id, device_name, value, meta, is_target=False):
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_name = device_name
        self._value_name = value
        self._label = meta["name"]
        self._unit = meta["unit"]
        self._value_key = "value"
        self._initial_value = meta.get("value")  # Store the initial value from config
        
        # Use human-friendly name from config instead of raw sensor name
        if is_target:
            # For target sensors, use the target name from config
            self._attr_name = meta["name"]  # This should already be "Target {name}"
        else:
            # For main sensors, use the human-friendly name from config
            self._attr_name = meta["name"]
        
        self._attr_unique_id = f"{device_id}_{self._value_name}_target" if is_target else f"{device_id}_{self._value_name}"
        self._device_class = meta["device_class"]

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def native_value(self):
        device_data = self.coordinator.data.get(self._device_id, {})
        _LOGGER.debug(f"Getting native_value for {self._value_name} (regular sensor) - device_id: {self._device_id}")
        _LOGGER.debug(f"Coordinator data keys: {list(self.coordinator.data.keys())}")
        _LOGGER.debug(f"Device data for {self._device_id}: {device_data}")
        
        # The API returns {"data": {"device": {...}}}, so we need to access it properly
        device = device_data.get("data", {}).get("device", {})
        operating_values = device.get("liveDeviceData", {}).get("operatingValues", [])
        
        _LOGGER.debug(f"Available operating values: {[v.get('name') for v in operating_values]}")
        _LOGGER.debug(f"Looking for sensor: {self._value_name}")

        for sensor in operating_values:
            if sensor.get("name") == self._value_name:
                result = sensor.get("value")  # Always use "value" for regular sensors
                _LOGGER.debug(f"Found value for {self._value_name}: {result}")
                _LOGGER.debug(f"Full sensor data: {sensor}")
                try:
                    return float(result) if result is not None else None
                except (TypeError, ValueError):
                    return result  # Return as string if not numeric
        
        # If not found in operating values, try to use initial value from config
        if self._initial_value is not None:
            _LOGGER.debug(f"Using initial value for {self._value_name}: {self._initial_value}")
            try:
                return float(self._initial_value) if self._initial_value is not None else None
            except (TypeError, ValueError):
                return self._initial_value  # Return as string if not numeric
        
        _LOGGER.warning(f"No value found for {self._value_name}")
        return None

    @property
    def state(self):
        """Return the state of the sensor."""
        _LOGGER.debug(f"Getting state for {self._value_name}")
        return self.native_value

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug(f"Coordinator update for {self._value_name}")
        super()._handle_coordinator_update()
        # Force a state update
        self.async_write_ha_state()

    @property
    def native_unit_of_measurement(self):
        return self._unit

    @property
    def device_class(self):
        return self._device_class

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
        success = await api.async_set_control(self._device_id, self._value_name, str(value))
        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error(f"Failed to set {self._attr_name} to {value}")

class IxfieldSettableSensor(IxfieldSensor, NumberEntity):
    """Representation of a settable IXField sensor."""

    def __init__(self, coordinator, device_id, device_name, sensor_name, config, is_target=False):
        # Initialize the base sensor class
        super().__init__(coordinator, device_id, device_name, sensor_name, config, is_target)
        self._is_target = is_target
        
        # Add settable-specific properties
        self._min_value = config.get("min_value", 0)
        self._max_value = config.get("max_value", 100)
        self._step = config.get("step", 1)
        
        _LOGGER.debug(f"Initialized IxfieldSettableSensor: {self.name}, is_target: {is_target}")

    @property
    def native_value(self):
        """Return the state of the sensor."""
        device_data = self.coordinator.data.get(self._device_id)
        if not device_data or "data" not in device_data:
            _LOGGER.debug(f"No device data for {self.name}")
            return None
        
        live_data = device_data.get("data", {}).get("device", {}).get("liveDeviceData", {})
        if not live_data:
            _LOGGER.debug(f"No live data for {self.name}")
            return None
        
        operating_values = live_data.get("operatingValues", [])
        if not operating_values:
            _LOGGER.debug(f"No operating values for {self.name}")
            return None
        
        # Find the sensor by name
        for sensor in operating_values:
            if sensor.get("name") == self._value_name:
                # For target sensors, use desiredValue; for regular settable sensors, use value
                if self._is_target:
                    value = sensor.get("desiredValue")
                    _LOGGER.debug(f"Target sensor {self.name} using desiredValue: {value}")
                else:
                    value = sensor.get("value")
                    _LOGGER.debug(f"Regular settable sensor {self.name} using value: {value}")
                return value
        
        _LOGGER.debug(f"Sensor {self._value_name} not found in operating values for {self.name}")
        return None

    @property
    def native_min_value(self):
        return self._min_value

    @property
    def native_max_value(self):
        return self._max_value

    @property
    def native_step(self):
        return self._step

    @property
    def mode(self):
        return NumberMode.SLIDER