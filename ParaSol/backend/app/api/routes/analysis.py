from fastapi import APIRouter

from app.schemas.rainfall import RainfallRequest

from app.services import rainfall_service
from app.services.twi_service import calculate_twi

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
