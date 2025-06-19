from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import TEMP_CELSIUS
from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD, CONF_DEVICES
from .api import IxfieldApi
from .coordinator import IxfieldCoordinator
import logging
import aiohttp

_LOGGER = logging.getLogger(__name__)

SENSOR_MAP = {
    "poolTempWithSettings": {"name": "Water Temperature", "unit": TEMP_CELSIUS},
    "targetTemperature": {"name": "Target Water Temperature", "unit": TEMP_CELSIUS},
    "targetORP": {"name": "Target ORP", "unit": "mV"},
    "orp": {"name": "ORP", "unit": "mV"},
    "targetpH": {"name": "Target pH", "unit": "pH"},
    "pH": {"name": "pH", "unit": "pH"},
    "remainingAgentA": {"name": "Agent A", "unit": "L"},
    "salinity": {"name": "Salinity", "unit": "%"},
    "ambientTemperature": {"name": "Ambient Temperature", "unit": TEMP_CELSIUS},
    "targetHeaterMode": {"name": "Heating / Cooling Mode", "unit": None},
}

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up IXField sensors from a config entry."""
    email = config_entry.data[CONF_EMAIL]
    password = config_entry.data[CONF_PASSWORD]
    device_ids = [d.strip() for d in config_entry.data[CONF_DEVICES].split(",") if d.strip()]
    session = aiohttp.ClientSession()
    api = IxfieldApi(email, password, session)
    await api.async_login()

    coordinator = IxfieldCoordinator(hass, api, device_ids)
    await coordinator.async_config_entry_first_refresh()

    sensors = []
    for device_id in device_ids:
        device_data = coordinator.data.get(device_id, {})
        device = device_data.get("data", {}).get("device", {})
        name_prefix = device.get("name", device_id)
        for value in device.get("liveDeviceData", {}).get("operatingValues", []):
            key = value.get("name")
            if key not in SENSOR_MAP:
                continue
            sensors.append(IxfieldSensor(coordinator, device_id, name_prefix, value, SENSOR_MAP[key]))
    async_add_entities(sensors)

class IxfieldSensor(CoordinatorEntity, Entity):
    def __init__(self, coordinator, device_id, device_name, value, meta):
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_name = device_name
        self._value_name = value.get("name")
        self._label = meta["name"]
        self._unit = meta["unit"]
        self._attr_name = f"{device_name} {self._label}"
        self._attr_unique_id = f"{device_id}_{self._value_name}"

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def native_value(self):
        device_data = self.coordinator.data.get(self._device_id, {})
        device = device_data.get("data", {}).get("device", {})
        for value in device.get("liveDeviceData", {}).get("operatingValues", []):
            if value.get("name") == self._value_name:
                return value.get("value")
        return None

    @property
    def unit_of_measurement(self):
        return self._unit 