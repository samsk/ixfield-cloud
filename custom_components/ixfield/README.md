# IXField Cloud Home Assistant Integration

This custom component integrates IXField Cloud pool devices with Home Assistant.

## Features
- Login to ixfield.com with email and password (Amazon Cognito IDP)
- Create sensors for pool device data
- Supports multiple devices
- **NEW: Interactive Device Dashboard** - Comprehensive monitoring and control interface
- Real-time device status monitoring
- Interactive controls for device settings
- Service sequence management
- Event monitoring and alerts

## Installation
1. Copy the `ixfield` folder to your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## Configuration
Go to Settings > Devices & Services > Add Integration > IXField Cloud.

You will need:
- Your IXField email
- Your IXField password
- A comma-separated list of device IDs (see your IXField account)

## Device Data
The integration fetches device data using the GetDevice GraphQL API, including:
- Water temperature, pH, ORP, salinity, signal, etc.
- Device controls (circulation pump, lighting, counterflow)
- Pool properties and configuration

## Dashboard

### Interactive Device Dashboard
The integration now includes a comprehensive dashboard for monitoring and controlling your IXField devices:

- **Real-time Monitoring**: Live status updates, connection monitoring, and operating values
- **Interactive Controls**: Toggle switches, numeric inputs, and dropdown selectors for device settings
- **Service Sequences**: One-click activation of maintenance and calibration sequences
- **Event Monitoring**: Real-time alerts and event detection
- **Responsive Design**: Works on desktop, tablet, and mobile devices

### Using the Dashboard
1. **Import Dashboard**: Copy the contents of `dashboard.yaml` and import it into Lovelace
2. **Custom Card**: Use the `ixfield-dashboard-card` in your Lovelace dashboards
3. **Services**: Use the new dashboard services for automation and scripting

For detailed dashboard documentation, see [DASHBOARD_README.md](DASHBOARD_README.md).

### Dashboard Services
- `ixfield.get_dashboard_data` - Get comprehensive device data
- `ixfield.set_dashboard_control` - Set device control values
- `ixfield.refresh_dashboard` - Refresh all device data

## Reference
See `specification.md` for the full API request/response and device data structure. 