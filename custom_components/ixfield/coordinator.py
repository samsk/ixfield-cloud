from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from datetime import timedelta
import logging

_LOGGER = logging.getLogger(__name__)

class IxfieldCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, api, device_ids, update_interval=timedelta(minutes=2)):
        super().__init__(
            hass,
            _LOGGER,
            name="IXField Device Data",
            update_interval=update_interval,
        )
        self.api = api
        self.device_ids = device_ids

    async def _async_update_data(self):
        data = {}
        for device_id in self.device_ids:
            try:
                device_data = await self.api.async_get_device(device_id)
                data[device_id] = device_data
            except Exception as err:
                _LOGGER.error(f"Error updating device {device_id}: {err}")
                raise UpdateFailed(f"Error updating device {device_id}: {err}")
        return data 