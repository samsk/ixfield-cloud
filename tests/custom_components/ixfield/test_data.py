"""Test data for IXField integration tests."""

# Anonymized device discovery response for testing
SAMPLE_DEVICE_DATA = {
    "data": {
        "device": {
            "id": "RGV3aWNlOjQ1NDQ=",
            "name": "TEST12305-24-005676 Test User",
            "type": "POOL",
            "controller": "1JQ-1EG-DYV",
            "operatingMode": "NORMAL",
            "inOperationSince": "2025-01-21T13:11:17.589Z",
            "controlsEnabled": True,
            "connectionStatus": "ONLINE",
            "connectionStatusChangedTime": "2025-06-26T10:44:27.087Z",
            "grafanaLink": "https://grafana.example.com/d/tJIKvFL4z/eledio-new?orgId=4&var-SN=5JQ-2EG-DYV",
            "needPropagateDeviceData": False,
            "isConfigurationJobInProgress": False,
            "dataPropagationFailed": False,
            "isControlsOverrideEnabled": False,
            "controlOverrideStart": None,
            "thingType": {
                "name": "sdwm002-poolmatix-pro-b",
                "businessName": "SDWM002-Poolmatix-Pro(B)",
                "thingTypeFamily": {
                    "name": "PoolmatixPro",
                    "__typename": "ThingTypeFamily"
                },
                "__typename": "ThingType"
            },
            "address": {
                "id": "QWRkcmVzczozMDQ3",
                "address": "Test Street 123, 12345 Test City, Test Country",
                "code": "test",
                "city": "Test City",
                "lat": 49.1849933,
                "lng": 18.8623812,
                "approximateLat": 49.186283835555344,
                "approximateLng": 18.86721308691927,
                "placeId": "ChIJ35SZ1l5XFEcR7xtTzImpC0Q",
                "postalCode": "12345",
                "__typename": "Address"
            },
            "contactInfo": {
                "name": "Test User",
                "phone": "+1234567890",
                "email": "test.user@example.com",
                "note": "",
                "__typename": "ContactInfo"
            },
            "company": {
                "id": "Q33tcGFueToxMA==",
                "name": "Test Company",
                "usesNewEligibilitySystem": False,
                "__typename": "Company"
            },
            "newProduct": {
                "id": "TmV3UHJzZHGjdDoxMDkx",
                "__typename": "NewProduct"
            },
            "liveDeviceData": {
                "runningServiceSequence": None,
                "operatingValues": [
                    {
                        "type": "NUMBER",
                        "name": "poolTempWithSettings",
                        "label": "Water Temperature",
                        "icon": None,
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
                        "settable": True,
                        "buttonText": None,
                        "buttonIcon": None,
                        "setEligibility": None,
                        "statusLabel": None,
                        "statusIcon": None,
                        "__typename": "Control",
                        "validFor": 3600
                    },
                    {
                        "type": "NUMBER",
                        "name": "targetORP",
                        "label": "ORP",
                        "icon": None,
                        "value": "645",
                        "desiredValue": "650",
                        "options": {
                            "digits": 0,
                            "min": 100,
                            "max": 800,
                            "step": 10
                        },
                        "showDesired": True,
                        "settable": True,
                        "buttonText": None,
                        "buttonIcon": None,
                        "setEligibility": None,
                        "statusLabel": None,
                        "statusIcon": None,
                        "__typename": "Control",
                        "validFor": 3600
                    },
                    {
                        "type": "NUMBER",
                        "name": "targetpH",
                        "label": "pH",
                        "icon": None,
                        "value": "7.3",
                        "desiredValue": "7.25",
                        "options": {
                            "min": 7,
                            "max": 8,
                            "step": 0.05,
                            "digits": 2,
                            "minVisible": 4.5,
                            "maxVisible": 8.5
                        },
                        "showDesired": True,
                        "settable": True,
                        "buttonText": None,
                        "buttonIcon": None,
                        "setEligibility": None,
                        "statusLabel": None,
                        "statusIcon": None,
                        "__typename": "Control",
                        "validFor": 3600
                    },
                    {
                        "type": "NUMBER",
                        "name": "remainingAgentA",
                        "label": "Agent A / pH-",
                        "icon": None,
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
                        "settable": True,
                        "buttonText": None,
                        "buttonIcon": None,
                        "setEligibility": None,
                        "statusLabel": None,
                        "statusIcon": None,
                        "__typename": "Control",
                        "validFor": 3600
                    },
                    {
                        "type": "NUMBER",
                        "name": "salinity",
                        "label": "Salinity",
                        "icon": None,
                        "value": "0.42",
                        "desiredValue": None,
                        "options": {
                            "unit": "PERCENT",
                            "digits": 2,
                            "minVisible": 0.1,
                            "maxVisible": 1.2
                        },
                        "showDesired": False,
                        "settable": False,
                        "buttonText": None,
                        "buttonIcon": None,
                        "setEligibility": None,
                        "statusLabel": None,
                        "statusIcon": None,
                        "__typename": "Control",
                        "validFor": 3600
                    },
                    {
                        "type": "NUMBER",
                        "name": "ambientTemperature",
                        "label": "Ambient Temperature",
                        "icon": None,
                        "value": "25",
                        "desiredValue": None,
                        "options": {
                            "unit": "TEMP_CELSIUS",
                            "digits": 1
                        },
                        "showDesired": False,
                        "settable": False,
                        "buttonText": None,
                        "buttonIcon": None,
                        "setEligibility": None,
                        "statusLabel": None,
                        "statusIcon": None,
                        "__typename": "Control",
                        "validFor": 3600
                    },
                    {
                        "type": "NUMBER",
                        "name": "signal",
                        "label": "Signal Strength",
                        "icon": None,
                        "value": "50",
                        "desiredValue": None,
                        "options": {
                            "unit": "PERCENT",
                            "digits": 0
                        },
                        "showDesired": False,
                        "settable": False,
                        "buttonText": None,
                        "buttonIcon": None,
                        "setEligibility": None,
                        "statusLabel": None,
                        "statusIcon": None,
                        "__typename": "Control",
                        "validFor": 3600
                    },
                    {
                        "type": "ENUM",
                        "name": "heaterMode",
                        "label": "Heating Status",
                        "icon": None,
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
                        "settable": False,
                        "buttonText": None,
                        "buttonIcon": None,
                        "setEligibility": None,
                        "statusLabel": None,
                        "statusIcon": None,
                        "__typename": "Control",
                        "validFor": None
                    },
                    {
                        "type": "ENUM",
                        "name": "targetHeaterMode",
                        "label": "Heating / Cooling",
                        "icon": None,
                        "value": "AUTO",
                        "desiredValue": "AUTO",
                        "options": {
                            "values": [
                                {"value": "HEATING", "label": "Heating Only"},
                                {"value": "AUTO", "label": "Heating / Cooling"},
                                {"value": "DISABLED", "label": "No Heater"}
                            ]
                        },
                        "showDesired": True,
                        "settable": True,
                        "buttonText": None,
                        "buttonIcon": None,
                        "setEligibility": None,
                        "statusLabel": None,
                        "statusIcon": None,
                        "__typename": "Control",
                        "validFor": None
                    },
                    {
                        "type": "ENUM",
                        "name": "connectionType",
                        "label": "Internet Connectivity",
                        "icon": None,
                        "value": "wifi",
                        "desiredValue": None,
                        "options": {
                            "values": [
                                {"value": "mobile", "label": "Mobile"},
                                {"value": "wifi", "label": "Wi-Fi"},
                                {"value": "ethernet", "label": "Ethernet Cable"}
                            ]
                        },
                        "showDesired": False,
                        "settable": False,
                        "buttonText": None,
                        "buttonIcon": None,
                        "setEligibility": None,
                        "statusLabel": None,
                        "statusIcon": None,
                        "__typename": "Control",
                        "validFor": None
                    }
                ],
                "controls": [
                    {
                        "type": "TOGGLE",
                        "name": "filtrationState",
                        "label": "Circulation Pump",
                        "icon": "filter",
                        "value": "true",
                        "desiredValue": None,
                        "options": {},
                        "showDesired": False,
                        "settable": True,
                        "buttonText": None,
                        "buttonIcon": None,
                        "setEligibility": None,
                        "statusLabel": None,
                        "statusIcon": None,
                        "__typename": "Control",
                        "forbiddenByUser": False,
                        "forbiddenByTechnology": False
                    },
                    {
                        "type": "TOGGLE",
                        "name": "lightsState",
                        "label": "Lighting",
                        "icon": "bulb",
                        "value": "false",
                        "desiredValue": None,
                        "options": {},
                        "showDesired": False,
                        "settable": True,
                        "buttonText": None,
                        "buttonIcon": None,
                        "setEligibility": None,
                        "statusLabel": None,
                        "statusIcon": None,
                        "__typename": "Control",
                        "forbiddenByUser": False,
                        "forbiddenByTechnology": False
                    },
                    {
                        "type": "TOGGLE",
                        "name": "jetstreamState",
                        "label": "Counterflow",
                        "icon": "air-flow",
                        "value": "false",
                        "desiredValue": None,
                        "options": {},
                        "showDesired": False,
                        "settable": True,
                        "buttonText": None,
                        "buttonIcon": None,
                        "setEligibility": None,
                        "statusLabel": None,
                        "statusIcon": None,
                        "__typename": "Control",
                        "forbiddenByUser": False,
                        "forbiddenByTechnology": False
                    }
                ],
                "serviceSequences": [
                    {
                        "type": "SERVICE_SEQUENCE",
                        "name": "dosingPumpA",
                        "label": "Manual Dosing - Dosing Pump A / pH-",
                        "icon": "two-drops",
                        "value": None,
                        "desiredValue": None,
                        "options": {},
                        "showDesired": False,
                        "settable": False,
                        "buttonText": None,
                        "buttonIcon": None,
                        "setEligibility": None,
                        "statusLabel": None,
                        "statusIcon": None,
                        "__typename": "Control",
                        "forbiddenByUser": False,
                        "forbiddenByTechnology": False
                    }
                ]
            },
            "eventDetectionPoints": [],
            "userAccess": {
                "id": "VXNlckRldmljZUFjY2Vzczo0Njk3",
                "customDeviceName": "Test Pool",
                "type": "DEVICE_ADMIN",
                "__typename": "UserDeviceAccess"
            },
            "eligibilities": {
                "setTargetPh": True,
                "setTargetFCI": True,
                "setTargetORP": True,
                "uvLampSequence": False,
                "displaySalinity": True,
                "besgoValveBackwash": False,
                "changeOperatingMode": True,
                "coolingTestSequence": False,
                "heatingTestSequence": False,
                "waterRefillSequence": False,
                "mainPumpOnlySequence": True,
                "mainPumpTestSequence": True,
                "setTargetTemperature": True,
                "configurationFormPool": True,
                "dosingServiceSequences": True,
                "flowSensorTestSequence": False,
                "setRemainingAgentVolume": True,
                "configurationFormHeating": True,
                "displayAmbientTemperature": True,
                "orpProbeCalibrationSequence": True,
                "configurationFormConnections": False,
                "displayReturnWaterTemperature": False,
                "chlorinatorWithMainPumpSequence": False,
                "configurationFormFilterBackwash": False,
                "configurationFormWaterLevelTank": True,
                "configurationFormWaterTreatment": True,
                "fclElectrodeCalibrationSequence": True,
                "skimmerWaterLevelSensorSequence": False,
                "configurationFormCirculationPump": False,
                "configurationFormPoolAccessories": False,
                "orpProbeOffsetCalibrationSequence": True,
                "phProbeOnePointCalibrationSequence": True,
                "phProbeTwoPointCalibrationSequence": True,
                "demoMode": True,
                "eventCodes": True,
                "galleryEdit": False,
                "galleryView": False,
                "deviceControl": True,
                "serviceHistory": False,
                "eventCoreCauses": True,
                "timeScheduleEdit": True,
                "operationCounters": False,
                "deviceConfiguration": False,
                "orderServiceFromApp": False,
                "timeScheduleSelection": True,
                "eventCorrectiveActions": True,
                "notificationDispatcher": True,
                "orderServiceFromAppFromEvent": True
            },
            "__typename": "Device"
        }
    }
}

