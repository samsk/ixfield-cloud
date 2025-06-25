# IXField Device Info Usage Guide

The IXField coordinator now includes comprehensive device information functionality that makes it easy to access device details across all components.

## Overview

The coordinator automatically extracts and caches device information from the API response, providing easy access to:

- Basic device information (name, type, controller, etc.)
- Address and location data
- Contact information
- Company details
- Device status and configuration
- Live data summaries

## Usage Examples

### Basic Device Information

```python
# Get all device info for a specific device
device_info = coordinator.get_device_info(device_id)

# Get just the device name
device_name = coordinator.get_device_name(device_id)

# Get device type
device_type = coordinator.get_device_type(device_id)
```

### Address and Location

```python
# Get full address information
address = coordinator.get_device_address(device_id)
# Returns: {
#   "id": "...",
#   "address": "123 Main St",
#   "city": "Example City",
#   "postal_code": "12345",
#   "lat": 40.7128,
#   "lng": -74.0060,
#   ...
# }
```

### Contact Information

```python
# Get contact details
contact = coordinator.get_device_contact(device_id)
# Returns: {
#   "name": "John Doe",
#   "phone": "+1234567890",
#   "email": "john@example.com",
#   "note": "Contact note"
# }
```

### Company Information

```python
# Get company details
company = coordinator.get_device_company(device_id)
# Returns: {
#   "id": "...",
#   "name": "Example Company",
#   "uses_new_eligibility_system": true
# }
```

### Status Summary

```python
# Get a comprehensive status summary
status = coordinator.get_device_status_summary(device_id)
# Returns: {
#   "name": "Pool Controller",
#   "type": "PoolController",
#   "connection_status": "CONNECTED",
#   "operating_mode": "AUTO",
#   "controls_enabled": true,
#   "in_operation_since": "2024-01-01T00:00:00Z",
#   "address": "123 Main St",
#   "city": "Example City"
# }

# Get status for all devices
all_status = coordinator.get_all_devices_status()
```

### Complete Device Info Structure

The complete device info structure includes:

```python
{
    "id": "device_id",
    "name": "Device Name",
    "type": "DeviceType",
    "controller": "ControllerType",
    "operating_mode": "AUTO",
    "in_operation_since": "2024-01-01T00:00:00Z",
    "connection_status": "CONNECTED",
    "connection_status_changed": "2024-01-01T00:00:00Z",
    "controls_enabled": true,
    "controls_override_enabled": false,
    "control_override_start": null,
    "configuration_in_progress": false,
    "data_propagation_failed": false,
    "need_propagate_device_data": false,
    "grafana_link": "https://grafana.example.com/...",
    
    "thing_type": {
        "name": "ThingTypeName",
        "business_name": "Business Name",
        "family": "ThingTypeFamily"
    },
    
    "address": {
        "id": "address_id",
        "address": "123 Main St",
        "code": "CODE",
        "city": "Example City",
        "lat": 40.7128,
        "lng": -74.0060,
        "approximate_lat": 40.7128,
        "approximate_lng": -74.0060,
        "place_id": "place_id",
        "postal_code": "12345"
    },
    
    "contact_info": {
        "name": "Contact Name",
        "phone": "+1234567890",
        "email": "contact@example.com",
        "note": "Contact note"
    },
    
    "company": {
        "id": "company_id",
        "name": "Company Name",
        "uses_new_eligibility_system": true
    },
    
    "live_data_summary": {
        "running_service_sequence": "ServiceSequenceName",
        "operating_values_count": 10,
        "controls_count": 5,
        "service_sequences_count": 3,
        "tabs_count": 2,
        "event_detection_points_count": 1,
        "user_access_count": 2,
        "eligibilities_count": 1
    },
    
    "user_access": [
        {
            "id": "access_id",
            "custom_device_name": "Custom Name",
            "type": "AccessType"
        }
    ]
}
```

## Integration in Components

### In Sensor Components

```python
class IxfieldSensor(CoordinatorEntity):
    def __init__(self, coordinator, device_id, device_name, value, meta, value_name, base_sensor_name):
        super().__init__(coordinator)
        self._device_id = device_id
        # Use device info for better naming
        self._device_name = coordinator.get_device_name(device_id)
        # ... rest of initialization
```

### In Service Functions

```python
async def device_status(call: ServiceCall) -> None:
    device_id = call.data["device_id"]
    coordinator = get_coordinator_for_device(device_id)
    
    # Get comprehensive device info
    device_info = coordinator.get_device_info(device_id)
    status_summary = coordinator.get_device_status_summary(device_id)
    
    # Use the information as needed
    _LOGGER.info(f"Device {status_summary['name']} in {status_summary['city']} is {status_summary['connection_status']}")
```

## Benefits

1. **Centralized Data**: All device information is extracted and cached in one place
2. **Easy Access**: Simple methods to get specific information
3. **Consistent Format**: Standardized data structure across all components
4. **Performance**: Cached data reduces API calls and processing
5. **Maintainability**: Single source of truth for device information extraction

## Notes

- Device info is automatically updated when the coordinator refreshes data
- All methods return safe defaults if data is not available
- The device info cache is cleared and rebuilt on each coordinator update
- Debug logging is available to track device info extraction 