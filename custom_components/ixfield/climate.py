from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, IXFIELD_DEVICE_URL
import logging

_LOGGER = logging.getLogger(__name__)

# Import the same configuration from sensor.py
from .sensor import SENSOR_MAPPINGS, SENSOR_MAP, get_sensor_config, generate_human_readable_name

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up IXField climate entities from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    device_ids = coordinator.device_ids
    climates = []
    created_unique_ids = set()
    
    for device_id in device_ids:
        device_info = coordinator.get_device_info(device_id)
        device_name = coordinator.get_device_name(device_id)
        _LOGGER.info(f"Processing climate entities for device {device_id}: {device_name}")
        
        device_data = coordinator.data.get(device_id, {})
        device = device_data.get("data", {}).get("device", {})
        operating_values = device.get("liveDeviceData", {}).get("operatingValues", [])
        
        _LOGGER.debug(f"Processing {len(operating_values)} operating values for climate entities on device {device_id}")
        
        # Find temperature sensors that end with "WithSettings" and have Celsius units
        for sensor_data in operating_values:
            sensor_name = sensor_data.get("name")
            if not sensor_name or not sensor_name.endswith("WithSettings"):
                continue
                
            config = get_sensor_config(sensor_name, sensor_data)
            
            # Check if this is a temperature sensor with Celsius units
            if config["unit"] != UnitOfTemperature.CELSIUS:
                continue
            
            # Look for corresponding mode sensor
            mode_sensor_name = sensor_name.replace("WithSettings", "Mode")
            mode_sensor = None
            
            for mode_data in operating_values:
                if mode_data.get("name") == mode_sensor_name:
                    mode_sensor = mode_data
                    break
            
            climate_entity = IxfieldClimate(
                coordinator, device_id, device_name, sensor_name, config, mode_sensor
            )
            
            if climate_entity.unique_id not in created_unique_ids:
                climates.append(climate_entity)
                created_unique_ids.add(climate_entity.unique_id)
                _LOGGER.debug(f"Created climate entity: {climate_entity.name}")
    
    _LOGGER.info(f"Created {len(climates)} climate entities")
    async_add_entities(climates)

class IxfieldClimate(CoordinatorEntity, ClimateEntity):
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.AUTO, HVACMode.OFF]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, device_id, device_name, sensor_name, config, mode_sensor):
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_name = device_name
        self._sensor_name = sensor_name
        self._config = config
        self._mode_sensor = mode_sensor
        
        # Use human-friendly name from config instead of raw sensor name
        self._attr_name = config["name"]
        
        self._attr_unique_id = f"{device_id}_{sensor_name}_climate"
        self._min_temp = config.get("min_value", 10.0)
        self._max_temp = config.get("max_value", 40.0)
        self._target_temperature_step = config.get("step", 0.5)

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def current_temperature(self):
        device_data = self.coordinator.data.get(self._device_id, {})
        device = device_data.get("data", {}).get("device", {})
        operating_values = device.get("liveDeviceData", {}).get("operatingValues", [])
        for value in operating_values:
            if value.get("name") == self._sensor_name:
                result = value.get("value")
                try:
                    return float(result) if result is not None else None
                except (TypeError, ValueError):
                    return None
        return None

    @property
    def target_temperature(self):
        device_data = self.coordinator.data.get(self._device_id, {})
        device = device_data.get("data", {}).get("device", {})
        operating_values = device.get("liveDeviceData", {}).get("operatingValues", [])
        for value in operating_values:
            if value.get("name") == self._sensor_name:
                result = value.get("desiredValue")
                try:
                    return float(result) if result is not None else None
                except (TypeError, ValueError):
                    return None
        return None

    @property
    def min_temp(self):
        return self._min_temp

    @property
    def max_temp(self):
        return self._max_temp

    @property
    def target_temperature_step(self):
        return self._target_temperature_step

    @property
    def hvac_mode(self):
        if not self._mode_sensor:
            return HVACMode.AUTO
            
        device_data = self.coordinator.data.get(self._device_id, {})
        device = device_data.get("data", {}).get("device", {})
        operating_values = device.get("liveDeviceData", {}).get("operatingValues", [])
        for value in operating_values:
            if value.get("name") == self._mode_sensor.get("name"):
                mode = value.get("value")
                if mode == "HEATING":
                    return HVACMode.HEAT
                elif mode == "DISABLED":
                    return HVACMode.OFF
                else:
                    return HVACMode.AUTO
        return HVACMode.AUTO

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

    async def async_set_temperature(self, **kwargs):
        """Set the target temperature."""
        temp = kwargs.get("temperature")
        if temp is not None:
            # Round to nearest step increment
            step = self._target_temperature_step
            rounded_temp = round(temp / step) * step
            api = self.coordinator.api
            success = await api.async_set_control(self._device_id, self._sensor_name, str(rounded_temp))
            if success:
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(f"Failed to set {self._attr_name} temperature to {rounded_temp}")

    async def async_set_hvac_mode(self, hvac_mode):
        """Set the HVAC mode."""
        if not self._mode_sensor:
            return
            
        api = self.coordinator.api
        mode_value = "AUTO"
        if hvac_mode == HVACMode.HEAT:
            mode_value = "HEATING"
        elif hvac_mode == HVACMode.OFF:
            mode_value = "DISABLED"
        
        success = await api.async_set_control(self._device_id, self._mode_sensor.get("name"), mode_value)
        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error(f"Failed to set {self._attr_name} mode to {mode_value}") 