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
)
from .optimistic_state import OptimisticStateManager, float_comparison_with_tolerance
from .sensor import get_sensor_config

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up IXField number entities from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    device_ids = coordinator.device_ids

    numbers = []
    created_unique_ids = set()

    for device_id in device_ids:
        device_name = coordinator.get_device_name(device_id)
        device_info = coordinator.get_device_info(device_id)
        if not device_info:
            continue

        # Get operating values (sensors) for this device
        operating_values = device_info.get("liveDeviceData", {}).get(
            "operatingValues", []
        )
        if not operating_values:
            continue

        # Look for temperature sensors that end with "WithSettings"
        for sensor_data in operating_values:
            sensor_name = sensor_data.get("name")
            if not sensor_name or not sensor_name.endswith("WithSettings"):
                _LOGGER.debug(
                    f"Skipping sensor {sensor_name} - doesn't end with 'WithSettings'"
                )
                continue

            config = get_sensor_config(sensor_name, sensor_data)
            _LOGGER.debug(
                f"Processing number candidate: {sensor_name}, config: {config}"
            )

            # Check if this is a temperature sensor with Celsius units
            if config["unit"] != UnitOfTemperature.CELSIUS:
                _LOGGER.debug(
                    f"Skipping sensor {sensor_name} - unit is {config['unit']}, not Celsius"
                )
                continue

            number_entity = IxfieldNumber(
                coordinator, device_id, device_name, sensor_name, config
            )

            if number_entity.unique_id not in created_unique_ids:
                numbers.append(number_entity)
                created_unique_ids.add(number_entity.unique_id)
                _LOGGER.debug(f"Created number entity: {number_entity.name}")
            else:
                _LOGGER.debug(
                    f"Number entity {number_entity.name} already exists, skipping"
                )

    _LOGGER.info(f"Created {len(numbers)} number entities")
    async_add_entities(numbers)


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
        """Get the current value from coordinator data."""
        return self.get_sensor_value(self._sensor_name, "value")

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        return self._get_current_value()

    @property
    def native_min_value(self) -> float:
        """Return the minimum value."""
        return self._config.get("min_value", 10.0)

    @property
    def native_max_value(self) -> float:
        """Return the maximum value."""
        return self._config.get("max_value", 40.0)

    @property
    def native_step(self) -> float:
        """Return the step value."""
        return self._config.get("step", 0.5)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return self._config.get("unit", UnitOfTemperature.CELSIUS)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self._optimistic_manager.execute_with_optimistic_update(
            target_value=value,
            api_call=lambda: self.coordinator.api.async_set_control(
                self._device_id, self._sensor_name, value
            ),
            verification_call=lambda: self._get_current_value(),
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
