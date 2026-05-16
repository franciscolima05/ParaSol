"""
Repositorio de Field.

Cada parcela tiene geometría PostGIS + `polygon_hash` (SHA-256 del GeoJSON
normalizado) que sirve de anclaje anti-fraude: si la geometría cambia
después de emitida una póliza, el hash cambia y se detecta.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Union

from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Polygon, shape
from sqlalchemy import func
from sqlalchemy.orm import Session

from ParaSol.ParaSol.backend.src.models import Field


# === Helpers ===

def _normalize_geojson(geojson: Dict[str, Any]) -> str:
    """
    Serializa el GeoJSON de forma determinística (sort_keys, sin espacios
    superfluos) para que el hash sea reproducible.
    """
    return json.dumps(geojson, sort_keys=True, separators=(",", ":"))


def compute_polygon_hash(geojson: Dict[str, Any]) -> str:
    """SHA-256 del GeoJSON normalizado del polígono."""
    return hashlib.sha256(_normalize_geojson(geojson).encode("utf-8")).hexdigest()


def _to_polygon(geometry: Union[Dict[str, Any], Polygon]) -> Polygon:
    if isinstance(geometry, Polygon):
        return geometry
    return shape(geometry)


# === Create ===

def create_field(
    session: Session,
    *,
    owner_id: int,
    name: str,
    geometry_geojson: Dict[str, Any],
    country: Optional[str] = None,
    region: Optional[str] = None,
    locality: Optional[str] = None,
) -> Field:
    """
    Crea una parcela. Precalcula `centroid`, `area_ha` (aprox. en ha asumiendo
    coords EPSG:4326 transformadas) y `polygon_hash`.

    NOTA: para área exacta habría que reproyectar a un CRS métrico local.
    Acá usamos shapely.area (en grados²) × factor aproximado solo como
    placeholder; en producción usar `ST_Area` con `geography`.
    """
    poly = _to_polygon(geometry_geojson)

    field = Field(
        owner_id=owner_id,
        name=name,
        geometry=from_shape(poly, srid=4326),
        centroid=from_shape(poly.centroid, srid=4326),
        # Aproximación rápida: 1 grado² ≈ 12_100 km² en el ecuador.
        # Solo para tener un orden de magnitud; el cálculo serio es PostGIS.
        area_ha=float(poly.area) * 12_100 * 100,
        country=country,
        region=region,
        locality=locality,
        polygon_hash=compute_polygon_hash(geometry_geojson),
    )
    session.add(field)
    session.flush()
    return field


# === Read ===

def get_field_by_id(session: Session, field_id: int) -> Optional[Field]:
    return session.get(Field, field_id)


def list_fields_by_owner(session: Session, owner_id: int) -> List[Field]:
    return (
        session.query(Field)
        .filter(Field.owner_id == owner_id)
        .order_by(Field.id)
        .all()
    )


def list_fields(
    session: Session,
    *,
    country: Optional[str] = None,
    region: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Field]:
    q = session.query(Field)
    if country is not None:
        q = q.filter(Field.country == country)
    if region is not None:
        q = q.filter(Field.region == region)
    return q.order_by(Field.id).limit(limit).offset(offset).all()


def find_fields_containing_point(
    session: Session, lon: float, lat: float
) -> List[Field]:
    """
    Encuentra parcelas que contienen el punto (lon, lat). Útil cuando
    el oráculo recibe un alerta meteorológica con coordenadas y necesita
    saber qué pólizas se afectan.
    """
    point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
    return (
        session.query(Field)
        .filter(func.ST_Contains(Field.geometry, point))
        .all()
    )


# === Anti-fraude ===

def verify_polygon_integrity(field: Field) -> bool:
    """
    Recalcula el hash del polígono actual y lo compara con `polygon_hash`.
    Devuelve True si coinciden (no hubo modificación post-emisión).
    """
    if field.geometry is None or field.polygon_hash is None:
        return False
    current_geojson = shape(to_shape(field.geometry)).__geo_interface__
    return compute_polygon_hash(current_geojson) == field.polygon_hash


# === Update ===

def update_field(session: Session, field: Field, **fields_in) -> Field:
    """
    Actualiza atributos del campo. Si se modifica la geometría, recalcula
    centroide, área y hash.
    """
    new_geom = fields_in.pop("geometry_geojson", None)
    for key, value in fields_in.items():
        if hasattr(field, key) and value is not None:
            setattr(field, key, value)

    if new_geom is not None:
        poly = _to_polygon(new_geom)
        field.geometry = from_shape(poly, srid=4326)
        field.centroid = from_shape(poly.centroid, srid=4326)
        field.area_ha = float(poly.area) * 12_100 * 100
        field.polygon_hash = compute_polygon_hash(new_geom)

    session.flush()
    return field


# === Delete ===

def delete_field(session: Session, field: Field) -> None:
    session.delete(field)
    session.flush()
