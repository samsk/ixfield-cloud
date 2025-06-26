# Device Info Sensors Configuration

## Overview

The IXField integration now includes an optional configuration setting to control whether device information sensors are extracted and created.

## Configuration Option

### `extract_device_info_sensors` (boolean, default: true)

This option controls whether the integration creates additional sensors for device information such as:
- Device address and location
- Contact information
- Company information
- Controller details
- Connection status
- Operating mode
- Operation start time

## Usage

### During Initial Setup

When setting up the integration for the first time, you can choose whether to extract device info sensors:

```yaml
# Example configuration
email: "your-email@example.com"
password: "your-password"
devices: "device1,device2"
device_names: '{"device1": "Pool Controller", "device2": "Garden System"}'
extract_device_info_sensors: true  # or false
```

### In Options

You can change this setting later through the integration options:

1. Go to **Settings** > **Devices & Services**
2. Find your IXField integration and click **Configure**
3. Update the **Extract Device Info Sensors** option
4. Click **Submit**

## Device Info Sensors Created

When enabled, the following sensors are created for each device:

### Address Information
- `device_address` - Full device address
- `device_address_city` - City where device is located
- `device_address_postal_code` - Postal code
- `device_address_location` - GPS coordinates (if available)

### Contact Information
- `device_contact_name` - Contact person name
- `device_contact_email` - Contact email address
- `device_contact_phone` - Contact phone number

### Device Information
- `device_company` - Company name
- `device_controller` - Controller type/version
- `device_connection_status` - Current connection status
- `device_operating_mode` - Operating mode
- `device_in_operation_since` - When device started operating

## Benefits

### When Enabled (default)
- Provides comprehensive device information
- Useful for monitoring device status and location
- Helps with device management and troubleshooting
- All sensors are diagnostic category for proper grouping

### When Disabled
- Reduces the number of entities created
- May improve performance for large installations
- Useful when device info is not needed or already available elsewhere

## Notes

- All device info sensors are read-only (diagnostic category)
- They update automatically when device information changes
- The setting can be changed at any time through the options flow
- Changes require a reload of the integration to take effect 