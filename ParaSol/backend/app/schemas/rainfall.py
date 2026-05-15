from pydantic import BaseModel

class RainfallRequest(BaseModel):
    coordinates: list