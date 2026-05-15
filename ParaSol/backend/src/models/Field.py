from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from ParaSol.ParaSol.backend.src.database import Base


class Field(Base):
    """
    Parcela / lote agrícola. Geometría POLYGON en WGS84 (SRID 4326).

    `polygon_hash` (SHA-256 del GeoJSON normalizado) es el anclaje
    anti-fraude: si se modifica el polígono después de emitida una póliza,
    el hash cambia y se detecta la inconsistencia.

    `centroid` y `area_ha` se precalculan al insertar para evitar costos
    de cómputo geoespacial en cada query.
    """
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Geometría (PostGIS)
    geometry = Column(Geometry("POLYGON", srid=4326), nullable=False)
    centroid = Column(Geometry("POINT", srid=4326))
    area_ha = Column(Float)

    # Ubicación administrativa
    country = Column(String(2))
    region = Column(String(100))         # "Buenos Aires", "Oaxaca"
    locality = Column(String(100))

    # Anti-fraude
    polygon_hash = Column(String(64))    # SHA-256 del GeoJSON normalizado

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="fields")
    policies = relationship("Policy", back_populates="field")
    parametric_events = relationship("ParametricEvent", back_populates="field")

    def __repr__(self):
        return f"<Field(id={self.id}, name='{self.name}', area_ha={self.area_ha})>"
