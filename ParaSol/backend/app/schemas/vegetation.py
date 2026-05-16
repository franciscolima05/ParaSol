from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from datetime import date, timedelta


class VegetationRequest(BaseModel):
    """
    Request para análisis de vegetación con Sentinel-2.

    coordinates: polígono en formato GeoJSON (lista de [lon, lat])
    start_date: inicio del período de análisis (YYYY-MM-DD)
    end_date: fin del período de análisis (YYYY-MM-DD)
    """

    coordinates: list
    start_date: str
    end_date: str

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, v):
        if not v or not isinstance(v, list):
            raise ValueError("coordinates must be a non-empty list")

        # Acepta tanto [[lon,lat],...] como [[[lon,lat],...]] (GeoJSON polygon)
        ring = v[0] if isinstance(v[0][0], list) else v

        if len(ring) < 4:
            raise ValueError(
                "A polygon requires at least 4 coordinate pairs (first and last must be equal)"
            )

        for pair in ring:
            if len(pair) != 2:
                raise ValueError("Each coordinate must be [longitude, latitude]")
            lon, lat = pair
            if not (-180 <= lon <= 180):
                raise ValueError(f"Longitude {lon} out of range [-180, 180]")
            if not (-90 <= lat <= 90):
                raise ValueError(f"Latitude {lat} out of range [-90, 90]")

        return v

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v):
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError(f"Date '{v}' must be in YYYY-MM-DD format")
        return v

    @model_validator(mode="after")
    def validate_date_range(self):
        start = date.fromisoformat(self.start_date)
        end = date.fromisoformat(self.end_date)

        if start >= end:
            raise ValueError("start_date must be before end_date")

        # Sentinel-2 SR disponible desde 2017-03-28
        sentinel2_launch = date(2017, 3, 28)
        if start < sentinel2_launch:
            raise ValueError(
                f"Sentinel-2 SR data is available from {sentinel2_launch} onward"
            )

        # Advertencia implícita: períodos muy cortos pueden no tener imágenes sin nubes
        delta = (end - start).days
        if delta < 10:
            raise ValueError(
                "Date range must be at least 10 days to allow sufficient Sentinel-2 coverage"
            )

        return self


class NDVIStats(BaseModel):
    ndvi_mean:   Optional[float]
    ndvi_min:    Optional[float]
    ndvi_max:    Optional[float]
    ndvi_median: Optional[float]
    image_count: int
    warning:     Optional[str]


class NDVIClassification(BaseModel):
    label:       str
    description: str
    value:       Optional[float]


class VegetationPeriod(BaseModel):
    start: str
    end:   str


class VegetationResponse(BaseModel):
    low_confidence:    bool
    confidence_reasons: list[str]
    period:           VegetationPeriod
    ndvi:             NDVIStats
    classification:   NDVIClassification
    dataset:          str
    resolution_meters: int