import ee
import json
import os

_initialized = False

def init_ee():
    global _initialized

    if _initialized:
        return

    service_account_json = os.getenv("EE_SERVICE_ACCOUNT_JSON")

    if not service_account_json:
        raise ValueError("EE_SERVICE_ACCOUNT_JSON no está definido")

    credentials_dict = json.loads(service_account_json)

    credentials = ee.ServiceAccountCredentials(
        credentials_dict["client_email"],
        service_account_json  # <- AQUÍ está el fix clave
    )

    ee.Initialize(credentials)

    _initialized = True