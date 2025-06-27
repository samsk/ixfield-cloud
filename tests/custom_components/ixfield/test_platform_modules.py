"""Tests for IXField platform modules (switch, number, select, climate)."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from homeassistant.const import UnitOfTemperature
from homeassistant.components.sensor import SensorDeviceClass

from custom_components.ixfield.switch import async_setup_entry as setup_switches
from custom_components.ixfield.number import async_setup_entry as setup_numbers
from custom_components.ixfield.select import async_setup_entry as setup_selects
from custom_components.ixfield.climate import async_setup_entry as setup_climate
from custom_components.ixfield.entity_helper import get_controls, create_unique_id
from .test_data import SAMPLE_DEVICE_DATA


class TestSwitchPlatform:
    """Test switch platform functionality."""

    def test_get_controls(self):
        """Test extraction of controls from device data."""
        mock_coordinator = Mock()
        mock_coordinator.data = {
            "test_device_id": SAMPLE_DEVICE_DATA
        }
        
        controls = get_controls(mock_coordinator, "test_device_id")
        
        assert len(controls) == 3  # Number of controls in test data
        
        # Check specific controls
        control_names = [control["name"] for control in controls]
        assert "filtrationState" in control_names
        assert "lightsState" in control_names
        assert "jetstreamState" in control_names

    def test_get_controls_empty_data(self):
        """Test controls extraction with empty data."""
        mock_coordinator = Mock()
        mock_coordinator.data = {}
        
        controls = get_controls(mock_coordinator, "nonexistent_device")
        assert controls == []

    @pytest.mark.asyncio
    async def test_switch_setup_entry(self):
        """Test switch setup entry."""
        mock_hass = Mock()
        mock_config_entry = Mock()
        mock_config_entry.entry_id = "test_entry"
        
        # Mock coordinator
        mock_coordinator = Mock()
        mock_coordinator.device_ids = ["test_device_id"]
        mock_coordinator.get_device_info.return_value = SAMPLE_DEVICE_DATA["data"]["device"]
        mock_coordinator.get_device_name.return_value = "Test Pool"
        mock_coordinator.data = {
            "test_device_id": SAMPLE_DEVICE_DATA
        }
        
        mock_hass.data = {
            "ixfield": {
                "test_entry": {
                    "coordinator": mock_coordinator
                }
            }
        }
        
        mock_async_add_entities = Mock()
        
        # Call setup_switches directly without patching non-existent function
        await setup_switches(mock_hass, mock_config_entry, mock_async_add_entities)
        
        # Verify entities were added
        mock_async_add_entities.assert_called_once()
        entities = mock_async_add_entities.call_args[0][0]
        
        # Should create switches for controls
        assert len(entities) > 0
        
        # Check that we have the expected switch types
        switch_names = [entity.name for entity in entities]
        assert "Circulation Pump" in switch_names
        assert "Lighting" in switch_names
        assert "Counterflow" in switch_names

    def test_switch_entity_properties(self):
        """Test switch entity properties."""
        from custom_components.ixfield.switch import IxfieldSwitch
        
        mock_coordinator = Mock()
        mock_coordinator.data = {
            "test_device_id": SAMPLE_DEVICE_DATA
        }
        mock_coordinator.last_update_success = True
        
        config = {
            "name": "Circulation Pump",
            "settable": True,
            "value": "true"
        }
        
        control = {
            "name": "filtrationState",
            "label": "Circulation Pump",
            "value": "true"
        }
        
        switch = IxfieldSwitch(
            mock_coordinator,
            "test_device_id",
            "Test Pool",
            control,
            config
        )
        
        # Test entity properties
        assert switch.name == "Circulation Pump"
        assert switch.available is True
        assert switch.is_on is True

    @pytest.mark.asyncio
    async def test_switch_turn_on(self):
        """Test switch turn on functionality."""
        from custom_components.ixfield.switch import IxfieldSwitch
        
        mock_hass = Mock()
        mock_hass.data = {}  # Empty data to avoid Mock.keys() error
        mock_coordinator = Mock()
        mock_coordinator.data = {
            "test_device_id": SAMPLE_DEVICE_DATA
        }
        mock_coordinator.last_update_success = True
        mock_coordinator.async_request_refresh = AsyncMock()
        
        # Mock the API
        mock_api = Mock()
        mock_api.async_set_control = AsyncMock(return_value=True)
        mock_coordinator.api = mock_api
        
        config = {
            "name": "Circulation Pump",
            "settable": True,
            "value": "false"
        }
        
        control = {
            "name": "filtrationState",
            "label": "Circulation Pump",
            "value": "false"
        }
        
        switch = IxfieldSwitch(
            mock_coordinator,
            "test_device_id",
            "Test Pool",
            control,
            config
        )
        switch.hass = mock_hass
        switch.entity_id = "switch.test_circulation_pump"
        
        # Test turn on
        await switch.async_turn_on()
        mock_api.async_set_control.assert_called_once_with(
            "test_device_id", "filtrationState", "ON"
        )

    @pytest.mark.asyncio
    async def test_switch_turn_off(self):
        """Test switch turn off functionality."""
        from custom_components.ixfield.switch import IxfieldSwitch
        
        mock_hass = Mock()
        mock_hass.data = {}  # Empty data to avoid Mock.keys() error
        mock_coordinator = Mock()
        mock_coordinator.data = {
            "test_device_id": SAMPLE_DEVICE_DATA
        }
        mock_coordinator.last_update_success = True
        mock_coordinator.async_request_refresh = AsyncMock()
        
        # Mock the API
        mock_api = Mock()
        mock_api.async_set_control = AsyncMock(return_value=True)
        mock_coordinator.api = mock_api
        
        config = {
            "name": "Circulation Pump",
            "settable": True,
            "value": "true"
        }
        
        control = {
            "name": "filtrationState",
            "label": "Circulation Pump",
            "value": "true"
        }
        
        switch = IxfieldSwitch(
            mock_coordinator,
            "test_device_id",
            "Test Pool",
            control,
            config
        )
        switch.hass = mock_hass
        switch.entity_id = "switch.test_circulation_pump"
        
        # Test turn off
        await switch.async_turn_off()
        mock_api.async_set_control.assert_called_once_with(
            "test_device_id", "filtrationState", "OFF"
        )


class TestNumberPlatform:
    """Test number platform functionality."""

    @pytest.mark.asyncio
    async def test_number_setup_entry(self):
        """Test number setup entry."""
        mock_hass = Mock()
        mock_config_entry = Mock()
        mock_config_entry.entry_id = "test_entry"
        
        # Mock coordinator
        mock_coordinator = Mock()
        mock_coordinator.device_ids = ["test_device_id"]
        mock_coordinator.get_device_info.return_value = SAMPLE_DEVICE_DATA["data"]["device"]
        mock_coordinator.get_device_name.return_value = "Test Pool"
        mock_coordinator.data = {
            "test_device_id": SAMPLE_DEVICE_DATA
        }
        
        mock_hass.data = {
            "ixfield": {
                "test_entry": {
                    "coordinator": mock_coordinator
                }
            }
        }
        
        mock_async_add_entities = Mock()
        
        # Call setup_numbers directly without patching non-existent function
        await setup_numbers(mock_hass, mock_config_entry, mock_async_add_entities)
        
        # Verify entities were added
        mock_async_add_entities.assert_called_once()
        entities = mock_async_add_entities.call_args[0][0]
        
        # Should create numbers for settable sensors
        assert len(entities) > 0

    def test_number_entity_properties(self):
        """Test number entity properties."""
        from custom_components.ixfield.number import IxfieldNumber
        
        mock_coordinator = Mock()
        mock_coordinator.data = {
            "test_device_id": SAMPLE_DEVICE_DATA
        }
        mock_coordinator.last_update_success = True
        
        config = {
            "name": "Water Temperature",
            "unit": UnitOfTemperature.CELSIUS,
            "settable": True,
            "min_value": 0,
            "max_value": 40,
            "step": 0.5,
            "value": "22.8"
        }
        
        number = IxfieldNumber(
            mock_coordinator,
            "test_device_id",
            "Test Pool",
            "poolTempWithSettings",
            config
        )
        
        # Test entity properties
        assert number.name == "Water Temperature"
        assert number.native_unit_of_measurement == UnitOfTemperature.CELSIUS
        assert number.native_min_value == 0
        assert number.native_max_value == 40
        assert number.native_step == 0.5
        assert number.native_value == 15.5  # Should be the desired_value, not the current value

    @pytest.mark.asyncio
    async def test_number_set_value(self):
        """Test number set value functionality."""
        from custom_components.ixfield.number import IxfieldNumber
        
        mock_hass = Mock()
        mock_hass.data = {}  # Empty data to avoid Mock.keys() error
        mock_coordinator = Mock()
        mock_coordinator.data = {
            "test_device_id": SAMPLE_DEVICE_DATA
        }
        mock_coordinator.last_update_success = True
        mock_coordinator.async_request_refresh = AsyncMock()
        
        # Mock the API
        mock_api = Mock()
        mock_api.async_set_control = AsyncMock(return_value=True)
        mock_coordinator.api = mock_api
        
        config = {
            "name": "Water Temperature",
            "unit": UnitOfTemperature.CELSIUS,
            "settable": True,
            "min_value": 0,
            "max_value": 40,
            "step": 0.5,
            "value": "22.8"
        }
        
        number = IxfieldNumber(
            mock_coordinator,
            "test_device_id",
            "Test Pool",
            "poolTempWithSettings",
            config
        )
        number.hass = mock_hass
        number.entity_id = "number.test_water_temperature"
        
        # Test set value
        await number.async_set_native_value(25.0)
        mock_api.async_set_control.assert_called_once_with(
            "test_device_id", "poolTempWithSettings", 25.0
        )


class TestSelectPlatform:
    """Test select platform functionality."""

    @pytest.mark.asyncio
    async def test_select_setup_entry(self):
        """Test select setup entry."""
        mock_hass = Mock()
        mock_config_entry = Mock()
        mock_config_entry.entry_id = "test_entry"
        
        # Mock coordinator
        mock_coordinator = Mock()
        mock_coordinator.device_ids = ["test_device_id"]
        mock_coordinator.get_device_info.return_value = SAMPLE_DEVICE_DATA["data"]["device"]
        mock_coordinator.get_device_name.return_value = "Test Pool"
        mock_coordinator.data = {
            "test_device_id": SAMPLE_DEVICE_DATA
        }
        
        mock_hass.data = {
            "ixfield": {
                "test_entry": {
                    "coordinator": mock_coordinator
                }
            }
        }
        
        mock_async_add_entities = Mock()
        
        # Call setup_selects directly without patching non-existent function
        await setup_selects(mock_hass, mock_config_entry, mock_async_add_entities)
        
        # Verify entities were added
        mock_async_add_entities.assert_called_once()
        entities = mock_async_add_entities.call_args[0][0]
        
        # Should create selects for enum sensors
        assert len(entities) > 0

    def test_select_entity_properties(self):
        """Test select entity properties."""
        from custom_components.ixfield.select import IxfieldSelect
        
        mock_coordinator = Mock()
        mock_coordinator.data = {
            "test_device_id": SAMPLE_DEVICE_DATA
        }
        mock_coordinator.last_update_success = True
        
        config = {
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
        
        select = IxfieldSelect(
            mock_coordinator,
            "test_device_id",
            "Test Pool",
            "heaterMode",
            config
        )
        
        # Test entity properties
        assert select.name == "Heating Status"
        assert select.current_option == "STANDBY"  # Should be the raw value, not the label
        assert len(select.options) == 3
        assert "COOLING" in select.options  # Should be the raw values, not the labels
        assert "HEATING" in select.options
        assert "STANDBY" in select.options

    @pytest.mark.asyncio
    async def test_select_select_option(self):
        """Test select option selection functionality."""
        from custom_components.ixfield.select import IxfieldSelect
        
        mock_hass = Mock()
        mock_hass.data = {}  # Empty data to avoid Mock.keys() error
        mock_coordinator = Mock()
        mock_coordinator.data = {
            "test_device_id": SAMPLE_DEVICE_DATA
        }
        mock_coordinator.last_update_success = True
        mock_coordinator.async_request_refresh = AsyncMock()
        
        # Mock the API
        mock_api = Mock()
        mock_api.async_set_control = AsyncMock(return_value=True)
        mock_coordinator.api = mock_api
        
        config = {
            "name": "Heating / Cooling",
            "settable": True,
            "value": "AUTO",
            "options": {
                "values": [
                    {"value": "HEATING", "label": "Heating Only"},
                    {"value": "AUTO", "label": "Heating / Cooling"},
                    {"value": "DISABLED", "label": "No Heater"}
                ]
            }
        }
        
        select = IxfieldSelect(
            mock_coordinator,
            "test_device_id",
            "Test Pool",
            "targetHeaterMode",
            config
        )
        select.hass = mock_hass
        select.entity_id = "select.test_heating_cooling"
        
        # Test select option
        await select.async_select_option("HEATING")  # Use the value, not the label
        mock_api.async_set_control.assert_called_once_with(
            "test_device_id", "targetHeaterMode", "HEATING"
        )


class TestClimatePlatform:
    """Test climate platform functionality."""

    @pytest.mark.asyncio
    async def test_climate_setup_entry(self):
        """Test climate setup entry."""
        mock_hass = Mock()
        mock_config_entry = Mock()
        mock_config_entry.entry_id = "test_entry"
        
        # Mock coordinator
        mock_coordinator = Mock()
        mock_coordinator.device_ids = ["test_device_id"]
        mock_coordinator.get_device_info.return_value = SAMPLE_DEVICE_DATA["data"]["device"]
        mock_coordinator.get_device_name.return_value = "Test Pool"
        mock_coordinator.data = {
            "test_device_id": SAMPLE_DEVICE_DATA
        }
        
        mock_hass.data = {
            "ixfield": {
                "test_entry": {
                    "coordinator": mock_coordinator
                }
            }
        }
        
        mock_async_add_entities = Mock()
        
        # Call setup_climate directly without patching non-existent function
        await setup_climate(mock_hass, mock_config_entry, mock_async_add_entities)
        
        # Verify entities were added
        mock_async_add_entities.assert_called_once()
        entities = mock_async_add_entities.call_args[0][0]
        
        # Should create climate entities for temperature control
        assert len(entities) > 0

    def test_climate_entity_properties(self):
        """Test climate entity properties."""
        from custom_components.ixfield.climate import IxfieldClimate
        
        mock_coordinator = Mock()
        mock_coordinator.data = {
            "test_device_id": SAMPLE_DEVICE_DATA
        }
        mock_coordinator.last_update_success = True
        
        config = {
            "name": "Pool Temperature",
            "unit": UnitOfTemperature.CELSIUS,
            "settable": True,
            "min_value": 0,
            "max_value": 40,
            "step": 0.5,
            "value": "22.8",
            "desired_value": "15.5"
        }
        
        climate = IxfieldClimate(
            mock_coordinator,
            "test_device_id",
            "Test Pool",
            "poolTempWithSettings",
            config,
            None
        )
        
        # Test entity properties
        assert climate.name == "Pool Temperature"
        assert climate.temperature_unit == UnitOfTemperature.CELSIUS
        assert climate.current_temperature == 22.8
        assert climate.target_temperature == 15.5
        assert climate.min_temp == 0
        assert climate.max_temp == 40
        assert climate.target_temperature_step == 0.5

    @pytest.mark.asyncio
    async def test_climate_set_temperature(self):
        """Test climate set temperature functionality."""
        from custom_components.ixfield.climate import IxfieldClimate
        
        mock_hass = Mock()
        mock_hass.data = {}  # Empty data to avoid Mock.keys() error
        mock_hass.config.units.temperature_unit = "°C"  # Mock temperature unit
        mock_coordinator = Mock()
        mock_coordinator.data = {
            "test_device_id": SAMPLE_DEVICE_DATA
        }
        mock_coordinator.last_update_success = True
        mock_coordinator.async_request_refresh = AsyncMock()
        
        # Mock the API
        mock_api = Mock()
        mock_api.async_set_control = AsyncMock(return_value=True)
        mock_coordinator.api = mock_api
        
        config = {
            "name": "Pool Temperature",
            "unit": UnitOfTemperature.CELSIUS,
            "settable": True,
            "min_value": 0,
            "max_value": 40,
            "step": 0.5,
            "value": "22.8",
            "desired_value": "15.5"
        }
        
        climate = IxfieldClimate(
            mock_coordinator,
            "test_device_id",
            "Test Pool",
            "poolTempWithSettings",
            config,
            None
        )
        climate.hass = mock_hass
        climate.entity_id = "climate.test_pool_temperature"
        
        # Test set temperature
        await climate.async_set_temperature(temperature=25.0)
        mock_api.async_set_control.assert_called_once_with(
            "test_device_id", "poolTempWithSettings", "25.0"
        )

    def test_climate_hvac_modes(self):
        """Test climate HVAC modes."""
        from custom_components.ixfield.climate import IxfieldClimate
        
        mock_coordinator = Mock()
        mock_coordinator.data = {
            "test_device_id": SAMPLE_DEVICE_DATA
        }
        mock_coordinator.last_update_success = True
        
        config = {
            "name": "Pool Temperature",
            "unit": UnitOfTemperature.CELSIUS,
            "settable": True,
            "min_value": 0,
            "max_value": 40,
            "step": 0.5,
            "value": "22.8",
            "desired_value": "15.5"
        }
        
        climate = IxfieldClimate(
            mock_coordinator,
            "test_device_id",
            "Test Pool",
            "poolTempWithSettings",
            config,
            None
        )
        
        # Test HVAC modes - the climate entity supports heat, auto, off
        assert "heat" in climate.hvac_modes
        assert "auto" in climate.hvac_modes
        assert "off" in climate.hvac_modes

    @pytest.mark.asyncio
    async def test_climate_set_hvac_mode(self):
        """Test climate set HVAC mode functionality."""
        from custom_components.ixfield.climate import IxfieldClimate
        
        mock_coordinator = Mock()
        mock_coordinator.data = {
            "test_device_id": SAMPLE_DEVICE_DATA
        }
        mock_coordinator.async_set_operating_value = Mock()
        
        config = {
            "name": "Pool Temperature",
            "unit": UnitOfTemperature.CELSIUS,
            "settable": True,
            "min_value": 0,
            "max_value": 40,
            "step": 0.5,
            "value": "22.8",
            "desired_value": "15.5"
        }
        
        climate = IxfieldClimate(
            mock_coordinator,
            "test_device_id",
            "Test Pool",
            "poolTempWithSettings",
            config,
            None
        )
        
        # Test set HVAC mode
        await climate.async_set_hvac_mode("heat")
        # This would typically set a heater mode control
        # The exact implementation depends on the climate entity logic


class TestPlatformIntegration:
    """Test integration between different platforms."""

    def test_platform_coordination(self):
        """Test that platforms work together correctly."""
        mock_coordinator = Mock()
        mock_coordinator.data = {
            "test_device_id": SAMPLE_DEVICE_DATA
        }
        
        # Test that operating values and controls are properly separated
        operating_values = SAMPLE_DEVICE_DATA["data"]["device"]["liveDeviceData"]["operatingValues"]
        controls = SAMPLE_DEVICE_DATA["data"]["device"]["liveDeviceData"]["controls"]
        
        # Operating values should be sensors/numbers/selects
        operating_value_names = [ov["name"] for ov in operating_values]
        assert "poolTempWithSettings" in operating_value_names
        assert "targetORP" in operating_value_names
        assert "targetpH" in operating_value_names
        
        # Controls should be switches
        control_names = [c["name"] for c in controls]
        assert "filtrationState" in control_names
        assert "lightsState" in control_names
        assert "jetstreamState" in control_names
        
        # There should be no overlap
        overlap = set(operating_value_names) & set(control_names)
        assert len(overlap) == 0

    def test_entity_unique_ids(self):
        """Test that entities have unique IDs across platforms."""
        from custom_components.ixfield.entity_helper import create_unique_id
        
        device_id = "test_device_id"
        
        # Test different sensor names create different unique IDs
        sensor_id = create_unique_id(device_id, "poolTempWithSettings", "sensor")
        number_id = create_unique_id(device_id, "targetORP", "number")
        switch_id = create_unique_id(device_id, "filtrationState", "switch")
        
        # All should be unique since they have different sensor names
        unique_ids = {sensor_id, number_id, switch_id}
        assert len(unique_ids) == 3
        
        # Test target entities have different IDs
        target_id = create_unique_id(device_id, "poolTempWithSettings", "sensor", is_target=True)
        assert target_id != sensor_id 