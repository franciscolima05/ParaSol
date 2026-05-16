import ee


SENTINEL1_COLLECTION = "COPERNICUS/S1_GRD"


def get_s1_collection(
    start_date,
    end_date,
    geometry,
    orbit=None,
    relative_orbit=None,
):
    """
    Devuelve la colección Sentinel-1 GRD filtrada para detección
    de anegamiento:

    - polarización VV (la más usada para water detection)
    - modo IW (Interferometric Wide swath, sobre tierra)
    - resolución 10m
    - filtrada por bbox del polígono y rango de fechas
    - opcionalmente filtrada por pasada orbital (ASCENDING/DESCENDING)
    - opcionalmente filtrada por relative_orbit (track específico)

    Filtrar por relative_orbit es CRÍTICO para comparaciones pre/post:
    distintos tracks observan la zona desde ángulos de incidencia
    diferentes y el backscatter VV varía con el ángulo. Mezclar tracks
    en un composite mediana introduce ruido del orden de la señal de
    inundación y enmascara el delta real.

    Las imágenes vienen ya calibradas a sigma0 en dB.
    """
    collection = (
        ee.ImageCollection(SENTINEL1_COLLECTION)
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.eq("resolution_meters", 10))
        .select("VV")
    )

    if orbit:
        collection = collection.filter(
            ee.Filter.eq("orbitProperties_pass", orbit)
        )

    if relative_orbit is not None:
        collection = collection.filter(
            ee.Filter.eq("relativeOrbitNumber_start", relative_orbit)
        )

    return collection


def list_available_tracks(geometry, start_date, end_date):
    """
    Lista las combinaciones (orbit_pass, relative_orbit) disponibles
    en la ventana, con la cantidad de escenas en cada una.
    """
    collection = (
        ee.ImageCollection(SENTINEL1_COLLECTION)
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.eq("resolution_meters", 10))
    )

    def per_image(image):
        return ee.Feature(None, {
            "orbit": image.get("orbitProperties_pass"),
            "track": image.get("relativeOrbitNumber_start"),
        })

    features = collection.map(per_image).getInfo()["features"]

    counts = {}
    for f in features:
        key = (f["properties"]["orbit"], f["properties"]["track"])
        counts[key] = counts.get(key, 0) + 1

    return counts


def pick_best_track(
    geometry, pre_start, pre_end, post_start, post_end, orbit=None
):
    """
    Elige el (orbit_pass, relative_orbit) que maximiza min(pre, post)
    — queremos que AMBAS ventanas tengan escenas del mismo track.

    Si `orbit` está fijado por el cliente, solo considera tracks dentro
    de esa pasada.
    """
    pre_counts = list_available_tracks(geometry, pre_start, pre_end)
    post_counts = list_available_tracks(geometry, post_start, post_end)

    # Tracks disponibles en AMBAS ventanas
    common_keys = set(pre_counts.keys()) & set(post_counts.keys())
    if orbit:
        common_keys = {k for k in common_keys if k[0] == orbit}

    if not common_keys:
        # Fallback: usar el track con más escenas post (puede no haber baseline)
        candidates = post_counts
        if orbit:
            candidates = {k: v for k, v in candidates.items() if k[0] == orbit}
        if not candidates:
            return orbit or "DESCENDING", None
        best_key = max(candidates, key=candidates.get)
        return best_key[0], best_key[1]

    # Maximizar el mínimo (pre, post) — penaliza tracks con cobertura asimétrica
    best_key = max(
        common_keys,
        key=lambda k: min(pre_counts.get(k, 0), post_counts.get(k, 0)),
    )
    return best_key[0], best_key[1]
