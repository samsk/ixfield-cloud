"""Shared test fixtures for IXField integration tests."""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from custom_components.ixfield.const import DOMAIN
from custom_components.ixfield.coordinator import IxfieldCoordinator
from custom_components.ixfield.api import IxfieldApi
from tests.custom_components.ixfield.test_data import SAMPLE_DEVICE_DATA


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = Mock(spec=HomeAssistant)
    hass.data = {}
    return hass


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    config_entry = Mock(spec=ConfigEntry)
    config_entry.entry_id = "test_entry_id"
    config_entry.data = {
        "email": "test@example.com",
        "password": "test_password",
        "devices": "test_device_id",
        "device_names": {"test_device_id": "Test Pool"},
        "extract_device_info_sensors": True
    }
    return config_entry


@pytest.fixture
def mock_api():
    """Create a mock IXField API instance."""
    api = Mock(spec=IxfieldApi)
    api.email = "test@example.com"
    api.password = "test_password"
    api.token = "test_token_123"
    api.user_id = "test_user_123"
    
    # Mock API methods
    api.login = AsyncMock(return_value=True)
    api.get_devices = AsyncMock(return_value=[
        {"id": "test_device_id", "name": "Test Pool", "type": "POOL"}
    ])
    api.get_device_data = AsyncMock(return_value=SAMPLE_DEVICE_DATA)
    api.set_operating_value = AsyncMock(return_value=True)
    api.set_control_value = AsyncMock(return_value=True)
    api.start_service_sequence = AsyncMock(return_value=True)
    
    return api


@pytest.fixture
def mock_coordinator(mock_hass, mock_api):
    """Create a mock IXField coordinator instance."""
    coordinator = Mock(spec=IxfieldCoordinator)
    coordinator.hass = mock_hass
    coordinator.api = mock_api
    coordinator.device_ids = ["test_device_id"]
    coordinator.device_names = {"test_device_id": "Test Pool"}
    coordinator.extract_device_info_sensors = True
    coordinator.data = {
        "test_device_id": SAMPLE_DEVICE_DATA
    }
    
    # Mock coordinator methods
    coordinator.get_device_info = Mock(return_value=SAMPLE_DEVICE_DATA["data"]["device"])
    coordinator.get_device_name = Mock(return_value="Test Pool")
    coordinator.should_extract_device_info_sensors = Mock(return_value=True)
    coordinator.async_set_operating_value = AsyncMock(return_value=True)
    coordinator.async_set_control_value = AsyncMock(return_value=True)
    coordinator.async_start_service_sequence = AsyncMock(return_value=True)
    coordinator.async_refresh = AsyncMock()
    
    return coordinator


@pytest.fixture
def mock_async_add_entities():
    """Create a mock async_add_entities function."""
    return Mock()


@pytest.fixture
def sample_device_data():
    """Provide sample device data for tests."""
    return SAMPLE_DEVICE_DATA


@pytest.fixture
def sample_operating_values():
    """Provide sample operating values for tests."""
    return SAMPLE_DEVICE_DATA["data"]["device"]["liveDeviceData"]["operatingValues"]


@pytest.fixture
def sample_controls():
    """Provide sample controls for tests."""
    return SAMPLE_DEVICE_DATA["data"]["device"]["liveDeviceData"]["controls"]


@pytest.fixture
def sample_service_sequences():
    """Provide sample service sequences for tests."""
    return SAMPLE_DEVICE_DATA["data"]["device"]["liveDeviceData"]["serviceSequences"]


@pytest.fixture
def mock_device_info():
    """Provide mock device info for tests."""
    return {
        "id": "test_device_id",
        "name": "Test Pool",
        "type": "POOL",
        "controller": "TEST-CONTROLLER",
        "connectionStatus": "ONLINE",
        "company": {"name": "Test Company"},
        "thing_type": {"name": "test-type"},
        "address": {
            "address": "Test Address",
            "city": "Test City",
            "postalCode": "12345"
        },
        "contactInfo": {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+1234567890"
        }
    }


@pytest.fixture
def mock_eligibilities():
    """Provide mock device eligibilities for tests."""
    return {
        "setTargetPh": True,
        "setTargetORP": True,
        "setTargetTemperature": True,
        "deviceControl": True,
        "setRemainingAgentVolume": True,
        "displaySalinity": True,
        "displayAmbientTemperature": True
    }


@pytest.fixture
def mock_sensor_config():
    """Provide mock sensor configuration for tests."""
    return {
        "name": "Water Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "settable": True,
        "show_desired": True,
        "min_value": 0,
        "max_value": 40,
        "step": 0.5,
        "value": "22.8",
        "desired_value": "15.5"
    }


@pytest.fixture
def mock_control_config():
    """Provide mock control configuration for tests."""
    return {
        "name": "Circulation Pump",
        "type": "TOGGLE",
        "settable": True,
        "value": "true"
    }


@pytest.fixture
def mock_enum_config():
    """Provide mock enum configuration for tests."""
    return {
        "name": "Heating Status",
        "settable": False,
        "value": "STANDBY",
        "options": {
            "values": [
                {"value": "COOLING", "label": "Cooling"},
                {"value": "HEATING", "label": "Heating"},
                {"value": "STANDBY", "label": "Standby"}
            ]
        }
    }


@pytest.fixture
def mock_climate_config():
    """Provide mock climate configuration for tests."""
    return {
        "name": "Pool Temperature",
        "unit": "°C",
        "settable": True,
        "min_value": 0,
        "max_value": 40,
        "step": 0.5,
        "value": "22.8",
        "desired_value": "15.5"
    } 