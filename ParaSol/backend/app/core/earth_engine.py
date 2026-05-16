import ee

_initialized = False


def init_ee():
    global _initialized

    if _initialized:
        return

    ee.Initialize(project="parasol-496423")
    _initialized = True