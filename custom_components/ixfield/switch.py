import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, IXFIELD_DEVICE_URL
from .entity_helper import (
    EntityCommonAttrsMixin,
    EntityNamingMixin,
    EntityValueMixin,
    create_unique_id,
    get_controls,
    create_device_info,
)
from .optimistic_state import OptimisticStateManager, boolean_comparison
from .sensor import generate_human_readable_name

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
        device_name = coordinator.get_device_name(device_id)
        controls = get_controls(coordinator, device_id)
        
        for control in controls:
            control_name = control.get("name")
            if not control_name:
                continue

            # Create switches for controls that end with "State"
            if control_name.endswith("State"):
                config = get_switch_config(control_name, control)
                switches.append(
                    IxfieldSwitch(coordinator, device_id, device_name, control, config)
                )
    async_add_entities(switches)


class IxfieldSwitch(
    CoordinatorEntity,
    SwitchEntity,
    EntityNamingMixin,
    EntityCommonAttrsMixin,
    EntityValueMixin,
):
    def __init__(self, coordinator, device_id, device_name, control, config):
        self.setup_entity_naming(
            device_name, control.get("name"), "switch", config["name"]
        )
        self.set_common_attrs(config, "switch")
        super().__init__(coordinator)

        self._device_id = device_id
        self._device_name = device_name
        self._control_name = control.get("name")
        self._label = control.get("label", self._control_name)
        self._config = config
        self._attr_unique_id = create_unique_id(device_id, self._control_name, "switch")
        self._optimistic = OptimisticStateManager(self.name, "Switch")
        self._optimistic.set_entity_ref(self)

    @property
    def is_on(self):
        # Use the optimistic state manager to get the current value
        value = self.get_control_value(self._control_name, "value")
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
            api_call=lambda: api.async_set_control(
                self._device_id, self._control_name, target_value
            ),
            verification_call=self._get_actual_state,
            value_comparison=boolean_comparison,
            coordinator_refresh=self.coordinator.async_request_refresh,
        )

    def _get_actual_state(self):
        value = self.get_control_value(self._control_name, "value")
        _LOGGER.debug(
            f"Switch {self._attr_name} actual value from coordinator: {value}"
        )
        return value in ["true", "ON", "on", "True"]

    @property
    def device_info(self):
        return create_device_info(self.coordinator, self._device_id, self._device_name)
