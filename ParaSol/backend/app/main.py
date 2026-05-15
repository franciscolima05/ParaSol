from fastapi import FastAPI

import app.core.earth_engine

from app.api.routes.analysis import router as rainfall_router

app = FastAPI()

#REQUEST = datos del cliente
#POLYGON = objeto GIS real
#DATES = fechas
#COLLECTION = colección de imágenes
#FIRST IMAGE = primera imagen de la colección
#BANDS = una capa de información dentro de una imagen
#RAINFALL BANDS = bandas del dataset => Earth Engine: sumó las 365 imágenes (lluvia total acumulada del año)
#STATS = estadísticas de la región

app.include_router(rainfall_router)