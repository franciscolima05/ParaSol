from fastapi import APIRouter

from app.schemas.rainfall import RainfallRequest
from app.schemas.sentinel import FloodRequest, FloodDebugRequest

from app.services import rainfall_service
from app.services.twi_service import calculate_twi
from app.services.flood_service import detect_flood
from app.services.flood_debug_service import debug_s1_coverage

router = APIRouter()

@router.get("/")
def root():
    return {"message": "ParaSol Backend Running"}


@router.post("/rainfall/check")
def check_rainfall(data: RainfallRequest):

    return rainfall_service.check_rainfall_service(data)

@router.post("/analysis/twi")
def twi_endpoint(payload: dict):
    polygon = payload["polygon"]

    print(polygon)

    result = calculate_twi(polygon)

    return {
        "status": "ok",
        "message": "TWI calculado",
        "data": result
    }


@router.post("/analysis/flood")
def flood_endpoint(data: FloodRequest):
    """
    Detección de anegamiento con Sentinel-1 SAR.

    El radar atraviesa nubes y funciona de noche, por lo que es la
    fuente correcta cuando hay nubosidad alta o el evento ocurre
    fuera del horario diurno. Compara el backscatter VV pre vs post
    sobre el mismo polígono.
    """
    return detect_flood(data)


@router.post("/analysis/flood/debug")
def flood_debug_endpoint(data: FloodDebugRequest):
    """
    Diagnóstico: para un polígono + ventana, cuenta cuántas escenas
    Sentinel-1 matchean cada filtro acumulado y lista las escenas
    disponibles.

    Útil para entender por qué scene_count sale bajo en /analysis/flood.
    """
    return debug_s1_coverage(data)
