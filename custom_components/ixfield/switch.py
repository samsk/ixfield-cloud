from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, IXFIELD_DEVICE_URL
from .sensor import generate_human_readable_name
import logging

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
        
        # Use human-friendly name from config
        self._attr_name = config["name"]
        
        self._attr_unique_id = f"{device_id}_{self._control_name}"

    @property
    def is_on(self):
        device_data = self.coordinator.data.get(self._device_id, {})
        device = device_data.get("data", {}).get("device", {})
        for control in device.get("liveDeviceData", {}).get("controls", []):
            if control.get("name") == self._control_name:
                return control.get("value") == "true"
        return False

    async def async_turn_on(self, **kwargs):
        api = self.coordinator.api
        success = await api.async_set_control(self._device_id, self._control_name, "true")
        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error(f"Failed to turn ON {self._attr_name}")

    async def async_turn_off(self, **kwargs):
        api = self.coordinator.api
        success = await api.async_set_control(self._device_id, self._control_name, "false")
        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error(f"Failed to turn OFF {self._attr_name}")

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