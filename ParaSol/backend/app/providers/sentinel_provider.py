import ee
import logging
logger = logging.getLogger("parasol")
# Sentinel-2 Surface Reflectance (Level-2A)
# Disponible desde 2017-03-28
SENTINEL2_DATASET = "COPERNICUS/S2_SR_HARMONIZED"

# Umbral de cobertura nubosa aceptable (%)
MAX_CLOUD_COVERAGE = 20


def get_ndvi_stats(polygon: ee.Geometry, start_date: str, end_date: str) -> dict:
    """
    Calcula estadísticas NDVI sobre un polígono para un rango de fechas.

    Sentinel-2 bandas relevantes:
        B4 → Red (665 nm)
        B8 → NIR Near-Infrared (842 nm)

    NDVI = (NIR - Red) / (NIR + Red)
    Rango: [-1, 1]
        < 0    → agua, nieve, nubes
        0–0.2  → suelo desnudo, urbano
        0.2–0.5 → vegetación escasa / pastizal
        > 0.5  → vegetación densa / cultivo activo

    Args:
        polygon: Geometría GEE del área de análisis
        start_date: Fecha inicio ISO (YYYY-MM-DD)
        end_date: Fecha fin ISO (YYYY-MM-DD)

    Returns:
        dict con mean, min, max, median del NDVI y conteo de imágenes usadas
    """
    logger.info(
        f"Querying Sentinel-2 NDVI | dates: {start_date} → {end_date} | "
        f"max_cloud: {MAX_CLOUD_COVERAGE}%"
    )

    collection = (
        ee.ImageCollection(SENTINEL2_DATASET)
        .filterBounds(polygon)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_COVERAGE))
    )

    image_count = collection.size().getInfo()
    logger.info(f"Sentinel-2 images found after cloud filter: {image_count}")

    if image_count == 0:
        logger.warning(
            f"No Sentinel-2 images available for the period {start_date} → {end_date} "
            f"with cloud coverage < {MAX_CLOUD_COVERAGE}%. "
            "Consider relaxing the date range or cloud threshold."
        )
        return {
            "ndvi_mean": None,
            "ndvi_min": None,
            "ndvi_max": None,
            "ndvi_median": None,
            "image_count": 0,
            "warning": "No images available for the given period and cloud threshold.",
        }

    def compute_ndvi(image: ee.Image) -> ee.Image:
        """Calcula NDVI por imagen y preserva timestamp."""
        ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
        return ndvi.copyProperties(image, ["system:time_start"])

    ndvi_collection = collection.map(compute_ndvi)

    # Imagen compuesta: mediana temporal → reduce efecto de outliers por nubes residuales
    ndvi_composite = ndvi_collection.median()

    # Reducción espacial sobre el polígono
    stats = ndvi_composite.reduceRegion(
        reducer=ee.Reducer.mean()
            .combine(ee.Reducer.min(), sharedInputs=True)
            .combine(ee.Reducer.max(), sharedInputs=True)
            .combine(ee.Reducer.median(), sharedInputs=True),
        geometry=polygon,
        scale=10,          # resolución nativa Sentinel-2 banda B8/B4 = 10m
        maxPixels=1e9,
        bestEffort=True,   # evita error si el polígono es muy grande
    ).getInfo()

    logger.info(f"NDVI stats computed: {stats}")

    return {
        "ndvi_mean":   round(stats.get("NDVI_mean",   0) or 0, 4),
        "ndvi_min":    round(stats.get("NDVI_min",    0) or 0, 4),
        "ndvi_max":    round(stats.get("NDVI_max",    0) or 0, 4),
        "ndvi_median": round(stats.get("NDVI_median", 0) or 0, 4),
        "image_count": image_count,
        "warning": None,
    }