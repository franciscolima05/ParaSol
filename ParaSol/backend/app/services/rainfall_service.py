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

    first_image = ee.Image(chirps.first())

    # resolución nativa del dataset
    native_scale = (
        first_image
        .projection()
        .nominalScale()
    )

    logger.info(
        "resolucion nativa CHIRPS: %s metros",
        native_scale.getInfo()
    )

    def extract_daily(image):

        date = image.date().format("YYYY-MM-dd")

        precipitation = image.select("precipitation")

        stats = precipitation.reduceRegion(
            reducer=(
                ee.Reducer.mean()
                .combine(
                    reducer2=ee.Reducer.max(),
                    sharedInputs=True
                )
                .combine(
                    reducer2=ee.Reducer.min(),
                    sharedInputs=True
                )
                .combine(
                    reducer2=ee.Reducer.percentile([95]),
                    sharedInputs=True
                )
            ),
            geometry=polygon,
            scale=native_scale,
            maxPixels=1e9
        )

        # cantidad efectiva de pixeles usados
        pixel_count = precipitation.reduceRegion(
            reducer=ee.Reducer.count(),
            geometry=polygon,
            scale=native_scale,
            maxPixels=1e9
        )

        return ee.Feature(None, {
            "date": date,

            "mean_mm": stats.get("precipitation_mean"),

            "max_mm": stats.get("precipitation_max"),

            "min_mm": stats.get("precipitation_min"),

            "p95_mm": stats.get("precipitation_p95"),

            "effective_pixels": pixel_count.get("precipitation")
        })

    daily_features = chirps.map(extract_daily)

    result = daily_features.getInfo()

    series = []

    low_confidence = False
    confidence_reasons = []

    for f in result["features"]:

        props = f["properties"]

        effective_pixels = props.get("effective_pixels")

        if effective_pixels is not None and effective_pixels < 5:
            low_confidence = True

        series.append({
            "date": props["date"],

            "mean_mm": props.get("mean_mm"),

            "max_mm": props.get("max_mm"),

            "min_mm": props.get("min_mm"),

            "p95_mm": props.get("p95_mm"),

            "effective_pixels": effective_pixels
        })

    if low_confidence:
        confidence_reasons.append(
            "polygon covers too few CHIRPS pixels"
        )

    valid_days = [
        day["mean_mm"]
        for day in series
        if day["mean_mm"] is not None
    ]

    total_rainfall_mm = sum(valid_days)

    max_observed_mm = max(
        (
            day["max_mm"]
            for day in series
            if day["max_mm"] is not None
        ),
        default=None
    )

    logger.info(
        "serie diaria calculada: %s días",
        len(series)
    )

    logger.info(
        "lluvia total: %.2f mm | pico máximo: %s mm",
        total_rainfall_mm,
        max_observed_mm
    )

    logger.info("calculo de lluvia completado")

    return {

        "low_confidence": low_confidence,

        "confidence_reasons": confidence_reasons,

        "total_rainfall_mm": round(
            total_rainfall_mm,
            2
        ),

        "max_observed_mm": (
            round(max_observed_mm, 2)
            if max_observed_mm is not None
            else None
        ),

        "unit": "mm",

        "dataset": "UCSB-CHG/CHIRPS/DAILY",

        "spatial_resolution_km": 5,

        "native_scale_meters": native_scale.getInfo(),

        "period": {
            "start": data.start_date,
            "end": data.end_date
        },

        "series": series
    }