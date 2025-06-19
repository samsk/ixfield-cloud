import aiohttp
import asyncio
import logging
from warrant import Cognito

_LOGGER = logging.getLogger(__name__)

COGNITO_AUTH_URL = "https://cognito-idp.eu-central-1.amazonaws.com/"
COGNITO_CLIENT_ID = "5489vt8bvntn3v95tdt2nngq0r"
GRAPHQL_URL = "https://to2gjdst4h.execute-api.eu-central-1.amazonaws.com/prod/"
USER_POOL_ID = "eu-central-1_jCOzBXuR0"

class IxfieldApi:
    def __init__(self, email, password, session):
        self._email = email
        self._password = password
        self._session = session
        self._token = None

    async def async_login(self):
        loop = asyncio.get_event_loop()
        def do_auth():
            u = Cognito(USER_POOL_ID, COGNITO_CLIENT_ID, username=self._email)
            u.authenticate(password=self._password)
            return u.access_token
        self._token = await loop.run_in_executor(None, do_auth)
        if not self._token:
            _LOGGER.error("No access token in Cognito response (warrant)")
            raise Exception("No access token in Cognito response (warrant)")

    async def async_get_device(self, device_id):
        headers = {
            "Content-Type": "application/json",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        payload = {
            "operationName": "GetDevice",
            "variables": {
                "directAccessView": True,
                "id": device_id,
                "lang": "en",
                "withFullCustomerData": True,
                "withRestrictedCustomerData": True,
                "withGrafanaLink": True
            },
            "query": "query GetDevice($id: ID!, $lang: String!, $withFullCustomerData: Boolean!, $withRestrictedCustomerData: Boolean!, $withGrafanaLink: Boolean!, $directAccessView: Boolean! = false) { device(deviceId: $id) { id name type controller operatingMode inOperationSince controlsEnabled connectionStatus connectionStatusChangedTime grafanaLink @include(if: $withGrafanaLink) needPropagateDeviceData isConfigurationJobInProgress dataPropagationFailed isControlsOverrideEnabled controlOverrideStart thingType { name businessName thingTypeFamily { name __typename } __typename } address { id address @include(if: $withFullCustomerData) code @include(if: $withRestrictedCustomerData) city @include(if: $withRestrictedCustomerData) lat @include(if: $withFullCustomerData) lng @include(if: $withFullCustomerData) approximateLat @include(if: $withRestrictedCustomerData) approximateLng @include(if: $withRestrictedCustomerData) placeId @include(if: $withFullCustomerData) postalCode @include(if: $withFullCustomerData) __typename } contactInfo @include(if: $withFullCustomerData) { name phone email note __typename } company { id name usesNewEligibilitySystem __typename } newProduct { id __typename } liveDeviceData { runningServiceSequence { name requiredEligibility __typename } operatingValues(lang: $lang) { ...ControlFields validFor __typename } controls(lang: $lang) { ...ControlFields forbiddenByUser forbiddenByTechnology __typename } serviceSequences(lang: $lang) { ...ControlFields forbiddenByUser forbiddenByTechnology __typename } tabs(lang: $lang) { label type items { ... on Tab { label type items { ... on TabItem { name label type value unit options formattedValue canSetInTab __typename } __typename } __typename } ... on TabItem { name label type value unit options formattedValue canSetInTab __typename } __typename } __typename } __typename } eventDetectionPoints { eventCodes { severity description(lang: $lang) __typename } __typename } userAccess @include(if: $directAccessView) { id customDeviceName type __typename } eligibilities __typename } __typename } fragment ControlFields on Control { type name label icon value desiredValue options showDesired settable buttonText buttonIcon setEligibility statusLabel statusIcon __typename }"
        }
        async with self._session.post(GRAPHQL_URL, json=payload, headers=headers) as resp:
            if resp.status != 200:
                _LOGGER.error(f"Failed to fetch device {device_id}: {resp.status}")
                return None
            return await resp.json()

    async def async_set_control(self, device_id, control_name, value):
        headers = {
            "Content-Type": "application/json",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        payload = {
            "operationName": "SetControl",
            "variables": {
                "deviceId": device_id,
                "name": control_name,
                "value": value,
            },
            "query": "mutation SetControl($deviceId: ID!, $name: String!, $value: String!) { setControl(deviceId: $deviceId, name: $name, value: $value) { success } }"
        }
        async with self._session.post(GRAPHQL_URL, json=payload, headers=headers) as resp:
            if resp.status != 200:
                _LOGGER.error(f"Failed to set control {control_name} on {device_id}: {resp.status}")
                return False
            result = await resp.json()
            return result.get("data", {}).get("setControl", {}).get("success", False) 