import ee

_initialized = False


def init_ee():
    global _initialized

    if _initialized:
        return

    ee.Initialize(project="test-agro-496400")
    _initialized = True


def get_dem():
    # DEM solo se crea después de init
    return ee.Image("USGS/SRTMGL1_003")