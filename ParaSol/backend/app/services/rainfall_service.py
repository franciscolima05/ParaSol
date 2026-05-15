import ee

from app.core.logger import logger
from app.providers.chirps_provider import get_chirps_collection

def check_rainfall_service(data):

    logger.info("comprobando la lluvia")

    polygon = ee.Geometry.Polygon(data.coordinates)

    chirps = get_chirps_collection(
        start_date=data.start_date,
        end_date=data.end_date
    )

    def extract_daily(image):
        date = image.date().format("YYYY-MM-dd")
        stats = image.select("precipitation").reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=polygon,
            scale=5000, 
            maxPixels=1e9
        )
        return ee.Feature(None, {
            "date": date,
            "precipitation": stats.get("precipitation")
        })

    daily_features = chirps.map(extract_daily)
    result = daily_features.getInfo()

    # cuánto llovió cada día específico
    series = [
        {
            "date": f["properties"]["date"],
            "precipitation_mm": f["properties"]["precipitation"]
        }
        for f in result["features"]
    ]

    # filtrás una sola vez
    valid_days = [
        day["precipitation_mm"] for day in series 
        if day["precipitation_mm"] is not None
    ]

    # cuánto llovió en total
    total_rainfall_mm = sum(valid_days)

    # cuánto llovió en promedio por día
    avg_daily_rainfall_mm = sum(valid_days) / len(valid_days)


    logger.info("serie diaria calculada: %s días", len(series))
    logger.info("calculo de lluvia completado")

    return {
        "total_rainfall_mm": total_rainfall_mm,
        "avg_daily_rainfall_mm": avg_daily_rainfall_mm,
        "unit": "mm",
        "period": {
            "start": data.start_date,
            "end": data.end_date
        },
        "series": series
    } 