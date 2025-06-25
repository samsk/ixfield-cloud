# IXField Device Information Display

This document explains how device information like address, contact details, and other metadata is now displayed in the IXField Home Assistant integration.

## Overview

The IXField integration now automatically creates sensors that display comprehensive device information, making it easy to see address, contact details, and other device metadata directly in Home Assistant.

## Device Information Sensors

The integration automatically creates the following sensors for each device:

### Address Information
- **Device Address**: Full street address
- **Device City**: City name
- **Device Postal Code**: Postal/ZIP code

### Contact Information
- **Device Contact Name**: Contact person's name
- **Device Contact Email**: Contact email address
- **Device Contact Phone**: Contact phone number

### Company Information
- **Device Company**: Company name

### Device Status
- **Device Connection Status**: Current connection status
- **Device Operating Mode**: Current operating mode
- **Device In Operation Since**: When the device started operating

## How to View Device Information

### Method 1: Device Card
1. Go to **Settings** → **Devices & Services**
2. Find your IXField device
3. Click on the device to view its card
4. Scroll down to see all the device information sensors

### Method 2: Developer Tools
1. Go to **Developer Tools** → **Services**
2. Select `ixfield.get_device_info` service
3. Enter your device ID in the `device_id` field
4. Click **Call Service**
5. Check the Home Assistant logs for detailed information

### Method 3: Dashboards
Add the device information sensors to your dashboards:
1. Edit your dashboard
2. Add a new card
3. Select the device information sensors you want to display
4. Customize the card layout as needed

## Example Device Information

When you call the `ixfield.get_device_info` service, you'll see output like this in the logs:

```
=== Device Information for Pool Controller (device123) ===
Device Type: PoolController
Controller: PoolControllerV2
Connection Status: CONNECTED
Operating Mode: AUTO
In Operation Since: 2024-01-15T08:30:00Z

=== Address Information ===
Address: 123 Main Street
City: Example City
Postal Code: 12345
Coordinates: 40.7128, -74.0060

=== Contact Information ===
Contact Name: John Doe
Contact Email: john@example.com
Contact Phone: +1234567890

=== Company Information ===
Company: Example Pool Company
Company ID: comp123
```

## Sensor Icons

Each device information sensor has a relevant icon:
- 📍 Device Address: `mdi:map-marker`
- 🏙️ Device City: `mdi:city`
- 📮 Device Postal Code: `mdi:mailbox`
- 👤 Device Contact Name: `mdi:account`
- 📧 Device Contact Email: `mdi:email`
- 📞 Device Contact Phone: `mdi:phone`
- 🏢 Device Company: `mdi:office-building`
- 📶 Device Connection Status: `mdi:wifi`
- ⚙️ Device Operating Mode: `mdi:cog`
- 🕐 Device In Operation Since: `mdi:clock-start`

## Automation Examples

You can use device information sensors in automations:

### Example 1: Notify when device goes offline
```yaml
automation:
  - alias: "Notify when IXField device goes offline"
    trigger:
      platform: state
      entity_id: sensor.device_connection_status
      to: "DISCONNECTED"
    action:
      - service: notify.mobile_app
        data:
          title: "IXField Device Offline"
          message: "Device {{ states('sensor.device_address') }} in {{ states('sensor.device_city') }} is offline"
```

### Example 2: Contact device owner
```yaml
automation:
  - alias: "Contact device owner for maintenance"
    trigger:
      platform: time
      at: "09:00:00"
    condition:
      - condition: state
        entity_id: sensor.device_connection_status
        state: "DISCONNECTED"
    action:
      - service: notify.email
        data:
          target: "{{ states('sensor.device_contact_email') }}"
          title: "Device Maintenance Required"
          message: "Your device at {{ states('sensor.device_address') }} needs attention"
```

## Configuration

No additional configuration is required. Device information sensors are automatically created when:
1. The integration is set up
2. Device information is available from the IXField API
3. The coordinator refreshes device data

## Troubleshooting

### Sensors Not Appearing
If device information sensors are not appearing:
1. Check that the device has address/contact information in the IXField system
2. Verify the integration is properly configured
3. Check the Home Assistant logs for any errors
4. Try calling the `ixfield.get_device_info` service to see what data is available

### Missing Information
If some information is missing:
1. The information may not be available in the IXField API
2. Check the device configuration in the IXField web interface
3. Contact your IXField service provider to add missing information

## Benefits

1. **Easy Access**: All device information is available as sensors
2. **Automation Ready**: Use device information in automations and scripts
3. **Dashboard Integration**: Add device information to your dashboards
4. **Contact Management**: Easy access to contact details for maintenance
5. **Location Awareness**: Know where each device is located
6. **Status Monitoring**: Track device connection and operating status

## Notes

- Device information sensors are read-only
- Values are updated when the coordinator refreshes data
- Sensors only appear if the corresponding information is available
- All sensors are associated with the device and appear in the device card 