from fastapi import FastAPI
from app.api.routes.analysis import router as rainfall_router
from app.core.earth_engine import init_ee
from app.api.routes.vegetation import router as vegetation_router

app = FastAPI()

#REQUEST = datos del cliente
#POLYGON = objeto GIS real
#DATES = fechas
#COLLECTION = colección de imágenes
#FIRST IMAGE = primera imagen de la colección
#BANDS = una capa de información dentro de una imagen
#RAINFALL BANDS = bandas del dataset => Earth Engine: sumó las 365 imágenes (lluvia total acumulada del año)
#STATS = estadísticas de la región

@app.on_event("startup")
def startup_event():
    init_ee()


app.include_router(rainfall_router)
app.include_router(vegetation_router)