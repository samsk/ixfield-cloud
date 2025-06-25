"""Support for IXField select entities."""
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.select import SelectEntity
from .const import DOMAIN, IXFIELD_DEVICE_URL
from .sensor_config import should_skip_sensor_for_platform
from .optimistic_state import OptimisticStateManager, string_comparison_ignore_case
import logging
import asyncio

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up IXField select entities from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    device_ids = coordinator.device_ids

    selects = []
    created_unique_ids = set()
    all_select_names = []
    
    for device_id in device_ids:
        device_info = coordinator.get_device_info(device_id)
        device_name = coordinator.get_device_name(device_id)
        _LOGGER.info(f"Processing select entities for device {device_id}: {device_name}")
        
        device_data = coordinator.data.get(device_id, {})
        device = device_data.get("data", {}).get("device", {})
        operating_values = device.get("liveDeviceData", {}).get("operatingValues", [])
        
        # Process operating values to find settable enum sensors
        for sensor_data in operating_values:
            sensor_name = sensor_data.get("name")
            if not sensor_name:
                continue
            
            # Use global configuration to determine if this sensor should be skipped
            if should_skip_sensor_for_platform(sensor_name, sensor_data, "select"):
                _LOGGER.debug(f"Skipping sensor {sensor_name} - not suitable for select platform")
                continue
            
            # Import the config function from sensor.py
            from .sensor import get_sensor_config
            config = get_sensor_config(sensor_name, sensor_data)
            
            # Create select entity for settable enum sensor
            select_entity = IxfieldSelect(coordinator, device_id, device_name, sensor_name, config)
            if select_entity.unique_id not in created_unique_ids:
                selects.append(select_entity)
                created_unique_ids.add(select_entity.unique_id)
                all_select_names.append(select_entity.name)
                _LOGGER.debug(f"Created select entity: {select_entity.name}")
    
    _LOGGER.info(f"Created {len(selects)} select entities: {all_select_names}")
    async_add_entities(selects)

class IxfieldSelect(CoordinatorEntity, SelectEntity):
    """Representation of a settable IXField select entity."""

    def __init__(self, coordinator, device_id, device_name, sensor_name, config):
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_name = device_name
        self._sensor_name = sensor_name
        
        # Set up the entity properties
        self._attr_name = config["name"]
        self._attr_unique_id = f"{device_id}_{sensor_name}"
        
        # Get options from the sensor data
        options = config.get("options", {})
        self._attr_options = options.get("options", [])  # List of available options
        self._attr_current_option = None
        
        # Use the shared optimistic state manager
        self._optimistic = OptimisticStateManager(self._attr_name, "Select")
        self._optimistic.set_entity_ref(self)
        
        _LOGGER.debug(f"Initialized IxfieldSelect: {self.name} with options: {self._attr_options}")

    @property
    def current_option(self):
        """Return the current selected option."""
        # Get the value from coordinator data
        device_data = self.coordinator.data.get(self._device_id, {})
        value = None
        if device_data and "data" in device_data:
            live_data = device_data.get("data", {}).get("device", {}).get("liveDeviceData", {})
            for sensor in live_data.get("operatingValues", []):
                if sensor.get("name") == self._sensor_name:
                    value = sensor.get("value")
                    break
        # Use the optimistic state manager to get the current value
        return self._optimistic.get_current_value(value)

    async def async_select_option(self, option: str):
        """Set the selected option."""
        api = self.coordinator.api
        await self._optimistic.execute_with_optimistic_update(
            target_value=option,
            api_call=lambda: api.async_set_control(self._device_id, self._sensor_name, option),
            verification_call=self._get_actual_option,
            value_comparison=string_comparison_ignore_case,
            coordinator_refresh=self.coordinator.async_request_refresh
        )

    def _get_actual_option(self):
        """Get the actual option from coordinator data without optimistic updates."""
        device_data = self.coordinator.data.get(self._device_id, {})
        if not device_data or "data" not in device_data:
            return None
        
        live_data = device_data.get("data", {}).get("device", {}).get("liveDeviceData", {})
        if not live_data:
            return None
        
        operating_values = live_data.get("operatingValues", [])
        if not operating_values:
            return None
        
        # Find the sensor by name
        for sensor in operating_values:
            if sensor.get("name") == self._sensor_name:
                value = sensor.get("value")
                _LOGGER.debug(f"Select {self.name} actual value from coordinator: {value}")
                return value
        
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