from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

SWITCHES = {
    "filtrationState": "Circulation Pump",
    "lightsState": "Lighting",
    "jetstreamState": "Counterflow",
}

async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    device_ids = coordinator.device_ids
    switches = []
    for device_id in device_ids:
        device_data = coordinator.data.get(device_id, {})
        device = device_data.get("data", {}).get("device", {})
        name_prefix = device.get("name", device_id)
        for control in device.get("liveDeviceData", {}).get("controls", []):
            if control.get("name") in SWITCHES:
                switches.append(IxfieldSwitch(coordinator, device_id, name_prefix, control))
    async_add_entities(switches)

class IxfieldSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, device_id, device_name, control):
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_name = device_name
        self._control_name = control.get("name")
        self._label = control.get("label", self._control_name)
        self._attr_name = f"{device_name} {self._label}"
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