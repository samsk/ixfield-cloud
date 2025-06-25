# IXField Device Naming System

This document describes the device naming system implemented in the IXField Home Assistant integration.

## Overview

The IXField integration now supports intelligent device naming that:
- Uses device types to construct default names
- Supports user-defined custom names
- Automatically adds increasing digits for multiple devices of the same type
- Provides consistent entity naming across all platforms

## How It Works

### Default Naming (Based on Device Type)

When no custom names are provided, the system automatically constructs device names based on the device type:

- **Single device of a type**: Uses the device type as the name
  - Example: `Pool Controller` → `pool_controller`
  - Example: `Garden System` → `garden_system`

- **Multiple devices of the same type**: Adds increasing digits
  - Example: 3 Pool Controllers → `pool_controller1`, `pool_controller2`, `pool_controller3`

### User-Defined Names

Users can override the default naming by providing a JSON mapping of device IDs to custom names in the configuration.

**Configuration Format:**
```json
{
  "device_id_1": "Custom Name 1",
  "device_id_2": "Custom Name 2"
}
```

**Example:**
```json
{
  "abc123": "Backyard Pool",
  "def456": "Front Garden System"
}
```

### Entity Naming

Entities (sensors, switches, etc.) are named using the pattern:
- `{device_name}_{entity_type}_{entity_id}`

**Examples:**
- `pool_controller_sensor_temperature`
- `backyard_pool_switch_pump`
- `garden_system_climate_heater`

## Configuration

### Initial Setup

During the initial configuration, you can provide device names in the "Device Names" field:

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration** → **IXField Cloud**
3. Enter your credentials and device IDs
4. In the "Device Names" field, optionally enter a JSON mapping:
   ```json
   {
     "device1": "Pool Controller",
     "device2": "Garden System"
   }
   ```

### Updating Configuration

To update device names after initial setup:

1. Go to **Settings** → **Devices & Services**
2. Find your IXField Cloud integration
3. Click **Configure**
4. Select **Update Device Configuration**
5. Modify the "Device Names" field as needed

## Examples

### Scenario 1: Single Pool Controller
- **Device Type**: Pool Controller
- **Default Name**: `pool_controller`
- **Entities**: 
  - `pool_controller_sensor_temperature`
  - `pool_controller_switch_pump`

### Scenario 2: Multiple Pool Controllers
- **Device Types**: Pool Controller (3 devices)
- **Default Names**: `pool_controller1`, `pool_controller2`, `pool_controller3`
- **Entities**:
  - `pool_controller1_sensor_temperature`
  - `pool_controller2_sensor_temperature`
  - `pool_controller3_sensor_temperature`

### Scenario 3: Mixed Device Types with Custom Names
- **Devices**: 2 Pool Controllers, 1 Garden System
- **Custom Names**: `{"device1": "Backyard Pool", "device3": "Front Garden"}`
- **Resulting Names**:
  - `device1`: `Backyard Pool` (custom)
  - `device2`: `pool_controller2` (auto-generated)
  - `device3`: `Front Garden` (custom)

## Fallback Behavior

If device information is not available during initialization:
- User-defined names are still applied if provided
- Device IDs are used as fallback names
- Names are updated once device information becomes available

## Technical Implementation

The naming system is implemented in the `IxfieldCoordinator` class with the following key methods:

- `_construct_device_names()`: Builds the device name mapping
- `get_device_name(device_id)`: Returns the name for a specific device
- `get_entity_name(device_id, entity_type, entity_id)`: Returns the name for an entity

The system automatically reconstructs names when device information is updated, ensuring consistency across the integration. 