from pydantic import BaseModel

class RainfallRequest(BaseModel):
    coordinates: list
    start_date: str
    end_date: str