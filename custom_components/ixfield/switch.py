from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, IXFIELD_DEVICE_URL
from .sensor import generate_human_readable_name
from .optimistic_state import OptimisticStateManager, boolean_comparison
import logging
import asyncio

_LOGGER = logging.getLogger(__name__)

# Override configurations for switches - can override name and other properties
SWITCH_MAP = {
    # Example overrides:
    # "filtrationState": {
    #     "name": "Circulation Pump"
    # },
    # "lightsState": {
    #     "name": "Pool Lighting"
    # },
    # "jetstreamState": {
    #     "name": "Counterflow System"
    # },
    # You can override any switch by its exact name from the API
    # "switchNameFromAPI": {
    #     "name": "Your Custom Switch Name"
    # }
}

def get_switch_config(control_name, control_data):
    """Get switch configuration with human-friendly name and overrides."""
    # Start with default configuration
    config = {
        "name": control_data.get("label") or generate_human_readable_name(control_name)
    }
    
    # Apply overrides from SWITCH_MAP
    if control_name in SWITCH_MAP:
        override = SWITCH_MAP[control_name]
        config.update({k: v for k, v in override.items() if v is not None})
    
    return config

async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    device_ids = coordinator.device_ids
    switches = []
    for device_id in device_ids:
        device_data = coordinator.data.get(device_id, {})
        device = device_data.get("data", {}).get("device", {})
        device_name = coordinator.get_device_name(device_id)
        for control in device.get("liveDeviceData", {}).get("controls", []):
            control_name = control.get("name")
            if not control_name:
                continue
                
            # Create switches for controls that end with "State"
            if control_name.endswith("State"):
                config = get_switch_config(control_name, control)
                switches.append(IxfieldSwitch(coordinator, device_id, device_name, control, config))
    async_add_entities(switches)

class IxfieldSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, device_id, device_name, control, config):
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_name = device_name
        self._control_name = control.get("name")
        self._label = control.get("label", self._control_name)
        self._config = config
        self._attr_name = config["name"]
        self._attr_unique_id = f"{device_id}_{self._control_name}"
        # Use the shared optimistic state manager
        self._optimistic = OptimisticStateManager(self._attr_name, "Switch")
        self._optimistic.set_entity_ref(self)

    @property
    def is_on(self):
        # Get the value from coordinator data
        device_data = self.coordinator.data.get(self._device_id, {})
        device = device_data.get("data", {}).get("device", {})
        value = None
        for control in device.get("liveDeviceData", {}).get("controls", []):
            if control.get("name") == self._control_name:
                value = control.get("value")
                break
        # Use the optimistic state manager to get the current value
        return self._optimistic.get_current_value(value in ["true", "ON", "on", "True"])

    async def async_turn_on(self, **kwargs):
        await self._async_set_switch_state(True)

    async def async_turn_off(self, **kwargs):
        await self._async_set_switch_state(False)

    async def _async_set_switch_state(self, target_state):
        api = self.coordinator.api
        target_value = "ON" if target_state else "OFF"
        await self._optimistic.execute_with_optimistic_update(
            target_value=target_state,
            api_call=lambda: api.async_set_control(self._device_id, self._control_name, target_value),
            verification_call=self._get_actual_state,
            value_comparison=boolean_comparison,
            coordinator_refresh=self.coordinator.async_request_refresh
        )

    def _get_actual_state(self):
        device_data = self.coordinator.data.get(self._device_id, {})
        device = device_data.get("data", {}).get("device", {})
        for control in device.get("liveDeviceData", {}).get("controls", []):
            if control.get("name") == self._control_name:
                value = control.get("value")
                _LOGGER.debug(f"Switch {self._attr_name} actual value from coordinator: {value}")
                return value in ["true", "ON", "on", "True"]
        return False

    @property
    def device_info(self):
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