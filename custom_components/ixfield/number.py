"""Support for IXField number entities."""
import logging
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature

from .const import DOMAIN, IXFIELD_DEVICE_URL
from .entity_helper import (
    EntityCommonAttrsMixin,
    EntityNamingMixin,
    EntityValueMixin,
    create_unique_id,
    get_operating_values,
)
from .optimistic_state import OptimisticStateManager, float_comparison_with_tolerance
from .sensor import get_sensor_config
from .sensor_config import should_skip_sensor_for_platform

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up IXField number entities from a config entry."""
    try:
        _LOGGER.info("Starting IXField number platform setup")
        
        coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
        device_ids = coordinator.device_ids
        
        _LOGGER.info(f"Found {len(device_ids)} devices for number platform")

        numbers = []
        created_unique_ids = set()

        for device_id in device_ids:
            device_name = coordinator.get_device_name(device_id)
            
            # Get operating values using common function
            operating_values = get_operating_values(coordinator, device_id)
            
            if not operating_values:
                _LOGGER.warning(f"No operating values found for device {device_id}")
                continue

            _LOGGER.info(f"Processing {len(operating_values)} operating values for number entities on device {device_id}")

            # Process all operating values to find suitable number entities
            for sensor_data in operating_values:
                sensor_name = sensor_data.get("name")
                if not sensor_name:
                    continue

                # Debug logging to see what's being processed
                _LOGGER.info(
                    f"Processing number candidate: {sensor_name}, settable: {sensor_data.get('settable')}, type: {sensor_data.get('type')}"
                )

                # Use global configuration to determine if this sensor should be skipped
                if should_skip_sensor_for_platform(sensor_name, sensor_data, "number"):
                    _LOGGER.info(
                        f"Skipping sensor {sensor_name} - not suitable for number platform"
                    )
                    continue

                # Only process settable sensors (not enum sensors)
                if sensor_data.get("type") == "ENUM":
                    _LOGGER.info(
                        f"Skipping sensor {sensor_name} - enum sensors go to select platform"
                    )
                    continue

                try:
                    config = get_sensor_config(sensor_name, sensor_data)
                    # Add "Target" suffix to the name for number entities
                    config["name"] = f"{config['name']} Target"
                    _LOGGER.info(
                        f"Processing number candidate: {sensor_name}, config: {config}"
                    )

                    number_entity = IxfieldNumber(
                        coordinator, device_id, device_name, sensor_name, config
                    )

                    if number_entity.unique_id not in created_unique_ids:
                        numbers.append(number_entity)
                        created_unique_ids.add(number_entity.unique_id)
                        _LOGGER.info(f"Created number entity: {number_entity.name}")
                    else:
                        _LOGGER.info(
                            f"Number entity {number_entity.name} already exists, skipping"
                        )
                except Exception as e:
                    _LOGGER.error(f"Error creating number entity for {sensor_name}: {e}")

        _LOGGER.info(f"Created {len(numbers)} number entities")
        async_add_entities(numbers)
        
    except Exception as e:
        _LOGGER.error(f"Error in number platform setup: {e}")
        import traceback
        _LOGGER.error(f"Traceback: {traceback.format_exc()}")


class IxfieldNumber(
    CoordinatorEntity,
    NumberEntity,
    EntityNamingMixin,
    EntityCommonAttrsMixin,
    EntityValueMixin,
):
    """Representation of an IXField number entity."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.AUTO

    def __init__(self, coordinator, device_id, device_name, sensor_name, config):
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_name = device_name
        self._sensor_name = sensor_name
        self._config = config
        self._optimistic_manager = OptimisticStateManager(sensor_name, "number")
        self._optimistic_manager.set_entity_ref(self)

        # Set up entity naming using the correct mixin method
        self.setup_entity_naming(
            device_name, sensor_name, "number", config.get("name", sensor_name)
        )

        # Set up common attributes using the correct mixin method
        self.set_common_attrs(config, "number")

        # Set up unique ID
        self._attr_unique_id = create_unique_id(device_id, sensor_name, "number")

    @property
    def name(self) -> str | None:
        return self._attr_name

    def _get_current_value(self) -> float | None:
        """Get the current desired/target value from coordinator data."""
        return self.get_sensor_value(self._sensor_name, "desiredValue")

    @property
    def native_value(self) -> float | None:
        """Return the current desired/target value."""
        return self._get_current_value()

    @property
    def native_min_value(self) -> float:
        """Return the minimum value."""
        # Use config value if available, otherwise provide sensible defaults based on unit
        min_value = self._config.get("min_value")
        if min_value is not None:
            return float(min_value)
        
        # Default values based on unit
        unit = self._config.get("unit", "")
        if unit == UnitOfTemperature.CELSIUS:
            return 10.0
        elif unit == "pH":
            return 7.0
        elif unit == "mV":  # ORP
            return 100.0
        else:
            return 0.0

    @property
    def native_max_value(self) -> float:
        """Return the maximum value."""
        # Use config value if available, otherwise provide sensible defaults based on unit
        max_value = self._config.get("max_value")
        if max_value is not None:
            return float(max_value)
        
        # Default values based on unit
        unit = self._config.get("unit", "")
        if unit == UnitOfTemperature.CELSIUS:
            return 40.0
        elif unit == "pH":
            return 8.0
        elif unit == "mV":  # ORP
            return 800.0
        else:
            return 100.0

    @property
    def native_step(self) -> float:
        """Return the step value."""
        # Use config value if available, otherwise provide sensible defaults based on unit
        step = self._config.get("step")
        if step is not None:
            return float(step)
        
        # Default values based on unit
        unit = self._config.get("unit", "")
        if unit == UnitOfTemperature.CELSIUS:
            return 0.5
        elif unit == "pH":
            return 0.05
        elif unit == "mV":  # ORP
            return 10.0
        else:
            return 1.0

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return self._config.get("unit", "")

    async def async_set_native_value(self, value: float) -> None:
        """Set new desired/target value."""
        await self._optimistic_manager.execute_with_optimistic_update(
            target_value=value,
            api_call=lambda: self.coordinator.api.async_set_control(
                self._device_id, self._sensor_name, value
            ),
            verification_call=lambda: self.get_sensor_value(self._sensor_name, "desiredValue"),
            value_comparison=float_comparison_with_tolerance,
            coordinator_refresh=self.coordinator.async_request_refresh,
            entity_state_update=self.async_write_ha_state,
        )

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
