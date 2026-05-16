from typing import Literal, Optional
from pydantic import BaseModel, Field


class DateRange(BaseModel):
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str = Field(..., description="YYYY-MM-DD")


class PolygonGeoJSON(BaseModel):
    coordinates: list = Field(
        ...,
        description="GeoJSON polygon coordinates: [[[lon, lat], ...]]"
    )


class FloodDebugRequest(BaseModel):
    """
    Request para el endpoint de debug. Toma un solo rango temporal
    (no pre/post) y un polígono, y devuelve cuántas escenas matchean
    cada filtro acumulado.
    """
    polygon: PolygonGeoJSON
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str = Field(..., description="YYYY-MM-DD")


class FloodRequest(BaseModel):
    """
    Request para detección de anegamiento con Sentinel-1 SAR.

    Compara la mediana del backscatter VV en una ventana pre-evento
    contra una ventana post-evento sobre el mismo polígono.

    El radar atraviesa nubes y funciona de noche, por lo que es la
    única fuente confiable cuando hay nubosidad elevada o el evento
    ocurre fuera del horario diurno.
    """
    polygon: PolygonGeoJSON
    pre_event: DateRange
    post_event: DateRange
    orbit: Optional[Literal["ASCENDING", "DESCENDING"]] = Field(
        default=None,
        description=(
            "Pasada orbital. Si es None se elige automáticamente la "
            "pasada del track con más escenas comunes pre+post."
        ),
    )
    relative_orbit: Optional[int] = Field(
        default=None,
        description=(
            "Número de track específico (relativeOrbitNumber_start). "
            "CRÍTICO para comparaciones pre/post limpias: distintos "
            "tracks tienen ángulos de incidencia diferentes y el VV "
            "varía con el ángulo. Si es None se elige el track que "
            "maximiza min(escenas_pre, escenas_post)."
        ),
    )
    flood_threshold_db: float = Field(
        default=-17.0,
        description=(
            "Umbral de backscatter VV en dB por debajo del cual se "
            "considera superficie de agua. Default -17 dB (UN-SPIDER)."
        ),
    )
    min_flooded_area_pct: float = Field(
        default=5.0,
        description=(
            "Umbral binario: una escena se considera 'anegada' si el "
            "porcentaje de área NUEVA inundada (vs baseline pre) supera "
            "este valor. Default 5%. Subir para cultivos más tolerantes "
            "(maíz ~10%), bajar para más sensibles (soja temprana ~3%)."
        ),
    )


class PeriodStats(BaseModel):
    period: DateRange
    scene_count: int
    vv_mean_db: Optional[float]


class SceneObservation(BaseModel):
    date: str
    new_flooded_pct: Optional[float] = Field(
        None,
        description="% del polígono nuevo-inundado en esta escena vs baseline pre"
    )
    flooded: Optional[bool] = Field(
        None,
        description="Si la escena supera el umbral min_flooded_area_pct"
    )


class FloodResponse(BaseModel):
    status: str
    message: str
    pre_event: PeriodStats
    post_event: PeriodStats
    orbit_used: str
    relative_orbit_used: Optional[int] = Field(
        None,
        description="Track relativeOrbit_number usado para el análisis"
    )
    flood_threshold_db: float
    min_flooded_area_pct: float
    flooded_area_pct: Optional[float] = Field(
        None,
        description="Porcentaje del polígono clasificado como inundado en el post-evento"
    )
    new_flooded_area_pct: Optional[float] = Field(
        None,
        description=(
            "Porcentaje del polígono que pasó de NO-agua en pre a "
            "agua en post (cambio neto atribuible al evento)"
        ),
    )
    delta_vv_db: Optional[float] = Field(
        None,
        description="Diferencia de backscatter medio post - pre, en dB"
    )
    flood_detected: Optional[bool] = Field(
        None,
        description=(
            "True si al menos una escena del post-evento supera el "
            "umbral min_flooded_area_pct contra la baseline pre. "
            "None si no hay datos pre suficientes para baseline."
        ),
    )
    flood_days: Optional[int] = Field(
        None,
        description=(
            "Días entre la primera y la última escena anegada del "
            "post-evento (inclusivo). 0 si no se detectó anegamiento. "
            "None si no hay baseline pre."
        ),
    )
    scenes: Optional[list[SceneObservation]] = Field(
        None,
        description="Detalle por escena ordenado cronológicamente"
    )
