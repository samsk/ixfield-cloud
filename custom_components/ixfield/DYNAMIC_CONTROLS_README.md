# IXField Dynamic Controls System

## Overview

The IXField integration now uses a dynamic control system that automatically discovers available sensors and maps them to user-friendly control names. This replaces the previous hardcoded sensor mappings with a flexible, configurable system.

## Key Features

### 1. **Automatic Sensor Discovery**
- The system automatically discovers all available sensors on each device
- No need to hardcode sensor names for different device types
- Supports multiple sensor naming patterns and conventions

### 2. **Flexible Pattern Matching**
- **Exact matches**: Direct sensor name matching
- **Wildcard patterns**: Use `*WithSettings` to match any sensor ending with "WithSettings"
- **Fuzzy matching**: Case-insensitive partial name matching
- **Multiple patterns**: Each control can have multiple sensor patterns to try

### 3. **User-Configurable Mappings**
- Users can define custom control mappings
- Override default mappings for specific devices
- Add new controls for custom sensors

### 4. **Type-Safe Validation**
- Automatic validation of control values based on type
- Temperature range validation (-50°C to 100°C)
- Boolean value normalization
- Unit conversion support

## Default Control Mappings

The system includes sensible defaults for common pool/spa controls:

| Control Name | Sensor Patterns | Type | Description |
|--------------|----------------|------|-------------|
| `circulation_pump` | `["filtrationState", "pumpState", "circulationState"]` | boolean | Circulation pump control |
| `lighting` | `["lightsState", "lightingState", "lightState"]` | boolean | Lighting control |
| `counterflow` | `["jetstreamState", "counterflowState", "jetsState"]` | boolean | Counterflow/jet stream control |
| `target_temperature` | `["*WithSettings", "targetTemp", "setpointTemp"]` | temperature | Target temperature setting |
| `target_orp` | `["targetORP", "setpointORP", "orpSetpoint"]` | number | Target ORP setting |
| `target_ph` | `["targetpH", "setpointpH", "phSetpoint"]` | number | Target pH setting |
| `agent_volume` | `["remainingAgentA", "agentVolume", "agentLevel"]` | number | Agent volume/level |
| `heater_mode` | `["targetHeaterMode", "heaterMode", "heatingMode"]` | enum | Heater mode setting |

## Usage

### 1. **Basic Device Control**

Use the existing `ixfield_device_control` service with the same interface:

```yaml
service: ixfield.ixfield_device_control
data:
  device_id: "your_device_id"
  controls:
    circulation_pump: true
    target_temperature: 25.5
    lighting: false
```

### 2. **Discover Available Controls**

Use the new `ixfield_get_available_controls` service to see what controls are available for your device:

```yaml
service: ixfield.ixfield_get_available_controls
data:
  device_id: "your_device_id"
```

This will return information about all available controls, including:
- Sensor names
- Current values
- Whether they're settable
- Control types and units

### 3. **Configure Custom Mappings**

Use the `ixfield_configure_control_mappings` service to add custom controls:

```yaml
service: ixfield.ixfield_configure_control_mappings
data:
  mappings:
    custom_pump:
      sensor_patterns: ["myCustomPump", "pumpControl"]
      description: "Custom pump control"
      type: "boolean"
    custom_temp:
      sensor_patterns: ["customTempSensor", "*Temp*"]
      description: "Custom temperature control"
      type: "temperature"
      unit: "°C"
```

## Pattern Matching Examples

### Wildcard Patterns

```python
# Matches any sensor ending with "WithSettings"
"*WithSettings"  # Matches: poolTempWithSettings, spaTempWithSettings

# Matches any sensor starting with "target"
"target*"        # Matches: targetORP, targetpH, targetTemp

# Matches any sensor containing "pump"
"*pump*"         # Matches: circulationPump, mainPump, pumpState
```

### Multiple Patterns

```python
"circulation_pump": {
    "sensor_patterns": [
        "filtrationState",      # Exact match
        "pumpState",           # Exact match
        "*circulation*"        # Wildcard match
    ]
}
```

## Control Types

