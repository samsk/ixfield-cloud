"""Tests for IXField sensor enumeration and configuration."""

import pytest
from unittest.mock import Mock, patch
from homeassistant.const import UnitOfTemperature
from homeassistant.components.sensor import SensorDeviceClass

from custom_components.ixfield.sensor import (
    get_sensor_config,
    generate_human_readable_name,
    SENSOR_MAPPINGS,
    async_setup_entry,
    IxfieldSensor,
    IxfieldTargetSensor,
)
from custom_components.ixfield.entity_helper import (
    get_operating_values,
    create_unique_id,
    EntityNamingMixin,
    EntityCommonAttrsMixin,
    EntityValueMixin,
)
from .test_data import SAMPLE_DEVICE_DATA, EXPECTED_SENSOR_CONFIGS


class TestSensorEnumeration:
    """Test sensor enumeration functionality."""

    def test_generate_human_readable_name(self):
        """Test human readable name generation."""
        # Test basic camelCase conversion
        assert generate_human_readable_name("poolTempWithSettings") == "Pool Temp"
        assert generate_human_readable_name("targetORP") == "Orp"
        assert generate_human_readable_name("remainingAgentA") == "Remaining Agent A"
        
        # Test with common suffixes
        assert generate_human_readable_name("temperatureWithSettings") == "Temperature"
        assert generate_human_readable_name("targetTemperature") == "Temperature"
        
        # Test edge cases
        assert generate_human_readable_name("") == ""
        assert generate_human_readable_name("single") == "Single"
        assert generate_human_readable_name("UPPERCASE") == "Uppercase"

    def test_sensor_mappings(self):
        """Test sensor unit and device class mappings."""
        # Test temperature mappings
        assert SENSOR_MAPPINGS["TEMP_CELSIUS"] == (UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE)
        assert SENSOR_MAPPINGS["TEMP_FAHRENHEIT"] == (UnitOfTemperature.FAHRENHEIT, SensorDeviceClass.TEMPERATURE)
        
        # Test volume mappings
        assert SENSOR_MAPPINGS["LITER"] == ("L", SensorDeviceClass.VOLUME)
        
        # Test percentage mappings
        assert SENSOR_MAPPINGS["PERCENT"] == ("%", None)
        
        # Test power mappings
        assert SENSOR_MAPPINGS["POWER"] == ("W", SensorDeviceClass.POWER)
        
        # Test fallback mappings
        assert SENSOR_MAPPINGS["STRING"] == (None, None)

    def test_get_sensor_config_temperature(self):
        """Test sensor configuration for temperature sensors."""
        sensor_data = {
            "type": "NUMBER",
            "name": "poolTempWithSettings",
            "label": "Water Temperature",
            "value": "22.8",
            "desiredValue": "15.5",
            "options": {
                "unit": "TEMP_CELSIUS",
                "min": 0,
                "max": 40,
                "step": 0.5,
                "digits": 1
            },
            "showDesired": True,
            "settable": True
        }
        
        config = get_sensor_config("poolTempWithSettings", sensor_data)
        
        assert config["name"] == "Water Temperature"
        assert config["unit"] == UnitOfTemperature.CELSIUS
        assert config["device_class"] == SensorDeviceClass.TEMPERATURE
        assert config["settable"] is True
        assert config["show_desired"] is True
        assert config["min_value"] == 0
        assert config["max_value"] == 40
        assert config["step"] == 0.5
        assert config["value"] == "22.8"
        assert config["desired_value"] == "15.5"

    def test_get_sensor_config_ph(self):
        """Test sensor configuration for pH sensors."""
        sensor_data = {
            "type": "NUMBER",
            "name": "targetpH",
            "label": "pH",
            "value": "7.3",
            "desiredValue": "7.25",
            "options": {
                "min": 7,
                "max": 8,
                "step": 0.05,
                "digits": 2
            },
            "showDesired": True,
            "settable": True
        }
        
        config = get_sensor_config("targetpH", sensor_data)
        
        assert config["name"] == "pH"
        assert config["unit"] is None  # pH has no unit
        assert config["device_class"] is None
        assert config["settable"] is False  # Override makes it non-settable
        assert config["show_desired"] is True
        assert config["min_value"] == 7
        assert config["max_value"] == 8
        assert config["step"] == 0.05
        assert config["value"] == "7.3"
        assert config["desired_value"] == "7.25"

    def test_get_sensor_config_volume(self):
        """Test sensor configuration for volume sensors."""
        sensor_data = {
            "type": "NUMBER",
            "name": "remainingAgentA",
            "label": "Agent A / pH-",
            "value": "7.809",
            "desiredValue": None,
            "options": {
                "unit": "LITER",
                "min": 0,
                "max": 60,
                "step": 0.1,
                "digits": 1
            },
            "showDesired": False,
            "settable": True
        }
        
        config = get_sensor_config("remainingAgentA", sensor_data)
        
        assert config["name"] == "Agent A / pH-"
        assert config["unit"] == "L"
        assert config["device_class"] == SensorDeviceClass.VOLUME
        assert config["settable"] is False  # Override makes it non-settable
        assert config["show_desired"] is False
        assert config["min_value"] == 0
        assert config["max_value"] == 60
        assert config["step"] == 0.1
        assert config["value"] == "7.809"
        assert config["desired_value"] is None

    def test_get_sensor_config_enum(self):
        """Test sensor configuration for enum sensors."""
        sensor_data = {
            "type": "ENUM",
            "name": "heaterMode",
            "label": "Heating Status",
            "value": "STANDBY",
            "desiredValue": None,
            "options": {
                "values": [
                    {"value": "COOLING", "label": "Cooling"},
                    {"value": "HEATING", "label": "Heating"},
                    {"value": "STANDBY", "label": "Standby"}
                ]
            },
            "showDesired": False,
            "settable": False
        }
        
        config = get_sensor_config("heaterMode", sensor_data)
        
        assert config["name"] == "Heating Status"
        assert config["unit"] is None
        assert config["device_class"] is None
        assert config["settable"] is False
        assert config["show_desired"] is False
        assert config["value"] == "STANDBY"
        assert config["desired_value"] is None
        assert "options" in config

    def test_get_sensor_config_fallback(self):
        """Test sensor configuration fallback for unknown units."""
        sensor_data = {
            "type": "NUMBER",
            "name": "unknownSensor",
            "label": "Unknown Sensor",
            "value": "123",
            "desiredValue": None,
            "options": {
                "unit": "UNKNOWN_UNIT",
                "min": 0,
                "max": 100
            },
            "showDesired": False,
            "settable": False
        }
        
        config = get_sensor_config("unknownSensor", sensor_data)
        
        # Should fallback to STRING mapping
        assert config["name"] == "Unknown Sensor"
        assert config["unit"] is None
        assert config["device_class"] is None

    def test_get_operating_values(self):
        """Test extraction of operating values from device data."""
        mock_coordinator = Mock()
        mock_coordinator.data = {
            "test_device_id": SAMPLE_DEVICE_DATA
        }
        
        operating_values = get_operating_values(mock_coordinator, "test_device_id")
        
        assert len(operating_values) == 10  # Number of operating values in test data
        
        # Check specific sensors
        sensor_names = [sensor["name"] for sensor in operating_values]
        assert "poolTempWithSettings" in sensor_names
        assert "targetORP" in sensor_names
        assert "targetpH" in sensor_names
        assert "remainingAgentA" in sensor_names

    def test_get_operating_values_empty_data(self):
        """Test operating values extraction with empty data."""
        mock_coordinator = Mock()
        mock_coordinator.data = {}
        
        operating_values = get_operating_values(mock_coordinator, "nonexistent_device")
        assert operating_values == []

    def test_create_unique_id(self):
        """Test unique ID creation."""
        device_id = "test_device_123"
        sensor_name = "poolTempWithSettings"
        platform = "sensor"
        
        # Test regular unique ID
        unique_id = create_unique_id(device_id, sensor_name, platform)
        assert unique_id == f"{device_id}_{sensor_name}"
        
        # Test target unique ID
        target_unique_id = create_unique_id(device_id, sensor_name, platform, is_target=True)
        assert target_unique_id == f"{device_id}_{sensor_name}_target"

    @pytest.mark.asyncio
    async def test_async_setup_entry(self):
        """Test sensor setup entry."""
        mock_hass = Mock()
        mock_config_entry = Mock()
        mock_config_entry.entry_id = "test_entry"
        
        # Mock coordinator
        mock_coordinator = Mock()
        mock_coordinator.device_ids = ["test_device_id"]
        mock_coordinator.get_device_info.return_value = SAMPLE_DEVICE_DATA["data"]["device"]
        mock_coordinator.get_device_name.return_value = "Test Pool"
        mock_coordinator.should_extract_device_info_sensors.return_value = False
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
        
        # Mock sensor_config to skip certain sensors
        with patch("custom_components.ixfield.sensor.should_skip_sensor_for_platform", return_value=False):
            await async_setup_entry(mock_hass, mock_config_entry, mock_async_add_entities)
        
        # Verify entities were added
        mock_async_add_entities.assert_called_once()
        entities = mock_async_add_entities.call_args[0][0]
        
        # Should create sensors for operating values
        assert len(entities) > 0
        
        # Check that we have the expected sensor types
        sensor_names = [entity.name for entity in entities]
        assert "Water Temperature" in sensor_names
        assert "ORP" in sensor_names
        assert "pH" in sensor_names

    def test_ixfield_sensor_entity(self):
        """Test IxfieldSensor entity creation and properties."""
        mock_coordinator = Mock()
        mock_coordinator.data = {
            "test_device_id": SAMPLE_DEVICE_DATA
        }
        mock_coordinator.last_update_success = True  # Mock the last_update_success property
        
        config = {
            "name": "Water Temperature",
            "unit": UnitOfTemperature.CELSIUS,
            "device_class": SensorDeviceClass.TEMPERATURE,
            "settable": True,
            "show_desired": True,
            "value": "22.8",
            "desired_value": "15.5"
        }
        
        sensor = IxfieldSensor(
            mock_coordinator,
            "test_device_id",
            "Test Pool",
            "poolTempWithSettings",
            config
        )
        
        # Test entity properties
        assert sensor.name == "Water Temperature"
        assert sensor.native_unit_of_measurement == UnitOfTemperature.CELSIUS
        assert sensor.device_class == SensorDeviceClass.TEMPERATURE
        assert sensor.available is True
        
        # Test value retrieval
        assert sensor.native_value == 22.8  # Should be float, not string

    def test_ixfield_target_sensor_entity(self):
        """Test IxfieldTargetSensor entity creation and properties."""
        mock_coordinator = Mock()
        mock_coordinator.data = {
            "test_device_id": SAMPLE_DEVICE_DATA
        }
        mock_coordinator.last_update_success = True  # Mock the last_update_success property
        
        config = {
            "name": "Water Temperature",
            "unit": UnitOfTemperature.CELSIUS,
            "device_class": SensorDeviceClass.TEMPERATURE,
            "settable": True,
            "show_desired": True,
            "value": "22.8",
            "desired_value": "15.5"
        }
        
        target_sensor = IxfieldTargetSensor(
            mock_coordinator,
            "test_device_id",
            "Test Pool",
            "poolTempWithSettings",
            config
        )
        
        # Test entity properties
        assert target_sensor.name == "Water Temperature Target"
        assert target_sensor.native_unit_of_measurement == UnitOfTemperature.CELSIUS
        assert target_sensor.device_class == SensorDeviceClass.TEMPERATURE
        assert target_sensor.available is True
        
        # Test value retrieval (should return desired value)
        assert target_sensor.native_value == 15.5  # Should be float, not string

    def test_entity_naming_mixin(self):
        """Test EntityNamingMixin functionality."""
        class TestEntity(EntityNamingMixin):
            pass
        
        entity = TestEntity()
        entity.setup_entity_naming(
            "Test Pool",
            "poolTempWithSettings",
            "sensor",
            "Water Temperature",
            is_target=False
        )
        
        assert entity._attr_has_entity_name is True
        assert entity._attr_name == "Water Temperature"
        assert entity._device_name == "Test Pool"
        assert entity._sensor_name == "poolTempWithSettings"
        assert entity._platform == "sensor"
        assert entity._is_target is False

    def test_entity_common_attrs_mixin(self):
        """Test EntityCommonAttrsMixin functionality."""
        class TestEntity(EntityCommonAttrsMixin):
            pass
        
        entity = TestEntity()
        config = {
            "device_class": SensorDeviceClass.TEMPERATURE,
            "unit": UnitOfTemperature.CELSIUS,
            "options": {
                "values": [
                    {"value": "ON", "label": "On"},
                    {"value": "OFF", "label": "Off"}
                ]
            }
        }
        
        entity.set_common_attrs(config, "select")
        
        assert entity._attr_device_class == SensorDeviceClass.TEMPERATURE
        assert entity._attr_native_unit_of_measurement == UnitOfTemperature.CELSIUS

    def test_entity_value_mixin(self):
        """Test EntityValueMixin functionality."""
        class TestEntity(EntityValueMixin):
            pass
        
        entity = TestEntity()
        entity._device_id = "test_device_id"
        entity._sensor_name = "poolTempWithSettings"
        
        mock_coordinator = Mock()
        mock_coordinator.data = {
            "test_device_id": SAMPLE_DEVICE_DATA
        }
        entity.coordinator = mock_coordinator
        
        # Test sensor value retrieval
        value = entity.get_sensor_value("poolTempWithSettings")
        assert value == 22.8  # Should be float, not string
        
        # Test with fallback
        value = entity.get_sensor_value("nonexistent", fallback_value="default")
        assert value == "default"

    def test_sensor_configuration_comprehensive(self):
        """Test comprehensive sensor configuration for all sensor types in test data."""
        operating_values = SAMPLE_DEVICE_DATA["data"]["device"]["liveDeviceData"]["operatingValues"]
        
        for sensor_data in operating_values:
            sensor_name = sensor_data["name"]
            config = get_sensor_config(sensor_name, sensor_data)
            
            # Basic validation
            assert "name" in config
            assert "unit" in config
            assert "device_class" in config
            assert "settable" in config
            assert "show_desired" in config
            assert "value" in config
            
            # Check against expected configurations
            if sensor_name in EXPECTED_SENSOR_CONFIGS:
                expected = EXPECTED_SENSOR_CONFIGS[sensor_name]
                assert config["name"] == expected["name"]
                assert config["unit"] == expected["unit"]
                assert config["device_class"] == expected["device_class"]
                assert config["settable"] == expected["settable"]
                assert config["show_desired"] == expected["show_desired"]
                assert config["value"] == expected["value"]
                assert config["desired_value"] == expected["desired_value"] 