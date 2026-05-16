import ee
from app.providers.sentinel_provider import get_ndvi_stats
import logging

logger = logging.getLogger("parasol")

# Tabla de clasificación NDVI → estado del cultivo
# Fuente: FAO / ESA Sentinel-2 Land Use guidelines
NDVI_CLASSES = [
    {"label": "water_or_snow",    "min": -1.0, "max": 0.0,  "description": "Agua, nieve o nube"},
    {"label": "bare_soil",        "min":  0.0, "max": 0.2,  "description": "Suelo desnudo o zona urbana"},
    {"label": "sparse_vegetation","min":  0.2, "max": 0.35, "description": "Vegetación escasa o pastizal degradado"},
    {"label": "moderate_crop",    "min":  0.35,"max": 0.5,  "description": "Cultivo en desarrollo o pastizal"},
    {"label": "healthy_crop",     "min":  0.5, "max": 0.7,  "description": "Cultivo sano y activo"},
    {"label": "dense_vegetation", "min":  0.7, "max": 1.0,  "description": "Vegetación densa / monte"},
]


def classify_ndvi(value: float | None) -> dict:
    """
    Clasifica un valor NDVI en una categoría agrícola interpretable.

    Returns:
        dict con label, description y el valor original
    """
    if value is None:
        return {"label": "no_data", "description": "Sin datos disponibles", "value": None}

    for cls in NDVI_CLASSES:
        if cls["min"] <= value < cls["max"]:
            return {"label": cls["label"], "description": cls["description"], "value": value}

    # Borde superior exacto (NDVI = 1.0)
    return {"label": "dense_vegetation", "description": "Vegetación densa / monte", "value": value}


def analyze_vegetation(coordinates: list, start_date: str, end_date: str) -> dict:
    """
    Ejecuta análisis de vegetación completo sobre un polígono.

    Args:
        coordinates: Lista de coordenadas GeoJSON [[lon, lat], ...]
        start_date: Fecha inicio (YYYY-MM-DD)
        end_date: Fecha fin (YYYY-MM-DD)

    Returns:
        dict con estadísticas NDVI, clasificación y metadatos
    """
    logger.info(f"Starting vegetation analysis | {start_date} → {end_date}")

    polygon = ee.Geometry.Polygon(coordinates)

    raw_stats = get_ndvi_stats(polygon, start_date, end_date)

    # Si no hay imágenes, retornamos directamente con warning
    if raw_stats["image_count"] == 0:
        return {
            "period": {"start": start_date, "end": end_date},
            "ndvi": raw_stats,
            "classification": classify_ndvi(None),
            "dataset": "COPERNICUS/S2_SR_HARMONIZED",
            "resolution_meters": 10,
        }

    classification = classify_ndvi(raw_stats["ndvi_mean"])

    logger.info(
        f"Vegetation analysis complete | "
        f"NDVI mean: {raw_stats['ndvi_mean']} | "
        f"Class: {classification['label']} | "
        f"Images used: {raw_stats['image_count']}"
    )
    
    confidence_reasons = []

    if raw_stats["image_count"] < 10:
        confidence_reasons.append(f"image_count={raw_stats['image_count']} (minimo recomendado: 10)")

    if raw_stats["ndvi_min"] < 0:
        confidence_reasons.append(f"ndvi_min={raw_stats['ndvi_min']} (Los valores negativos indican contaminación por agua o nubes)")

    low_confidence = len(confidence_reasons) > 0
    
    return {
        "low_confidence": low_confidence,
        "confidence_reasons": confidence_reasons if low_confidence else [],
        "period": {"start": start_date, "end": end_date},
        "ndvi": raw_stats,
        "classification": classification,
        "dataset": "COPERNICUS/S2_SR_HARMONIZED",
        "resolution_meters": 10,
    }