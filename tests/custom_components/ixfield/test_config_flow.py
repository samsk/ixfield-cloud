"""Tests for IXField config flow module."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, AbortFlow

from custom_components.ixfield.config_flow import IxfieldConfigFlow
from .test_data import SAMPLE_DEVICE_DATA


class TestIxfieldConfigFlow:
    """Test IXField config flow functionality."""

    @pytest.mark.asyncio
    async def test_config_flow_init(self):
        """Test config flow initialization."""
        flow = IxfieldConfigFlow()
        
        assert flow.VERSION == 1

    @pytest.mark.asyncio
    async def test_config_flow_user_step(self, mock_hass):
        """Test config flow user step."""
        flow = IxfieldConfigFlow()
        flow.hass = mock_hass
        
        # Test user step
        result = await flow.async_step_user()
        
        assert result["type"] == FlowResultType.FORM
        assert "data_schema" in result
        assert "step_id" in result
        assert result["step_id"] == "user"

    @pytest.mark.asyncio
    async def test_config_flow_user_step_with_data(self, mock_hass):
        """Test config flow user step with data."""
        flow = IxfieldConfigFlow()
        flow.hass = mock_hass
        flow.context = {}
        # Patch async_progress_by_handler
        mock_hass.config_entries.flow.async_progress_by_handler = Mock(return_value=[])
        flow._async_current_entries = Mock(return_value=[])
        
        # Mock API login and device fetching
        with patch("custom_components.ixfield.config_flow.IxfieldApi") as mock_api_class:
            mock_api = Mock()
            mock_api.async_login = AsyncMock()
            mock_api.async_get_user_devices = AsyncMock(return_value={
                "data": {
                    "me": {
                        "devices": [
                            {"id": "device_1", "name": "Test Pool 1", "type": "POOL"},
                            {"id": "device_2", "name": "Test Pool 2", "type": "POOL"}
                        ]
                    }
                }
            })
            mock_api_class.return_value = mock_api
            
            # Test user step with valid data
            user_input = {
                "email": "test@example.com",
                "password": "test_password"
            }
            
            result = await flow.async_step_user(user_input)
            
            # Should create config entry directly
            assert result["type"] == FlowResultType.CREATE_ENTRY
            assert "data" in result
            assert result["data"]["email"] == "test@example.com"
            assert result["data"]["password"] == "test_password"

    @pytest.mark.asyncio
    async def test_config_flow_user_step_invalid_credentials(self, mock_hass):
        """Test config flow user step with invalid credentials."""
        flow = IxfieldConfigFlow()
        flow.hass = mock_hass
        flow.context = {}
        mock_hass.config_entries.flow.async_progress_by_handler = Mock(return_value=[])
        flow._async_current_entries = Mock(return_value=[])
        
        # Mock API login failure
        with patch("custom_components.ixfield.config_flow.IxfieldApi") as mock_api_class:
            mock_api = Mock()
            mock_api.async_login = AsyncMock(side_effect=Exception("Invalid credentials"))
            mock_api_class.return_value = mock_api
            
            # Test user step with invalid data
            user_input = {
                "email": "test@example.com",
                "password": "wrong_password"
            }
            
            result = await flow.async_step_user(user_input)
            
            # Should show error
            assert result["type"] == FlowResultType.FORM
            assert "errors" in result
            assert "base" in result["errors"]

    @pytest.mark.asyncio
    async def test_config_flow_user_step_no_devices(self, mock_hass):
        """Test config flow user step with no devices found."""
        flow = IxfieldConfigFlow()
        flow.hass = mock_hass
        flow.context = {}
        mock_hass.config_entries.flow.async_progress_by_handler = Mock(return_value=[])
        flow._async_current_entries = Mock(return_value=[])
        
        # Mock API login but no devices
        with patch("custom_components.ixfield.config_flow.IxfieldApi") as mock_api_class:
            mock_api = Mock()
            mock_api.async_login = AsyncMock()
            mock_api.async_get_user_devices = AsyncMock(return_value={
                "data": {
                    "me": {
                        "devices": []
                    }
                }
            })
            mock_api_class.return_value = mock_api
            
            # Test user step with valid data but no devices
            user_input = {
                "email": "test@example.com",
                "password": "test_password"
            }
            
            result = await flow.async_step_user(user_input)
            
            # Should show error
            assert result["type"] == FlowResultType.FORM
            assert "errors" in result
            assert "base" in result["errors"]

    @pytest.mark.asyncio
    async def test_config_flow_user_step_failed_device_fetch(self, mock_hass):
        """Test config flow user step with failed device fetch."""
        flow = IxfieldConfigFlow()
        flow.hass = mock_hass
        flow.context = {}
        mock_hass.config_entries.flow.async_progress_by_handler = Mock(return_value=[])
        flow._async_current_entries = Mock(return_value=[])
        
        # Mock API login but failed device fetch
        with patch("custom_components.ixfield.config_flow.IxfieldApi") as mock_api_class:
            mock_api = Mock()
            mock_api.async_login = AsyncMock()
            mock_api.async_get_user_devices = AsyncMock(return_value=None)
            mock_api_class.return_value = mock_api
            
            # Test user step with valid data but failed device fetch
            user_input = {
                "email": "test@example.com",
                "password": "test_password"
            }
            
            result = await flow.async_step_user(user_input)
            
            # Should show error
            assert result["type"] == FlowResultType.FORM
            assert "errors" in result
            assert "base" in result["errors"]

    @pytest.mark.asyncio
    async def test_config_flow_options_flow(self, mock_hass):
        """Test config flow options flow."""
        flow = IxfieldConfigFlow()
        flow.hass = mock_hass
        
        # Test options flow
        options_flow = flow.async_get_options_flow(Mock())
        
        assert options_flow is not None

    @pytest.mark.asyncio
    async def test_config_flow_error_handling(self, mock_hass):
        """Test config flow error handling."""
        flow = IxfieldConfigFlow()
        flow.hass = mock_hass
        flow.context = {}
        mock_hass.config_entries.flow.async_progress_by_handler = Mock(return_value=[])
        flow._async_current_entries = Mock(return_value=[])
        
        # Mock API exception
        with patch("custom_components.ixfield.config_flow.IxfieldApi") as mock_api_class:
            mock_api = Mock()
            mock_api.async_login = AsyncMock(side_effect=Exception("Network error"))
            mock_api_class.return_value = mock_api
            
            # Test user step with network error
            user_input = {
                "email": "test@example.com",
                "password": "test_password"
            }
            
            result = await flow.async_step_user(user_input)
            
            # Should show error
            assert result["type"] == FlowResultType.FORM
            assert "errors" in result

    @pytest.mark.asyncio
    async def test_config_flow_data_validation(self, mock_hass):
        """Test config flow data validation."""
        flow = IxfieldConfigFlow()
        flow.hass = mock_hass
        flow.context = {}
        mock_hass.config_entries.flow.async_progress_by_handler = Mock(return_value=[])
        flow._async_current_entries = Mock(return_value=[])
        
        # Test with missing required fields
        user_input = {
            "email": "",  # Empty email
            "password": "test_password"
        }
        
        result = await flow.async_step_user(user_input)
        
        # Should show validation error
        assert result["type"] == FlowResultType.FORM
        assert "errors" in result

    @pytest.mark.asyncio
    async def test_config_flow_unique_id_handling(self, mock_hass):
        """Test config flow unique ID handling."""
        flow = IxfieldConfigFlow()
        flow.hass = mock_hass
        flow.context = {}
        mock_hass.config_entries.flow.async_progress_by_handler = Mock(return_value=[])
        # Mock an existing entry with the same unique_id
        mock_entry = Mock()
        mock_entry.unique_id = "test@example.com"
        flow._async_current_entries = Mock(return_value=[mock_entry])
        # Mock API success
        with patch("custom_components.ixfield.config_flow.IxfieldApi") as mock_api_class:
            mock_api = Mock()
            mock_api.async_login = AsyncMock()
            mock_api.async_get_user_devices = AsyncMock(return_value={
                "data": {
                    "me": {
                        "devices": [
                            {"id": "device_1", "name": "Test Pool 1", "type": "POOL"}
                        ]
                    }
                }
            })
            mock_api_class.return_value = mock_api
            # Test user step with existing email
            user_input = {
                "email": "test@example.com",
                "password": "test_password"
            }
            with pytest.raises(AbortFlow):
                await flow.async_step_user(user_input) 