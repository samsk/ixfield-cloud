import logging
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, IXFIELD_DEVICE_URL
from .entity_helper import (
    EntityCommonAttrsMixin,
    EntityNamingMixin,
    EntityValueMixin,
    create_unique_id,
    get_operating_values,
    create_device_info,
)
from .optimistic_state import (
    OptimisticStateManager,
    float_comparison_with_tolerance,
    string_comparison_ignore_case,
)

# Import the same configuration from sensor.py
from .sensor import get_sensor_config

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up IXField climate entities from a config entry."""
    _LOGGER.info("Setting up IXField climate entities")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    device_ids = coordinator.device_ids
    climates = []
    created_unique_ids = set()

    for device_id in device_ids:
        device_name = coordinator.get_device_name(device_id)
        _LOGGER.info(
            f"Processing climate entities for device {device_id}: {device_name}"
        )

        operating_values = get_operating_values(coordinator, device_id)

        _LOGGER.debug(
            f"Processing {len(operating_values)} operating values for climate entities on device {device_id}"
        )
        _LOGGER.debug(
            f"Available operating values: {[v.get('name') for v in operating_values]}"
        )

        # Find temperature sensors that end with "WithSettings" and have Celsius units
        for sensor_data in operating_values:
            sensor_name = sensor_data.get("name")
            if not sensor_name or not sensor_name.endswith("WithSettings"):
                _LOGGER.debug(
                    f"Skipping sensor {sensor_name} - doesn't end with 'WithSettings'"
                )
                continue

            config = get_sensor_config(sensor_name, sensor_data)
            _LOGGER.debug(
                f"Processing climate candidate: {sensor_name}, config: {config}"
            )

            # Check if this is a temperature sensor with Celsius units
            _LOGGER.debug(
                f"Comparing unit: config['unit'] = {config['unit']}, UnitOfTemperature.CELSIUS = {UnitOfTemperature.CELSIUS}"
            )
            if config["unit"] != UnitOfTemperature.CELSIUS:
                _LOGGER.debug(
                    f"Skipping sensor {sensor_name} - unit is {config['unit']}, not Celsius"
                )
                continue

            # Look for corresponding mode sensor
            mode_sensor_name = sensor_name.replace("WithSettings", "Mode")
            mode_sensor = None

            for mode_data in operating_values:
                if mode_data.get("name") == mode_sensor_name:
                    mode_sensor = mode_data
                    break

            if not mode_sensor:
                _LOGGER.debug(
                    f"No mode sensor found for {sensor_name}, looking for {mode_sensor_name}"
                )

            climate_entity = IxfieldClimate(
                coordinator, device_id, device_name, sensor_name, config, mode_sensor
            )

            if climate_entity.unique_id not in created_unique_ids:
                climates.append(climate_entity)
                created_unique_ids.add(climate_entity.unique_id)
                _LOGGER.debug(f"Created climate entity: {climate_entity.name}")
            else:
                _LOGGER.debug(
                    f"Climate entity {climate_entity.name} already exists, skipping"
                )

    _LOGGER.info(f"Created {len(climates)} climate entities")
    async_add_entities(climates)


class IxfieldClimate(
    CoordinatorEntity,
    ClimateEntity,
    EntityNamingMixin,
    EntityCommonAttrsMixin,
    EntityValueMixin,
):
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.AUTO, HVACMode.OFF]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(
        self, coordinator, device_id, device_name, sensor_name, config, mode_sensor
    ):
        self.setup_entity_naming(device_name, sensor_name, "climate", config["name"])
        self.set_common_attrs(config, "climate")
        super().__init__(coordinator)

        self._device_id = device_id
        self._device_name = device_name
        self._sensor_name = sensor_name
        self._config = config
        self._mode_sensor = mode_sensor
        self._attr_unique_id = create_unique_id(device_id, sensor_name, "climate")
        self._min_temp = config.get("min_value", 10.0)
        self._max_temp = config.get("max_value", 40.0)
        self._target_temperature_step = config.get("step", 0.5)
        self._optimistic_temp = OptimisticStateManager(self.name, "ClimateTemp")
        self._optimistic_temp.set_entity_ref(self)
        self._optimistic_mode = OptimisticStateManager(self.name, "ClimateMode")
        self._optimistic_mode.set_entity_ref(self)

    @property
    def current_temperature(self):
        return self.get_sensor_value(self._sensor_name, "value")

    @property
    def target_temperature(self):
        # Get the value from coordinator data
        value = self.get_sensor_value(self._sensor_name, "desiredValue")
        try:
            return self._optimistic_temp.get_current_value(
                float(value) if value is not None else None
            )
        except Exception:
            return self._optimistic_temp.get_current_value(None)

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
        # Get the value from coordinator data
        if not self._mode_sensor:
            return HVACMode.AUTO
        value = self.get_sensor_value(self._mode_sensor.get("name"), "value")
        # Map value to HVACMode
        mode = HVACMode.AUTO
        if value == "HEATING":
            mode = HVACMode.HEAT
        elif value == "DISABLED":
            mode = HVACMode.OFF
        return self._optimistic_mode.get_current_value(mode)

    @property
    def hvac_action(self):
        """Return the current HVAC action (heating, cooling, idle, etc.)."""
        # First check if we have a specific heaterMode sensor
        operating_values = get_operating_values(self.coordinator, self._device_id)
        
        # Look for heaterMode sensor in operating values
        for sensor in operating_values:
            if sensor.get("name") == "heaterMode":
                heater_mode_value = sensor.get("value")
                if heater_mode_value == "HEATING":
                    return "heating"
                break

        # Fallback to checking the mode sensor if available
        if self._mode_sensor:
            mode_value = self.get_sensor_value(self._mode_sensor.get("name"), "value")
            if mode_value == "HEATING":
                return "heating"

        # Check current vs target temperature to determine if heating is needed
        current_temp = self.current_temperature
        target_temp = self.target_temperature

        if current_temp is not None and target_temp is not None:
            # If current temperature is below target and mode is HEAT, we're heating
            if current_temp < target_temp and self.hvac_mode == HVACMode.HEAT:
                return "heating"

        # Default to idle if not heating
        return "idle"

    @property
    def device_info(self):
        """Return device info."""
        return create_device_info(self.coordinator, self._device_id, self._device_name)

    async def async_set_temperature(self, **kwargs):
        temp = kwargs.get("temperature")
        if temp is not None:
            step = self._target_temperature_step
            rounded_temp = round(temp / step) * step
            api = self.coordinator.api
            await self._optimistic_temp.execute_with_optimistic_update(
                target_value=rounded_temp,
                api_call=lambda: api.async_set_control(
                    self._device_id, self._sensor_name, str(rounded_temp)
                ),
                verification_call=self._get_actual_target_temperature,
                value_comparison=float_comparison_with_tolerance,
                coordinator_refresh=self.coordinator.async_request_refresh,
            )

    async def async_set_hvac_mode(self, hvac_mode):
        if not self._mode_sensor:
            return
        api = self.coordinator.api
        mode_value = "AUTO"
        if hvac_mode == HVACMode.HEAT:
            mode_value = "HEATING"
        elif hvac_mode == HVACMode.OFF:
            mode_value = "DISABLED"
        await self._optimistic_mode.execute_with_optimistic_update(
            target_value=hvac_mode,
            api_call=lambda: api.async_set_control(
                self._device_id, self._mode_sensor.get("name"), mode_value
            ),
            verification_call=self._get_actual_hvac_mode,
            value_comparison=string_comparison_ignore_case,
            coordinator_refresh=self.coordinator.async_request_refresh,
        )

    def _get_actual_target_temperature(self):
        device_data = self.coordinator.data.get(self._device_id, {})
        if not device_data or "data" not in device_data:
            return None
        device = device_data.get("data", {}).get("device", {})
        for v in device.get("liveDeviceData", {}).get("operatingValues", []):
            if v.get("name") == self._sensor_name:
                try:
                    return float(v.get("desiredValue"))
                except Exception:
                    return None
        return None

    def _get_actual_hvac_mode(self):
        if not self._mode_sensor:
            return HVACMode.AUTO
        device_data = self.coordinator.data.get(self._device_id, {})
        if not device_data or "data" not in device_data:
            return HVACMode.AUTO
        device = device_data.get("data", {}).get("device", {})
        for v in device.get("liveDeviceData", {}).get("operatingValues", []):
            if v.get("name") == self._mode_sensor.get("name"):
                value = v.get("value")
                if value == "HEATING":
                    return HVACMode.HEAT
                elif value == "DISABLED":
                    return HVACMode.OFF
                else:
                    return HVACMode.AUTO
        return HVACMode.AUTO
