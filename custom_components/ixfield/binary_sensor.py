from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    device_ids = coordinator.device_ids
    sensors = []
    for device_id in device_ids:
        device_data = coordinator.data.get(device_id, {})
        device = device_data.get("data", {}).get("device", {})
        name_prefix = device.get("name", device_id)
        for value in device.get("liveDeviceData", {}).get("operatingValues", []):
            if value.get("name") == "heaterMode":
                sensors.append(IxfieldHeatingBinarySensor(coordinator, device_id, name_prefix, value))
    async_add_entities(sensors)

class IxfieldHeatingBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, device_id, device_name, value):
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_name = device_name
        self._value_name = value.get("name")
        self._label = value.get("label", self._value_name)
        self._attr_name = f"{device_name} {self._label}"
        self._attr_unique_id = f"{device_id}_{self._value_name}"

    @property
    def is_on(self):
        device_data = self.coordinator.data.get(self._device_id, {})
        device = device_data.get("data", {}).get("device", {})
        for value in device.get("liveDeviceData", {}).get("operatingValues", []):
            if value.get("name") == self._value_name:
                return value.get("value") == "HEATING"
        return False 