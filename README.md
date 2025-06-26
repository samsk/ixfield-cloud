# IXField Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![maintainer](https://img.shields.io/badge/maintainer-%40samsk-orange.svg)](https://github.com/samsk)
[![license](https://img.shields.io/badge/license-GPL-green.svg)](LICENSE)

A comprehensive Home Assistant integration for IXField Cloud pool and spa controllers. This integration provides full control and monitoring capabilities for IXField devices, including dynamic sensor discovery, device control, and comprehensive device information.

## Tested Devices
- PoolMatixPro

## 🏊‍♂️ Features

### Core Functionality
- **Full Device Control**: Control pumps, lighting, temperature, pH, ORP, and more
- **Real-time Monitoring**: Live sensor data and device status
- **Dynamic Sensor Discovery**: Automatically discovers and maps available sensors
- **Device Information**: Comprehensive device details including address and contact info
- **Service Sequences**: Start maintenance and calibration sequences
- **Multiple Device Support**: Manage multiple pool/spa controllers

### Entity Types
- **Sensors**: Temperature, pH, ORP, flow rates, and more
- **Numbers**: Settable values with validation
- **Selects**: Enum-based controls (modes, settings)
- **Switches**: Boolean controls (pumps, lights, valves)
- **Climate**: Temperature control with mode management
- **Device Info Sensors**: Address, contact, and company information

### Advanced Features
- **Dynamic Control System**: Configurable sensor mappings with pattern matching
- **Optimistic Updates**: Immediate UI feedback with background verification
- **Comprehensive Logging**: Detailed logging for troubleshooting
- **Error Handling**: Robust error handling and recovery
- **Type Safety**: Value validation and type checking

## 📋 Requirements

- Home Assistant 2023.8.0 or newer
- IXField Cloud account
- Internet connection for API access

## 🚀 Installation

### Option 1: HACS (Recommended)

1. Install [HACS](https://hacs.xyz/) if you haven't already
2. Add this repository as a custom repository in HACS
3. Search for "IXField" in the HACS store
4. Click "Download" and restart Home Assistant

### Option 2: Manual Installation

1. Download the `custom_components/ixfield` folder
2. Copy it to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## ⚙️ Configuration

### Initial Setup

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **IXField**
4. Enter your IXField Cloud credentials:
   - **Email**: Your IXField account email
   - **Password**: Your IXField account password
5. Select the devices you want to integrate
6. Configure device names (optional)
7. Choose whether to extract device info sensors
8. Click **Submit**

### Configuration Options

#### Device Names
You can assign custom names to your devices for easier identification:
```yaml
device_names:
  "device_id_1": "Backyard Pool"
  "device_id_2": "Spa Controller"
```

#### Extract Device Info Sensors
When enabled, creates additional sensors for:
- Device address and location
- Contact information
- Company details
- Controller information
- Connection status

## 🔧 Dynamic Control System

The integration uses a sophisticated dynamic control system that automatically discovers available sensors and maps them to user-friendly control names.

### Default Controls

| Control | Type | Description | Sensor Patterns |
|---------|------|-------------|-----------------|
| `circulation_pump` | boolean | Circulation pump | `filtrationState`, `pumpState` |
| `lighting` | boolean | Lighting control | `lightsState`, `lightingState` |
| `counterflow` | boolean | Counterflow/jets | `jetstreamState`, `counterflowState` |
| `target_temperature` | temperature | Temperature setting | `*WithSettings`, `targetTemp` |
| `target_ph` | number | pH setting | `targetpH`, `setpointpH` |
| `target_orp` | number | ORP setting | `targetORP`, `setpointORP` |
| `agent_volume` | number | Agent level | `remainingAgentA`, `agentVolume` |
| `heater_mode` | enum | Heater mode | `targetHeaterMode`, `heaterMode` |

### Custom Mappings

You can define custom control mappings for your specific devices:

```yaml
service: ixfield.ixfield_configure_control_mappings
data:
  mappings:
    ozone_generator:
      sensor_patterns: ["ozoneState", "ozoneGenerator"]
      description: "Ozone generator control"
      type: "boolean"
    custom_temp:
      sensor_patterns: ["customTempSensor", "*Temp*"]
      description: "Custom temperature control"
      type: "temperature"
      unit: "°C"
```

## 📊 Entity Naming

The integration follows Home Assistant's latest entity naming conventions:

- **Entity Names**: Only identify the data point (e.g., "Temperature", "pH")
- **Friendly Names**: Automatically generated as "Device Name + Entity Name"
- **Entity IDs**: Follow the pattern `entity_type.device_name_entity_name`

### Examples
- Device: "Backyard Pool", Entity: "Temperature" → Friendly Name: "Backyard Pool Temperature"
- Device: "Spa Controller", Entity: "pH" → Friendly Name: "Spa Controller pH"

## 🔍 Troubleshooting

### Common Issues

#### Authentication Errors
- Verify your IXField Cloud credentials
- Check that your account has access to the devices
- Ensure your internet connection is stable

#### Missing Sensors
- Use the `ixfield_get_available_controls` service to see available sensors
- Check device connection status
- Try reloading the integration

#### Control Not Working
- Verify the sensor is settable using `ixfield_get_available_controls`
- Check device connection status
- Review the logs for specific error messages

### Logging

Enable debug logging for detailed information:

```yaml
logger:
  default: info
  logs:
    custom_components.ixfield: debug
```

### Useful Services for Troubleshooting

```yaml
# Get device status
service: ixfield.ixfield_device_status
data:
  device_id: "your_device_id"

# Refresh device data
service: ixfield.ixfield_device_refresh
data:
  device_id: "your_device_id"

# Reload all sensors
service: ixfield.ixfield_reload_sensors

# Re-enumerate all sensors
service: ixfield.ixfield_reenumerate_sensors
```

## 📝 Configuration Files

### Full Configuration Example

```yaml
# configuration.yaml
ixfield:
  email: "your-email@example.com"
  password: "your-password"
  devices: "device1,device2"
  device_names:
    device1: "Backyard Pool"
    device2: "Spa Controller"
  extract_device_info_sensors: true
```

### Device Configuration

```yaml
# Example device configuration
device_dict:
  "device_id_1":
    name: "Backyard Pool"
    type: "POOL"
  "device_id_2":
    name: "Spa Controller"
    type: "SPA"
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the GPL License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- IXField for providing the API
- Home Assistant community for inspiration and support
- Contributors and testers

## 📞 Support

If you need help with this integration:

1. Check the [troubleshooting section](#troubleshooting)
2. Review the [Home Assistant logs](https://www.home-assistant.io/docs/tools/logging/)
3. Open an issue on GitHub with:
   - Home Assistant version
   - Integration version
   - Error messages from logs
   - Steps to reproduce the issue

## 🔄 Changelog

### Version 1.0.0
- Initial release
- Full device control and monitoring
- Dynamic sensor discovery
- Comprehensive device information
- Service sequences support
- Multiple entity types (sensors, numbers, selects, switches, climate)

### Version 1.1.0
- Dynamic control system with pattern matching
- User-configurable control mappings
- Enhanced error handling and validation
- Improved entity naming conventions
- Additional services for device management

---

**Note**: This integration is not affiliated with IXfield or IXsolve. It is a community-developed integration for Home Assistant. 