import ee
import math

#TWI = ln(área_acumulada / tan(pendiente))
def calculate_twi(polygon_geojson):
    coords = polygon_geojson["coordinates"]
    geom = ee.Geometry.Polygon(coords)

    dem = ee.Image("USGS/SRTMGL1_003")

    slope_rad = ee.Terrain.slope(dem).multiply(math.pi / 180)
    tan_slope = slope_rad.tan().max(0.001)

    flow_acc = dem.convolve(ee.Kernel.square(3, "pixels"))

    twi = flow_acc.divide(tan_slope).log().rename("TWI")

    stats = twi.reduceRegion(
        reducer=ee.Reducer.mean().combine(
            ee.Reducer.max(), sharedInputs=True
        ),
        geometry=geom,
        scale=30,
        maxPixels=1e9,
        bestEffort=True
    )

    result = stats.getInfo()  # getInfo() acá adentro, no afuera

    return {
        "avg_twi": result.get("TWI_mean"),
        "max_twi": result.get("TWI_max"),
    }