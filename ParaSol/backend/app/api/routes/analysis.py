from fastapi import APIRouter

from app.schemas.rainfall import RainfallRequest
from app.services import rainfall_service

router = APIRouter()

@router.get("/")
def root():
    return {"message": "ParaSol Backend Running"}


@router.post("/rainfall/check")
def check_rainfall(data: RainfallRequest):

    return rainfall_service.check_rainfall_service(data)