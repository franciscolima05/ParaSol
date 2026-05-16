import ee
from datetime import datetime

from app.core.logger import logger
from app.providers.sentinel1_provider import (
    get_s1_collection,
    pick_best_track,
)


# Tamaño del kernel para speckle filter (Lee/focal_median).
# 50m suaviza moteado típico de SAR sin perder bordes de agua.
SPECKLE_KERNEL_RADIUS_M = 50

# Escala de reducción espacial. Sentinel-1 GRD viene a ~10m.
REDUCTION_SCALE_M = 10


def _despeckle(image):
    """Reduce el ruido moteado característico de SAR con focal_median."""
    return image.focal_median(
        radius=SPECKLE_KERNEL_RADIUS_M,
        kernelType="circle",
        units="meters",
    )


def _period_stats(collection, geometry, reducer="median"):
    """
    Construye un composite temporal de la colección y reporta la
    media espacial del VV (en dB) sobre el polígono.

    reducer:
        "median" → para PRE: baseline robusto del estado seco típico.
        "min"    → para POST: captura el peak de inundación incluso
                    en eventos cortos (el agua pasa por el polígono
                    y drena antes de la siguiente revisita).
    """
    scene_count = collection.size().getInfo()
    if scene_count == 0:
        return None, 0

    if reducer == "min":
        reduced = collection.min()
    else:
        reduced = collection.median()
    composite = _despeckle(reduced).rename("VV")

    stats = composite.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geometry,
        scale=REDUCTION_SCALE_M,
        maxPixels=1e9,
        bestEffort=True,
    ).getInfo()

    return stats.get("VV"), scene_count


def _area_below_threshold_pct(image, geometry, threshold_db):
    """% del polígono donde el composite (VV en dB) está por debajo del umbral."""
    water_mask = image.lt(threshold_db).rename("water")

    pixel_area = ee.Image.pixelArea()
    water_area_img = pixel_area.updateMask(water_mask)

    total_area = pixel_area.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=REDUCTION_SCALE_M,
        maxPixels=1e9,
        bestEffort=True,
    ).getInfo().get("area")

    water_area = water_area_img.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=REDUCTION_SCALE_M,
        maxPixels=1e9,
        bestEffort=True,
    ).getInfo().get("area")

    if not total_area or total_area == 0:
        return None

    water_area = water_area or 0
    return round((water_area / total_area) * 100, 4)


def _new_flooded_pct(pre_composite, post_composite, geometry, threshold_db):
    """% del polígono que pasó de NO-agua (pre) a agua (post composite)."""
    pre_water = pre_composite.lt(threshold_db)
    post_water = post_composite.lt(threshold_db)

    new_water_mask = post_water.And(pre_water.Not()).rename("new_water")

    pixel_area = ee.Image.pixelArea()
    new_water_area_img = pixel_area.updateMask(new_water_mask)

    total_area = pixel_area.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=REDUCTION_SCALE_M,
        maxPixels=1e9,
        bestEffort=True,
    ).getInfo().get("area")

    new_water_area = new_water_area_img.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=REDUCTION_SCALE_M,
        maxPixels=1e9,
        bestEffort=True,
    ).getInfo().get("area")

    if not total_area or total_area == 0:
        return None

    new_water_area = new_water_area or 0
    return round((new_water_area / total_area) * 100, 4)


def _per_scene_new_flooded_pct(
    post_collection, pre_composite, geometry, threshold_db
):
    """
    Para cada escena del post-evento, calcula el % del polígono que
    pasó de NO-agua (baseline pre) a agua en esa escena específica.

    Se ejecuta todo del lado de Earth Engine con .map() y un único
    getInfo() final — evita ida-y-vuelta por escena.
    """
    pre_water = pre_composite.lt(threshold_db)
    pre_water_not = pre_water.Not()
    pixel_area = ee.Image.pixelArea()

    def per_scene(image):
        date = image.date().format("YYYY-MM-dd")
        despeckled = image.focal_median(
            radius=SPECKLE_KERNEL_RADIUS_M,
            kernelType="circle",
            units="meters",
        )
        scene_water = despeckled.lt(threshold_db)
        new_water = scene_water.And(pre_water_not)

        total_area = pixel_area.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=geometry,
            scale=REDUCTION_SCALE_M,
            maxPixels=1e9,
            bestEffort=True,
        ).get("area")

        new_water_area = pixel_area.updateMask(new_water).reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=geometry,
            scale=REDUCTION_SCALE_M,
            maxPixels=1e9,
            bestEffort=True,
        ).get("area")

        # ratio = new_water / total  (server-side, safe contra divisiones)
        pct = (
            ee.Number(new_water_area)
            .divide(ee.Number(total_area).max(1))
            .multiply(100)
        )

        return ee.Feature(None, {
            "date": date,
            "new_flooded_pct": pct,
        })

    features = post_collection.map(per_scene).getInfo()
    scenes = [
        {
            "date": f["properties"]["date"],
            "new_flooded_pct": (
                round(f["properties"]["new_flooded_pct"], 4)
                if f["properties"]["new_flooded_pct"] is not None
                else None
            ),
        }
        for f in features["features"]
    ]
    # Una misma fecha puede aparecer en dos escenas si hay solapamiento de tiles;
    # ordenamos por fecha para el cálculo de duración.
    scenes.sort(key=lambda s: s["date"])
    return scenes


def _flood_duration_days(flooded_scenes):
    """Días entre la primera y última escena anegada (rango inclusivo)."""
    if not flooded_scenes:
        return 0
    first = datetime.strptime(flooded_scenes[0]["date"], "%Y-%m-%d")
    last = datetime.strptime(flooded_scenes[-1]["date"], "%Y-%m-%d")
    return (last - first).days + 1


