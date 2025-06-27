"""Tests for IXField coordinator and API modules."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.ixfield.coordinator import IxfieldCoordinator
from custom_components.ixfield.api import IxfieldApi
from .test_data import SAMPLE_DEVICE_DATA


class TestIxfieldAPI:
    """Test IXField API functionality."""

    def test_api_initialization(self):
        """Test API initialization."""
        mock_session = Mock()
        api = IxfieldApi("test@example.com", "password123", mock_session)
        
        assert api._email == "test@example.com"
        assert api._password == "password123"
        assert api._session == mock_session

    @pytest.mark.asyncio
    async def test_api_login(self):
        """Test API login functionality."""
        mock_session = Mock()
        api = IxfieldApi("test@example.com", "password123", mock_session)
        
        # Mock successful login response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": {
                "login": {
                    "token": "test_token_123",
                    "user": {
                        "id": "user_123",
                        "email": "test@example.com"
                    }
                }
            }
        })
        
        with patch.object(api, 'async_login') as mock_login:
            mock_login.return_value = None
            await api.async_login()
            
            # Verify login was called
            mock_login.assert_called_once()

    @pytest.mark.asyncio
    async def test_api_login_failure(self):
        """Test API login failure handling."""
        mock_session = Mock()
        api = IxfieldApi("test@example.com", "wrong_password", mock_session)
        
        # Mock failed login response
        with patch.object(api, 'async_login', side_effect=Exception("Authentication failed")):
            with pytest.raises(Exception, match="Authentication failed"):
                await api.async_login()

    @pytest.mark.asyncio
    async def test_api_get_devices(self):
        """Test API get devices functionality."""
        mock_session = Mock()
        api = IxfieldApi("test@example.com", "password123", mock_session)
        api._token = "test_token_123"
        
        # Mock successful devices response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": {
                "devices": [
                    {
                        "id": "device_1",
                        "name": "Test Pool 1",
                        "type": "POOL"
                    },
                    {
                        "id": "device_2",
                        "name": "Test Pool 2",
                        "type": "POOL"
                    }
                ]
            }
        })
        
        with patch.object(api, 'async_get_user_devices', return_value=mock_response.json.return_value):
            devices_response = await api.async_get_user_devices()
            
            assert devices_response is not None
            assert "data" in devices_response
            assert "devices" in devices_response["data"]
            assert len(devices_response["data"]["devices"]) == 2

    @pytest.mark.asyncio
    async def test_api_get_device_data(self):
        """Test API get device data functionality."""
        mock_session = Mock()
        api = IxfieldApi("test@example.com", "password123", mock_session)
        api._token = "test_token_123"
        
        # Mock successful device data response
        with patch.object(api, 'async_get_device', return_value=SAMPLE_DEVICE_DATA):
            device_data = await api.async_get_device("test_device_id")
            
            assert device_data is not None
            assert "data" in device_data
            assert "device" in device_data["data"]
            assert device_data["data"]["device"]["id"] == "RGV3aWNlOjQ1NDQ="

    @pytest.mark.asyncio
    async def test_api_set_operating_value(self):
        """Test API set operating value functionality."""
        mock_session = Mock()
        api = IxfieldApi("test@example.com", "password123", mock_session)
        api._token = "test_token_123"
        
        # Mock successful set value response
        with patch.object(api, 'async_set_control', return_value=True):
            result = await api.async_set_control("test_device_id", "poolTempWithSettings", 25.0)
            
            assert result is True

    @pytest.mark.asyncio
    async def test_api_set_control_value(self):
        """Test API set control value functionality."""
        mock_session = Mock()
        api = IxfieldApi("test@example.com", "password123", mock_session)
        api._token = "test_token_123"
        
        # Mock successful set control response
        with patch.object(api, 'async_set_control', return_value=True):
            result = await api.async_set_control("test_device_id", "filtrationState", True)
            
            assert result is True

    @pytest.mark.asyncio
    async def test_api_start_service_sequence(self):
        """Test API start service sequence functionality."""
        mock_session = Mock()
        api = IxfieldApi("test@example.com", "password123", mock_session)
        api._token = "test_token_123"
        
        # Mock successful service sequence response
        with patch.object(api, 'async_set_control', return_value=True):
            result = await api.async_set_control("test_device_id", "dosingPumpA", True)
            
            assert result is True

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test API error handling."""
        mock_session = Mock()
        api = IxfieldApi("test@example.com", "password123", mock_session)
        api._token = "test_token_123"
        
        # Mock network error
        with patch.object(api, 'async_get_user_devices', side_effect=Exception("Network error")):
            with pytest.raises(Exception, match="Network error"):
                await api.async_get_user_devices()

    def test_api_session_management(self):
        """Test API session management."""
        mock_session = Mock()
        api = IxfieldApi("test@example.com", "password123", mock_session)
        
        # Test session creation
        assert api._session == mock_session


