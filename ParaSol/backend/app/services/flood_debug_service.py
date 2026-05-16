import ee

from app.core.logger import logger


SENTINEL1_COLLECTION = "COPERNICUS/S1_GRD"


def _count(collection):
    """Count seguro contra errores en colecciones vacías."""
    try:
        return collection.size().getInfo()
    except Exception as e:
        logger.warning("error contando coleccion: %s", e)
        return None


def _scene_details(collection, limit=50):
    """
    Lista las primeras N escenas con sus metadatos clave. Nos permite ver
    qué hay disponible (fechas, orbit, polarisation, resolution, mode).
    """
    def per_image(image):
        return ee.Feature(None, {
            "id": image.id(),
            "date": image.date().format("YYYY-MM-dd"),
            "orbit": image.get("orbitProperties_pass"),
            "mode": image.get("instrumentMode"),
            "polarisations": image.get("transmitterReceiverPolarisation"),
            "resolution": image.get("resolution_meters"),
            "relative_orbit": image.get("relativeOrbitNumber_start"),
        })

    try:
        features = (
            collection
            .limit(limit)
            .map(per_image)
            .getInfo()["features"]
        )
        return [f["properties"] for f in features]
    except Exception as e:
        logger.warning("error listando escenas: %s", e)
        return []


def debug_s1_coverage(data):
    """
    Diagnostico: para el polígono + ventana, cuenta cuántas escenas
    matchean cada filtro acumulado y muestra el detalle de las escenas
    que llegan al final.

    Permite ver exactamente qué filtro está cortando escenas y por qué.
    """
    logger.info("debug S1 coverage")

    geometry = ee.Geometry.Polygon(data.polygon.coordinates)
    start = data.start_date
    end = data.end_date

    # Filtros acumulados
    base = ee.ImageCollection(SENTINEL1_COLLECTION).filterBounds(geometry)
    with_dates = base.filterDate(start, end)
    with_iw = with_dates.filter(ee.Filter.eq("instrumentMode", "IW"))
    with_vv = with_iw.filter(
        ee.Filter.listContains("transmitterReceiverPolarisation", "VV")
    )
    with_10m = with_vv.filter(ee.Filter.eq("resolution_meters", 10))

    asc = with_10m.filter(ee.Filter.eq("orbitProperties_pass", "ASCENDING"))
    desc = with_10m.filter(ee.Filter.eq("orbitProperties_pass", "DESCENDING"))

    # Mirando con menos filtros para detectar qué cae
    counts = {
        "1_bbox_only": _count(base),
        "2_bbox_plus_dates": _count(with_dates),
        "3_plus_mode_IW": _count(with_iw),
        "4_plus_polarisation_VV": _count(with_vv),
        "5_plus_resolution_10m": _count(with_10m),
        "6a_ASCENDING": _count(asc),
        "6b_DESCENDING": _count(desc),
    }

    # Resoluciones presentes en la colección con fechas y bbox aplicados
    try:
        resolutions = (
            with_iw
            .aggregate_array("resolution_meters")
            .distinct()
            .getInfo()
        )
    except Exception:
        resolutions = []

    # Modos presentes (algunas zonas reciben EW además de IW)
    try:
        modes = (
            with_dates
            .aggregate_array("instrumentMode")
            .distinct()
            .getInfo()
        )
    except Exception:
        modes = []

    return {
        "status": "ok",
        "polygon_bbox": geometry.bounds().coordinates().getInfo(),
        "window": {"start_date": start, "end_date": end},
        "counts_by_filter": counts,
        "filter_pipeline": [
            "1. filterBounds(polygon)",
            "2. filterDate(start, end)",
            "3. filter mode == IW",
            "4. filter polarisation contains VV",
            "5. filter resolution_meters == 10",
            "6. split by orbit pass",
        ],
        "modes_available_in_window": modes,
        "resolutions_available_in_IW_window": resolutions,
        "scenes_sample": _scene_details(with_10m, limit=50),
    }
