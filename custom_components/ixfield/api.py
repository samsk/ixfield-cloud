import aiohttp
import asyncio
import boto3
import logging
from typing import Any, Dict, Optional
from pycognito.aws_srp import AWSSRP

_LOGGER = logging.getLogger(__name__)

COGNITO_AUTH_URL = "https://cognito-idp.eu-central-1.amazonaws.com/"
COGNITO_CLIENT_ID = "5489vt8bvntn3v95tdt2nngq0r"
GRAPHQL_URL = "https://to2gjdst4h.execute-api.eu-central-1.amazonaws.com/prod/"
USER_POOL_ID = "eu-central-1_jCOzBXuR0"
AWS_REGION = "eu-central-1"


class IxfieldApi:
    def __init__(
        self, email: str, password: str, session: aiohttp.ClientSession
    ) -> None:
        self._email = email
        self._password = password
        self._session = session
        self._token: Optional[str] = None

    async def async_login(self) -> None:
        """Authenticate using pycognito.aws_srp.AWSSRP for proper SRP handling"""
        loop = asyncio.get_event_loop()

        def do_auth() -> str:
            try:
                _LOGGER.info(f"Attempting SRP authentication for user: {self._email}")
                client = boto3.client("cognito-idp", region_name=AWS_REGION)
                aws = AWSSRP(
                    username=self._email,
                    password=self._password,
                    pool_id=USER_POOL_ID,
                    client_id=COGNITO_CLIENT_ID,
                    client=client,
                )
                tokens = aws.authenticate_user()
                _LOGGER.info("SRP authentication successful")
                return tokens["AuthenticationResult"]["AccessToken"]
            except Exception as e:
                _LOGGER.error(f"SRP authentication error: {e}")
                raise e

        self._token = await loop.run_in_executor(None, do_auth)
        if not self._token:
            _LOGGER.error("No access token in SRP authentication response")
            raise Exception("No access token in SRP authentication response")

    async def async_get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
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
                "withGrafanaLink": True,
            },
            "query": "query GetDevice($id: ID!, $lang: String!, $withFullCustomerData: Boolean!, $withRestrictedCustomerData: Boolean!, $withGrafanaLink: Boolean!, $directAccessView: Boolean! = false) { device(deviceId: $id) { id name type controller operatingMode inOperationSince controlsEnabled connectionStatus connectionStatusChangedTime grafanaLink @include(if: $withGrafanaLink) needPropagateDeviceData isConfigurationJobInProgress dataPropagationFailed isControlsOverrideEnabled controlOverrideStart thingType { name businessName thingTypeFamily { name __typename } __typename } address { id address @include(if: $withFullCustomerData) code @include(if: $withRestrictedCustomerData) city @include(if: $withRestrictedCustomerData) lat @include(if: $withFullCustomerData) lng @include(if: $withFullCustomerData) approximateLat @include(if: $withRestrictedCustomerData) approximateLng @include(if: $withRestrictedCustomerData) placeId @include(if: $withFullCustomerData) postalCode @include(if: $withFullCustomerData) __typename } contactInfo @include(if: $withFullCustomerData) { name phone email note __typename } company { id name usesNewEligibilitySystem __typename } newProduct { id __typename } liveDeviceData { runningServiceSequence { name requiredEligibility __typename } operatingValues(lang: $lang) { ...ControlFields validFor __typename } controls(lang: $lang) { ...ControlFields forbiddenByUser forbiddenByTechnology __typename } serviceSequences(lang: $lang) { ...ControlFields forbiddenByUser forbiddenByTechnology __typename } tabs(lang: $lang) { label type items { ... on Tab { label type items { ... on TabItem { name label type value unit options formattedValue canSetInTab __typename } __typename } __typename } ... on TabItem { name label type value unit options formattedValue canSetInTab __typename } __typename } __typename } __typename } eventDetectionPoints { eventCodes { severity description(lang: $lang) __typename } __typename } userAccess @include(if: $directAccessView) { id customDeviceName type __typename } eligibilities __typename } __typename } fragment ControlFields on Control { type name label icon value desiredValue options showDesired settable buttonText buttonIcon setEligibility statusLabel statusIcon __typename }",
        }
        _LOGGER.debug(f"Making API request for device {device_id}")
        async with self._session.post(
            GRAPHQL_URL, json=payload, headers=headers
        ) as resp:
            _LOGGER.debug(f"API response status for device {device_id}: {resp.status}")
            if resp.status != 200:
                _LOGGER.error(f"Failed to fetch device {device_id}: {resp.status}")
                response_text = await resp.text()
                _LOGGER.error(f"Response body: {response_text}")
                return None
            response_data = await resp.json()
            _LOGGER.debug(f"API response data for device {device_id}: {response_data}")
            return response_data

    async def async_set_control(
        self, device_id: str, control_name: str, value: Any, set_desired: bool = False
    ) -> bool:
        headers = {
            "Content-Type": "application/json",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        # Use the correct mutation format as provided in the example
        payload = {
            "variables": {
                "data": {"deviceId": device_id, "name": control_name, "value": value}
            },
            "query": "mutation ($data: ControlDeviceInput!) {\n  deviceControl(input: $data) {\n    success\n    __typename\n  }\n}",
        }

        _LOGGER.debug(
            f"Setting control {control_name} to {value} on device {device_id}"
        )
        async with self._session.post(
            GRAPHQL_URL, json=payload, headers=headers
        ) as resp:
            if resp.status != 200:
                _LOGGER.error(
                    f"Failed to set control {control_name} on {device_id}: {resp.status}"
                )
                response_text = await resp.text()
                _LOGGER.error(f"Response body: {response_text}")
                return False
            result = await resp.json()
            _LOGGER.debug(f"Control set response: {result}")
            success = (
                result.get("data", {}).get("deviceControl", {}).get("success", False)
            )
            if success:
                _LOGGER.info(
                    f"Successfully set control {control_name} to {value} on device {device_id}"
                )
            else:
                _LOGGER.error(
                    f"API returned failure for setting control {control_name} to {value} on device {device_id}"
                )
            return success

    async def async_get_user_devices(self) -> Optional[Dict[str, Any]]:
        """Get all user devices using the GetUserDevices query."""
        headers = {
            "Content-Type": "application/json",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        payload = {
            "operationName": "GetUserDevices",
            "variables": {
                "pageNumber": 1,
                "withCompanyName": True,
                "withCustomName": True,
                "withAddress": False,
                "type": "POOL",
                "companyId": None,
                "searchText": "",
                "connectionStatus": None,
                "withEvents": None,
                "lang": "en",
            },
            "query": 'query GetUserDevices($type: DeviceTypeEnum!, $companyId: ID, $searchText: String, $pageNumber: Int! = 1, $connectionStatus: Boolean, $withEvents: Boolean, $withCompanyName: Boolean! = false, $withCustomName: Boolean! = false, $withAddress: Boolean! = false, $lang: String!) {\n  me {\n    id\n    devices(\n      type: $type\n      companyId: $companyId\n      searchText: $searchText\n      pageNumber: $pageNumber\n      connectionStatus: $connectionStatus\n      withEvents: $withEvents\n    ) {\n      id\n      name\n      connectionType: paramByName(name: "connectionType", lang: $lang) {\n        formattedValue\n        __typename\n      }\n      customName @include(if: $withCustomName)\n      controller\n      operatingMode\n      connectionStatus\n      connectionStatusChangedTime\n      company @include(if: $withCompanyName) {\n        id\n        name\n        __typename\n      }\n      eventDetectionPoints {\n        eventCodes {\n          severity\n          description(lang: $lang)\n          __typename\n        }\n        __typename\n      }\n      address @include(if: $withAddress) {\n        lat\n        lng\n        approximateLat\n        approximateLng\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n',
        }

        _LOGGER.debug("Making API request to get user devices")
        async with self._session.post(
            GRAPHQL_URL, json=payload, headers=headers
        ) as resp:
            _LOGGER.debug(f"GetUserDevices API response status: {resp.status}")
            if resp.status != 200:
                _LOGGER.error(f"Failed to fetch user devices: {resp.status}")
                response_text = await resp.text()
                _LOGGER.error(f"Response body: {response_text}")
                return None
            response_data = await resp.json()
            _LOGGER.debug(f"GetUserDevices API response data: {response_data}")
            return response_data