def detect_flood(data):
    """
    Pipeline principal de detección de anegamiento con Sentinel-1.

    Devuelve estadísticas agregadas + análisis por escena:

        flood_detected — True si alguna escena post supera el umbral
                         min_flooded_area_pct contra la baseline pre.
        flood_days     — span en días entre primera y última escena anegada.
        scenes[]       — observación por fecha (transparencia / debugging).
    """
    logger.info("detectando anegamiento con Sentinel-1")

    geometry = ee.Geometry.Polygon(data.polygon.coordinates)

    # Resolución de track orbital.
    # CRÍTICO: hay que comparar pre vs post sobre el MISMO relative_orbit,
    # de lo contrario el delta_vv_db queda contaminado por la diferencia
    # de ángulo de incidencia entre pasadas distintas.
    if data.orbit and data.relative_orbit is not None:
        orbit = data.orbit
        relative_orbit = data.relative_orbit
    else:
        orbit, relative_orbit = pick_best_track(
            geometry,
            data.pre_event.start_date,
            data.pre_event.end_date,
            data.post_event.start_date,
            data.post_event.end_date,
            orbit=data.orbit,
        )
    logger.info(
        "usando track: orbit=%s relative_orbit=%s",
        orbit, relative_orbit,
    )

    # Colecciones pre / post (filtradas al MISMO track)
    pre_collection = get_s1_collection(
        data.pre_event.start_date,
        data.pre_event.end_date,
        geometry,
        orbit,
        relative_orbit,
    )
    post_collection = get_s1_collection(
        data.post_event.start_date,
        data.post_event.end_date,
        geometry,
        orbit,
        relative_orbit,
    )

    # Pre = mediana (baseline robusto)
    # Post = min (captura peak incluso en eventos cortos)
    pre_mean_db, pre_count = _period_stats(
        pre_collection, geometry, reducer="median"
    )
    post_mean_db, post_count = _period_stats(
        post_collection, geometry, reducer="min"
    )

    logger.info(
        "escenas pre=%s post=%s | VV_pre=%s VV_post=%s",
        pre_count, post_count, pre_mean_db, post_mean_db,
    )

    base_response = {
        "pre_event": {
            "period": {
                "start_date": data.pre_event.start_date,
                "end_date": data.pre_event.end_date,
            },
            "scene_count": pre_count,
            "vv_mean_db": pre_mean_db,
        },
        "post_event": {
            "period": {
                "start_date": data.post_event.start_date,
                "end_date": data.post_event.end_date,
            },
            "scene_count": post_count,
            "vv_mean_db": post_mean_db,
        },
        "orbit_used": orbit,
        "relative_orbit_used": relative_orbit,
        "flood_threshold_db": data.flood_threshold_db,
        "min_flooded_area_pct": data.min_flooded_area_pct,
        "flooded_area_pct": None,
        "new_flooded_area_pct": None,
        "delta_vv_db": None,
        "flood_detected": None,
        "flood_days": None,
        "scenes": None,
    }

    if post_count == 0:
        return {
            **base_response,
            "status": "no_data",
            "message": "No hay escenas Sentinel-1 en la ventana post-evento",
        }

    # Composite agregado del post para flooded_area_pct.
    # Usamos min() (no median) para capturar el peak de eventos cortos:
    # la mediana ahoga inundaciones que duran menos que el revisit time.
    post_composite = _despeckle(post_collection.min()).rename("VV")
    flooded_pct = _area_below_threshold_pct(
        post_composite, geometry, data.flood_threshold_db
    )

    # Sin baseline pre no podemos atribuir el agua al evento → no hay
    # flood_detected / flood_days confiable. Devolvemos lo que se pueda.
    if pre_count == 0:
        return {
            **base_response,
            "status": "ok_no_baseline",
            "message": (
                "No hay escenas pre-evento para baseline. "
                "Métricas agregadas calculadas; flood_detected y "
                "flood_days no aplicables sin pre."
            ),
            "flooded_area_pct": flooded_pct,
        }

    pre_composite = _despeckle(pre_collection.median()).rename("VV")
    new_flooded_pct = _new_flooded_pct(
        pre_composite, post_composite, geometry, data.flood_threshold_db
    )
    delta_db = None
    if pre_mean_db is not None and post_mean_db is not None:
        delta_db = round(post_mean_db - pre_mean_db, 4)

    # Análisis por escena
    per_scene = _per_scene_new_flooded_pct(
        post_collection,
        pre_composite,
        geometry,
        data.flood_threshold_db,
    )
    threshold_pct = data.min_flooded_area_pct
    scenes_with_flag = [
        {
            **s,
            "flooded": (
                s["new_flooded_pct"] is not None
                and s["new_flooded_pct"] >= threshold_pct
            ),
        }
        for s in per_scene
    ]
    flooded_scenes = [s for s in scenes_with_flag if s["flooded"]]
    flood_detected = len(flooded_scenes) > 0
    flood_days = _flood_duration_days(flooded_scenes)

    logger.info(
        "anegamiento: detected=%s days=%s flooded=%s%% new=%s%% delta=%s dB | %d/%d escenas anegadas",
        flood_detected, flood_days, flooded_pct, new_flooded_pct, delta_db,
        len(flooded_scenes), len(per_scene),
    )

    return {
        **base_response,
        "status": "ok",
        "message": "Detección de anegamiento completada",
        "flooded_area_pct": flooded_pct,
        "new_flooded_area_pct": new_flooded_pct,
        "delta_vv_db": delta_db,
        "flood_detected": flood_detected,
        "flood_days": flood_days,
        "scenes": scenes_with_flag,
    }
