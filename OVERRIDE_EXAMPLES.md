# IXField Integration Override Examples

This guide shows how to override sensor names, device types, and other properties in the IXField integration.

## Overview

The integration provides override maps in each platform file that allow you to customize:
- **Sensor names** (human-friendly display names)
- **Units** (temperature, percentage, etc.)
- **Device classes** (temperature, humidity, etc.)
- **Settable properties** (min/max values, step size)
- **Binary sensor on/off values**
- **Switch names**

## How to Override

### 1. Find the Sensor/Control Name

First, you need to find the exact name of the sensor or control from the API. You can do this by:
- Checking the Home Assistant logs when the integration loads
- Looking at the unique IDs of entities in Home Assistant
- Using the developer tools to inspect the API response

### 2. Edit the Override Maps

Each platform has its own override map:

#### Sensors (`sensor.py` - `SENSOR_MAP`)

```python
SENSOR_MAP = {
    # Override a temperature sensor
    "poolTempWithSettings": {
        "name": "Pool Temperature",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "settable": True,
        "min_value": 10,
        "max_value": 40,
        "step": 0.5
    },
    
    # Override a mode sensor
    "heaterMode": {
        "name": "Heater Status",
        "unit": None,
        "device_class": None
    },
    
    # Override target sensor (for settable sensors)
    "poolTempWithSettings.desired": {
        "name": "Target Pool Temperature",
        "settable": True,
        "min_value": 10,
        "max_value": 40,
        "step": 0.5
    }
}
```

#### Switches (`switch.py` - `SWITCH_MAP`)

```python
SWITCH_MAP = {
    "filtrationState": {
        "name": "Circulation Pump"
    },
    "lightsState": {
        "name": "Pool Lighting"
    },
    "jetstreamState": {
        "name": "Counterflow System"
    }
}
```

#### Binary Sensors (`binary_sensor.py` - `BINARY_SENSOR_MAP`)

```python
BINARY_SENSOR_MAP = {
    "heaterMode": {
        "name": "Heater Status",
        "on_value": "HEATING"
    },
    "filtrationState": {
        "name": "Filtration Active",
        "on_value": "true"
    }
}
```

## Available Properties

### For Sensors (`SENSOR_MAP`)

| Property | Type | Description |
|----------|------|-------------|
| `name` | string | Human-friendly display name |
| `unit` | string | Unit of measurement (e.g., "°C", "%") |
| `device_class` | SensorDeviceClass | Home Assistant device class |
| `settable` | boolean | Whether the sensor can be set |
| `min_value` | number | Minimum value for settable sensors |
| `max_value` | number | Maximum value for settable sensors |
| `step` | number | Step size for settable sensors |

### For Switches (`SWITCH_MAP`)

| Property | Type | Description |
|----------|------|-------------|
| `name` | string | Human-friendly display name |

### For Binary Sensors (`BINARY_SENSOR_MAP`)

| Property | Type | Description |
|----------|------|-------------|
| `name` | string | Human-friendly display name |
| `on_value` | string | Value that indicates "on" state |

## Common Device Classes

```python
from homeassistant.components.sensor import SensorDeviceClass

# Temperature sensors
SensorDeviceClass.TEMPERATURE

# Humidity sensors
SensorDeviceClass.HUMIDITY

# Pressure sensors
SensorDeviceClass.PRESSURE

# Power sensors
SensorDeviceClass.POWER

# Energy sensors
SensorDeviceClass.ENERGY

# Current sensors
SensorDeviceClass.CURRENT

# Voltage sensors
SensorDeviceClass.VOLTAGE

# Frequency sensors
SensorDeviceClass.FREQUENCY

# None (for custom sensors)
None
```

## Common Units

```python
from homeassistant.const import UnitOfTemperature

# Temperature
UnitOfTemperature.CELSIUS
UnitOfTemperature.FAHRENHEIT
UnitOfTemperature.KELVIN

# Other common units
"%"          # Percentage
"bar"        # Pressure
"L/min"      # Flow rate
"rpm"        # Speed
"pH"         # pH value
"mV"         # Millivolts
"Hz"         # Frequency
"W"          # Power
"kWh"        # Energy
"A"          # Current
"V"          # Voltage
```

## Examples

### Example 1: Customize Pool Temperature Sensor

```python
SENSOR_MAP = {
    "poolTempWithSettings": {
        "name": "Pool Water Temperature",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "settable": True,
        "min_value": 15,
        "max_value": 35,
        "step": 0.5
    }
}
```

### Example 2: Customize Heater Binary Sensor

```python
BINARY_SENSOR_MAP = {
    "heaterMode": {
        "name": "Pool Heater Active",
        "on_value": "HEATING"
    }
}
```

### Example 3: Customize Filtration Switch

```python
SWITCH_MAP = {
    "filtrationState": {
        "name": "Pool Filtration System"
    }
}
```

### Example 4: Customize Target Temperature Sensor

```python
SENSOR_MAP = {
    "poolTempWithSettings.desired": {
        "name": "Desired Pool Temperature",
        "settable": True,
        "min_value": 15,
        "max_value": 35,
        "step": 0.5
    }
}
```

## After Making Changes

1. **Restart Home Assistant** or reload the integration
2. **Check the logs** for any errors
3. **Verify the changes** in the Home Assistant UI

## Tips

- **Use exact sensor names** from the API (case-sensitive)
- **Test with one override at a time** to avoid conflicts
- **Check the logs** if overrides don't work as expected
- **Backup your changes** before making modifications
- **Use descriptive names** that make sense in your setup

## Troubleshooting

### Override Not Working?
- Check that the sensor name is exactly correct (case-sensitive)
- Ensure the override map syntax is correct
- Restart Home Assistant after making changes
- Check the logs for any errors

### Can't Find Sensor Name?
- Enable debug logging for the integration
- Check the unique IDs of entities in Home Assistant
- Look at the API response in the browser developer tools 