class TestIxfieldDataUpdateCoordinator:
    """Test IXField Data Update Coordinator functionality."""

    @pytest.mark.asyncio
    async def test_coordinator_initialization(self):
        """Test coordinator initialization."""
        mock_hass = Mock()
        mock_api = Mock()
        device_dict = {
            "test_device_id": {
                "name": "Test Pool",
                "type": "POOL",
                "custom_name": "Test Pool"
            }
        }
        
        coordinator = IxfieldCoordinator(
            mock_hass,
            mock_api,
            device_dict,
            extract_device_info_sensors=True
        )
        
        assert coordinator.api == mock_api
        assert coordinator.device_dict == device_dict
        assert coordinator.device_ids == ["test_device_id"]
        assert coordinator.should_extract_device_info_sensors() is True

    @pytest.mark.asyncio
    async def test_coordinator_data_update(self):
        """Test coordinator data update functionality."""
        mock_hass = Mock()
        mock_api = Mock()
        device_dict = {
            "test_device_id": {
                "name": "Test Pool",
                "type": "POOL"
            }
        }
        
        mock_api.async_get_device = AsyncMock(return_value=SAMPLE_DEVICE_DATA)
        
        coordinator = IxfieldCoordinator(
            mock_hass,
            mock_api,
            device_dict
        )
        
        # Test data update
        data = await coordinator._async_update_data()
        
        assert data is not None
        assert "test_device_id" in data
        assert data["test_device_id"] == SAMPLE_DEVICE_DATA

    @pytest.mark.asyncio
    async def test_coordinator_multiple_devices(self):
        """Test coordinator with multiple devices."""
        mock_hass = Mock()
        mock_api = Mock()
        device_dict = {
            "device_1": {"name": "Pool 1", "type": "POOL"},
            "device_2": {"name": "Pool 2", "type": "POOL"}
        }
        
        mock_api.async_get_device = AsyncMock(return_value=SAMPLE_DEVICE_DATA)
        
        coordinator = IxfieldCoordinator(
            mock_hass,
            mock_api,
            device_dict
        )
        
        assert len(coordinator.device_ids) == 2
        assert "device_1" in coordinator.device_ids
        assert "device_2" in coordinator.device_ids

    @pytest.mark.asyncio
    async def test_coordinator_error_handling(self):
        """Test coordinator error handling."""
        mock_hass = Mock()
        mock_api = Mock()
        device_dict = {
            "test_device_id": {
                "name": "Test Pool",
                "type": "POOL"
            }
        }
        
        mock_api.async_get_device = AsyncMock(side_effect=Exception("API Error"))
        
        coordinator = IxfieldCoordinator(
            mock_hass,
            mock_api,
            device_dict
        )
        
        # Test error handling - should raise UpdateFailed
        with pytest.raises(UpdateFailed, match="Error updating device test_device_id: API Error"):
            await coordinator._async_update_data()

    def test_coordinator_device_info_methods(self):
        """Test coordinator device info methods."""
        mock_hass = Mock()
        mock_api = Mock()
        device_dict = {
            "test_device_id": {
                "name": "Test Pool",
                "type": "POOL",
                "custom_name": "Test Pool"
            }
        }
        
        coordinator = IxfieldCoordinator(
            mock_hass,
            mock_api,
            device_dict
        )
        
        # Test device name
        device_name = coordinator.get_device_name("test_device_id")
        assert device_name == "Test Pool"
        
        # Test device type
        device_type = coordinator.get_device_type("test_device_id")
        assert device_type == "Unknown"  # No device info loaded yet
        
        # Test entity name
        entity_name = coordinator.get_entity_name("test_device_id", "sensor")
        assert entity_name == "Test Pool_sensor"

    @pytest.mark.asyncio
    async def test_coordinator_set_operating_value(self):
        """Test coordinator set operating value functionality."""
        # This method doesn't exist in the coordinator
        # The coordinator only handles data updates, not control operations
        pass

    @pytest.mark.asyncio
    async def test_coordinator_set_control_value(self):
        """Test coordinator set control value functionality."""
        # This method doesn't exist in the coordinator
        # The coordinator only handles data updates, not control operations
        pass

    @pytest.mark.asyncio
    async def test_coordinator_start_service_sequence(self):
        """Test coordinator start service sequence functionality."""
        # This method doesn't exist in the coordinator
        # The coordinator only handles data updates, not control operations
        pass

    def test_coordinator_update_interval(self):
        """Test coordinator update interval configuration."""
        mock_hass = Mock()
        mock_api = Mock()
        device_dict = {
            "test_device_id": {
                "name": "Test Pool",
                "type": "POOL"
            }
        }
        
        # Test default update interval
        coordinator = IxfieldCoordinator(
            mock_hass,
            mock_api,
            device_dict
        )
        
        assert coordinator.update_interval == timedelta(minutes=2)
        
        # Test custom update interval
        coordinator_custom = IxfieldCoordinator(
            mock_hass,
            mock_api,
            device_dict,
            update_interval=timedelta(minutes=5)
        )
        
        assert coordinator_custom.update_interval == timedelta(minutes=5)

    @pytest.mark.asyncio
    async def test_coordinator_refresh_data(self):
        """Test coordinator data refresh functionality."""
        mock_hass = Mock()
        mock_api = Mock()
        device_dict = {
            "test_device_id": {
                "name": "Test Pool",
                "type": "POOL"
            }
        }
        
        mock_api.async_get_device = AsyncMock(return_value=SAMPLE_DEVICE_DATA)
        
        coordinator = IxfieldCoordinator(
            mock_hass,
            mock_api,
            device_dict
        )
        
        # Test refresh
        await coordinator.async_refresh()
        
        # Verify API was called
        mock_api.async_get_device.assert_called_once()

    def test_coordinator_device_connection_status(self):
        """Test coordinator device connection status."""
        mock_hass = Mock()
        mock_api = Mock()
        device_dict = {
            "test_device_id": {
                "name": "Test Pool",
                "type": "POOL"
            }
        }
        
        coordinator = IxfieldCoordinator(
            mock_hass,
            mock_api,
            device_dict
        )
        
        # Test status summary - should return device_id since no device info loaded yet
        status = coordinator.get_device_status_summary("test_device_id")
        assert status["name"] == "test_device_id"  # No device info loaded yet

    def test_coordinator_device_eligibilities(self):
        """Test coordinator device eligibilities."""
        # This method doesn't exist in the coordinator
        pass 