# Expected sensor configurations for testing
EXPECTED_SENSOR_CONFIGS = {
    "poolTempWithSettings": {
        "name": "Water Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "settable": True,
        "show_desired": True,
        "min_value": 0,
        "max_value": 40,
        "step": 0.5,
        "value": "22.8",
        "desired_value": "15.5"
    },
    "targetORP": {
        "name": "ORP",
        "unit": None,
        "device_class": None,
        "settable": False,
        "show_desired": True,
        "min_value": 100,
        "max_value": 800,
        "step": 10,
        "value": "645",
        "desired_value": "650"
    },
    "targetpH": {
        "name": "pH",
        "unit": None,
        "device_class": None,
        "settable": False,
        "show_desired": True,
        "min_value": 7,
        "max_value": 8,
        "step": 0.05,
        "value": "7.3",
        "desired_value": "7.25"
    },
    "remainingAgentA": {
        "name": "Agent A / pH-",
        "unit": "L",
        "device_class": "volume",
        "settable": False,
        "show_desired": False,
        "min_value": 0,
        "max_value": 60,
        "step": 0.1,
        "value": "7.809",
        "desired_value": None
    },
    "salinity": {
        "name": "Salinity",
        "unit": "%",
        "device_class": None,
        "settable": False,
        "show_desired": False,
        "value": "0.42",
        "desired_value": None
    },
    "ambientTemperature": {
        "name": "Ambient Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "settable": False,
        "show_desired": False,
        "value": "25",
        "desired_value": None
    },
    "signal": {
        "name": "Signal Strength",
        "unit": "%",
        "device_class": None,
        "settable": False,
        "show_desired": False,
        "value": "50",
        "desired_value": None
    }
}

# Expected control configurations for testing
EXPECTED_CONTROL_CONFIGS = {
    "filtrationState": {
        "name": "Circulation Pump",
        "type": "TOGGLE",
        "settable": True,
        "value": "true"
    },
    "lightsState": {
        "name": "Lighting",
        "type": "TOGGLE",
        "settable": True,
        "value": "false"
    },
    "jetstreamState": {
        "name": "Counterflow",
        "type": "TOGGLE",
        "settable": True,
        "value": "false"
    }
} 