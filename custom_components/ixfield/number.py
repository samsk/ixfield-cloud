"""Support for IXField number entities."""
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature
from homeassistant.components.sensor import SensorDeviceClass
from .const import DOMAIN, IXFIELD_DEVICE_URL
from .sensor_config import should_skip_sensor_for_platform
from .optimistic_state import OptimisticStateManager, float_comparison_with_tolerance
from .entity_helper import EntityNamingMixin, create_unique_id, EntityCommonAttrsMixin, EntityValueMixin
import logging
import asyncio

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up IXField number entities from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    device_ids = coordinator.device_ids

    numbers = []
    created_unique_ids = set()
    all_number_names = []
    
    for device_id in device_ids:
        device_info = coordinator.get_device_info(device_id)
        device_name = coordinator.get_device_name(device_id)
        _LOGGER.info(f"Processing number entities for device {device_id}: {device_name}")
        
        device_data = coordinator.data.get(device_id, {})
        device = device_data.get("data", {}).get("device", {})
        operating_values = device.get("liveDeviceData", {}).get("operatingValues", [])
        
        # Process operating values to find settable sensors
        for sensor_data in operating_values:
            sensor_name = sensor_data.get("name")
            if not sensor_name:
                continue
            
            # Use global configuration to determine if this sensor should be skipped
            if should_skip_sensor_for_platform(sensor_name, sensor_data, "number"):
                _LOGGER.debug(f"Skipping sensor {sensor_name} - not suitable for number platform")
                continue
            
            # Import the config function from sensor.py
            from .sensor import get_sensor_config
            config = get_sensor_config(sensor_name, sensor_data)
            
            # Create additional target number entity if show_desired is True
            if config.get("show_desired", False):
                target_config = config.copy()
                target_config["name"] = f"Target {config['name']}"
                target_number = IxfieldNumber(coordinator, device_id, device_name, sensor_name, target_config, is_target=True)
                if target_number.unique_id not in created_unique_ids:
                    numbers.append(target_number)
                    created_unique_ids.add(target_number.unique_id)
                    all_number_names.append(target_number.name)
                    _LOGGER.debug(f"Created target number entity: {target_number.name}")
    
    _LOGGER.info(f"Created {len(numbers)} number entities: {all_number_names}")
    async_add_entities(numbers)

class IxfieldNumber(CoordinatorEntity, NumberEntity, EntityNamingMixin, EntityCommonAttrsMixin, EntityValueMixin):
    """Representation of a settable IXField number entity."""

    def __init__(self, coordinator, device_id, device_name, sensor_name, config, is_target=False):
        self.setup_entity_naming(device_name, sensor_name, "number", config["name"], is_target)
        self.set_common_attrs(config, "number")
        super().__init__(coordinator)

        self._device_id = device_id
        self._device_name = device_name
        self._sensor_name = sensor_name
        self._is_target = is_target
        self._attr_unique_id = create_unique_id(device_id, sensor_name, "number", is_target)
        self._optimistic = OptimisticStateManager(self.name, "Number")
        self._optimistic.set_entity_ref(self)
        _LOGGER.debug(f"Initialized IxfieldNumber: {self.name}, is_target: {is_target}")

    @property
    def native_value(self):
        """Return the current value of the number entity."""
        # Use the optimistic state manager to get the current value
        value_key = "desiredValue" if self._is_target else "value"
        value = self.get_sensor_value(self._sensor_name, value_key)
        return self._optimistic.get_current_value(value)

    async def async_set_native_value(self, value):
        """Set the value of the number entity."""
        api = self.coordinator.api
        async def api_call():
            if self._is_target:
                return await api.async_set_control(self._device_id, self._sensor_name, str(value), set_desired=True)
            else:
                return await api.async_set_control(self._device_id, self._sensor_name, str(value))
        await self._optimistic.execute_with_optimistic_update(
            target_value=float(value),
            api_call=api_call,
            verification_call=self._get_actual_value,
            value_comparison=float_comparison_with_tolerance,
            coordinator_refresh=self.coordinator.async_request_refresh
        )

    def _get_actual_value(self):
        """Get the actual value from coordinator data without optimistic updates."""
        value_key = "desiredValue" if self._is_target else "value"
        value = self.get_sensor_value(self._sensor_name, value_key)
        
        # Convert to float if possible
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
        return None

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