### Boolean Controls
- **Values**: `true`/`false`, `"true"`/`"false"`, `"on"`/`"off"`, `"1"`/`"0"`
- **API Format**: Always converted to `"true"`/`"false"`
- **Examples**: Pumps, lights, valves

### Temperature Controls
- **Values**: Numeric values in Celsius
- **Validation**: Range -50°C to 100°C
- **Examples**: Pool temperature, spa temperature

### Number Controls
- **Values**: Any numeric value
- **Validation**: Must be convertible to float
- **Examples**: pH, ORP, flow rates

### Enum Controls
- **Values**: String values from predefined options
- **Validation**: Based on sensor's available options
- **Examples**: Heater modes, operating modes

## Error Handling

The system provides comprehensive error handling:

1. **Control Not Available**: Logs warning and skips the control
2. **Invalid Value**: Logs error and skips the control
3. **Sensor Not Settable**: Logs warning and skips the control
4. **API Call Failed**: Logs error and reports failure

All errors are collected and reported in the service response.

## Configuration Persistence

### Current Implementation
- User mappings are stored in memory during runtime
- Mappings are lost on Home Assistant restart
- Default mappings are always available

### Future Enhancements
- Store user mappings in configuration files
- Per-device mapping overrides
- Import/export mapping configurations

## Migration from Hardcoded System

### What Changed
- **Before**: Hardcoded sensor names like `"poolTempWithSettings"`
- **After**: Dynamic discovery with pattern matching

### What Stayed the Same
- Service interface remains identical
- Control names remain the same
- Error handling and logging

### Benefits
- **Flexibility**: Works with any device type
- **Maintainability**: No code changes needed for new sensors
- **User Control**: Users can customize mappings
- **Robustness**: Better error handling and validation

## Troubleshooting

### Control Not Found
1. Use `ixfield_get_available_controls` to see available sensors
2. Check sensor names in device data
3. Add custom mapping with correct sensor patterns

### Value Validation Errors
1. Check control type in mapping
2. Ensure value is in correct format
3. Verify value is within valid range

### API Call Failures
1. Check if sensor is settable
2. Verify device connection
3. Check API response for specific errors

## Examples

### Example 1: Standard Pool Control
```yaml
service: ixfield.ixfield_device_control
data:
  device_id: "pool_controller_123"
  controls:
    circulation_pump: true
    target_temperature: 26.0
    lighting: true
    counterflow: false
```

### Example 2: Custom Control Mapping
```yaml
# First, configure custom mapping
service: ixfield.ixfield_configure_control_mappings
data:
  mappings:
    ozone_generator:
      sensor_patterns: ["ozoneState", "ozoneGenerator"]
      description: "Ozone generator control"
      type: "boolean"

# Then use the custom control
service: ixfield.ixfield_device_control
data:
  device_id: "pool_controller_123"
  controls:
    ozone_generator: true
```

### Example 3: Discover and Use Available Controls
```yaml
# Get available controls
service: ixfield.ixfield_get_available_controls
data:
  device_id: "pool_controller_123"

# Use discovered controls based on the response
service: ixfield.ixfield_device_control
data:
  device_id: "pool_controller_123"
  controls:
    target_temperature: 25.5
    target_ph: 7.4
```

## Advanced Configuration

### Custom Sensor Patterns
```python
# Example of complex pattern matching
"advanced_pump": {
    "sensor_patterns": [
        "mainPumpState",           # Exact match
        "*pump*state*",           # Wildcard pattern
        "circulation*",           # Prefix match
        "filtration"              # Simple match
    ],
    "description": "Advanced pump control with multiple patterns",
    "type": "boolean"
}
```

### Type-Specific Validation
```python
# Custom validation for specific controls
"custom_flow_rate": {
    "sensor_patterns": ["flowRate", "waterFlow"],
    "description": "Custom flow rate control",
    "type": "number",
    "unit": "L/min",
    "validation": {
        "min": 0,
        "max": 100,
        "step": 0.5
    }
}
```

This dynamic control system provides much greater flexibility and maintainability compared to the previous hardcoded approach, while maintaining backward compatibility with existing automation and scripts. 