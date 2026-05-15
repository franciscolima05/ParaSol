import ee

from app.core.logger import logger
from app.providers.chirps_provider import get_chirps_collection

def check_rainfall_service(data):

    logger.info("comprobando la lluvia")

    polygon = ee.Geometry.Polygon(data.coordinates)

    chirps = get_chirps_collection(
        start_date="2024-01-01",
        end_date="2024-12-31"
    )

    rainfall = (
        chirps
        .select("precipitation")
        .sum()
    )

    stats = rainfall.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=polygon,
        scale=5000,
        maxPixels=1e9
    )

    result = stats.getInfo()
    rainfall_mm=result.get("precipitation")
    logger.info("lluvia acumulada: %s mm", rainfall_mm)

    logger.info("calculo de lluvia completado")

    return {
           "rainfall_mm": rainfall_mm,
           "unit": "mm",
           "period": {
               "start": "2024-01-01",
               "end": "2024-12-31"
           }
       }