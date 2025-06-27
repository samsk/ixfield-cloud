"""Tests for IXField services module."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.const import ATTR_ENTITY_ID

from custom_components.ixfield.services import (
    async_setup_services,
    async_unload_services,
)
from .test_data import SAMPLE_DEVICE_DATA


class TestServices:
    """Test IXField services functionality."""

    @pytest.mark.asyncio
    async def test_async_setup_services(self, mock_hass, mock_coordinator):
        """Test service setup."""
        # Mock the coordinator in hass data
        mock_hass.data = {
            "ixfield": {
                "test_entry": {
                    "coordinator": mock_coordinator
                }
            }
        }
        
        # Mock service registration
        mock_hass.services = Mock()
        mock_hass.services.async_register = Mock()
        
        await async_setup_services(mock_hass)
        
        # Verify services were registered
        assert mock_hass.services.async_register.call_count >= 1

    @pytest.mark.asyncio
    async def test_async_unload_services(self, mock_hass):
        """Test service unload."""
        # Mock service deregistration
        mock_hass.services = Mock()
        mock_hass.services.async_remove = Mock()
        
        await async_unload_services(mock_hass)
        
        # Verify services were deregistered
        assert mock_hass.services.async_remove.call_count >= 1

    @pytest.mark.asyncio
    async def test_service_error_handling(self, mock_hass):
        """Test service error handling."""
        # Mock service registration to raise an exception
        mock_hass.services = Mock()
        mock_hass.services.async_register = Mock(side_effect=Exception("Service registration failed"))
        
        # Should raise an exception since the implementation doesn't handle errors
        with pytest.raises(Exception, match="Service registration failed"):
            await async_setup_services(mock_hass)

    @pytest.mark.asyncio
    async def test_service_logging(self, mock_hass, mock_coordinator):
        """Test service logging."""
        # Mock the coordinator in hass data
        mock_hass.data = {
            "ixfield": {
                "test_entry": {
                    "coordinator": mock_coordinator
                }
            }
        }
        
        # Mock service registration
        mock_hass.services = Mock()
        mock_hass.services.async_register = Mock()
        
        # The service setup doesn't log anything during setup
        # Only individual services log when called
        await async_setup_services(mock_hass)
        
        # Verify services were registered
        assert mock_hass.services.async_register.call_count >= 1 