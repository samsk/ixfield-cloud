# IXField Cloud Home Assistant Integration

This custom component integrates IXField Cloud pool devices with Home Assistant.

## Features
- Login to ixfield.com with email and password (Amazon Cognito IDP)
- Create sensors for pool device data
- Supports multiple devices

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

## Reference
See `specification.md` for the full API request/response and device data structure. 