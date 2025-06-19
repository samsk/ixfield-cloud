from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    device_ids = coordinator.device_ids
    climates = []
    for device_id in device_ids:
        device_data = coordinator.data.get(device_id, {})
        device = device_data.get("data", {}).get("device", {})
        name_prefix = device.get("name", device_id)
        live = device.get("liveDeviceData", {})
        # Only add if both water temp and target temp are present
        has_temp = any(v.get("name") == "poolTempWithSettings" for v in live.get("operatingValues", []))
        has_target = any(v.get("name") == "targetTemperature" for v in live.get("operatingValues", []))
        has_mode = any(v.get("name") == "targetHeaterMode" for v in live.get("operatingValues", []))
        if has_temp and has_target and has_mode:
            climates.append(IxfieldThermostat(coordinator, device_id, name_prefix))
    async_add_entities(climates)

class IxfieldThermostat(CoordinatorEntity, ClimateEntity):
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.AUTO, HVACMode.OFF]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.HVAC_MODE
    _attr_temperature_unit = TEMP_CELSIUS

    def __init__(self, coordinator, device_id, device_name):
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_name = device_name
        self._attr_name = f"{device_name} Pool Thermostat"
        self._attr_unique_id = f"{device_id}_thermostat"

    @property
    def current_temperature(self):
        return self._get_value("poolTempWithSettings")

    @property
    def target_temperature(self):
        return self._get_value("targetTemperature")

    @property
    def hvac_mode(self):
        mode = self._get_value("targetHeaterMode")
        if mode == "HEATING":
            return HVACMode.HEAT
        elif mode == "DISABLED":
            return HVACMode.OFF
        else:
            return HVACMode.AUTO

    def _get_value(self, name):
        device_data = self.coordinator.data.get(self._device_id, {})
        device = device_data.get("data", {}).get("device", {})
        for value in device.get("liveDeviceData", {}).get("operatingValues", []):
            if value.get("name") == name:
                try:
                    return float(value.get("value"))
                except (TypeError, ValueError):
                    return value.get("value")
        return None

    async def async_set_temperature(self, **kwargs):
        temp = kwargs.get("temperature")
        if temp is not None:
            api = self.coordinator.api
            await api.async_set_control(self._device_id, "targetTemperature", str(temp))
            await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode):
        api = self.coordinator.api
        if hvac_mode == HVACMode.HEAT:
            await api.async_set_control(self._device_id, "targetHeaterMode", "HEATING")
        elif hvac_mode == HVACMode.OFF:
            await api.async_set_control(self._device_id, "targetHeaterMode", "DISABLED")
        else:
            await api.async_set_control(self._device_id, "targetHeaterMode", "AUTO")
        await self.coordinator.async_request_refresh() 