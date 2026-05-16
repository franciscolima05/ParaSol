from fastapi import APIRouter, HTTPException
from app.schemas.vegetation import VegetationRequest, VegetationResponse
from app.services.ndvi_service import analyze_vegetation
import logging
logger = logging.getLogger("parasol")
router = APIRouter(prefix="/analysis", tags=["vegetation"])


@router.post("/ndvi", response_model=VegetationResponse)
async def check_vegetation(request: VegetationRequest):
    """
    Analiza el estado de vegetación de una región usando Sentinel-2.

    Calcula NDVI (Normalized Difference Vegetation Index) sobre el polígono
    definido por las coordenadas, para el período especificado.

    **Dataset:** COPERNICUS/S2_SR_HARMONIZED (Level-2A Surface Reflectance)
    **Resolución:** 10 metros
    **Disponibilidad:** desde 2017-03-28

    **Interpretación NDVI:**
    - `< 0`      → agua, nieve o nube
    - `0.0–0.2`  → suelo desnudo
    - `0.2–0.35` → vegetación escasa
    - `0.35–0.5` → cultivo en desarrollo
    - `0.5–0.7`  → cultivo sano
    - `> 0.7`    → vegetación densa

    **Ejemplo de request:**
    ```json
    {
      "coordinates": [
        [-60.326698, -38.198767],
        [-60.306698, -38.198767],
        [-60.306698, -38.178767],
        [-60.326698, -38.178767],
        [-60.326698, -38.198767]
      ],
      "start_date": "2024-01-01",
      "end_date": "2024-03-31"
    }
    ```
    """
    logger.info(
        f"POST /analysis/ndvi | dates: {request.start_date} → {request.end_date}"
    )

    try:
        result = analyze_vegetation(
            coordinates=request.coordinates,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        return result

    except Exception as e:
        logger.error(f"NDVI analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Vegetation analysis failed: {str(e)}",
        )