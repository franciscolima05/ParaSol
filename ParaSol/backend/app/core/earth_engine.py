import ee
import json
import os

_initialized = False


def init_ee():
    global _initialized

    if _initialized:
        return

    service_account_json = os.getenv("EE_SERVICE_ACCOUNT_JSON")

    if service_account_json:
        credentials_dict = json.loads(service_account_json)
        credentials = ee.ServiceAccountCredentials(
            email=credentials_dict["client_email"],
            key_data=json.dumps(credentials_dict),
        )
        ee.Initialize(credentials=credentials, project="parasol-496423")
    else:
        ee.Initialize(project="parasol-496423")

    _initialized = True