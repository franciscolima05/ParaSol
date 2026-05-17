from fastapi import FastAPI
from app.api.routes.analysis import router as rainfall_router
from app.core.earth_engine import init_ee
from app.api.routes.vegetation import router as vegetation_router
from pathlib import Path
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

BASE_DIR = Path(__file__).resolve().parents[2]  # ParaSol/

load_dotenv(BASE_DIR / ".env.dev")

FRONTEND_DIR = BASE_DIR / "frontend" / "web"
SPICH_DIR = FRONTEND_DIR / "spich"

app = FastAPI()

@app.on_event("startup")
def startup_event():
    init_ee()

app.include_router(rainfall_router)
app.include_router(vegetation_router)

@app.get("/")
def serve_index():
    return FileResponse(str(SPICH_DIR / "index.html"))

app.mount("/static", StaticFiles(directory=str(SPICH_DIR)), name="static")
app.mount("/spich", StaticFiles(directory=str(SPICH_DIR), html=True), name="spich")
app.mount("/aseguradora", StaticFiles(directory=str(FRONTEND_DIR / "aseguradora"), html=True), name="aseguradora")
app.mount("/agricultor", StaticFiles(directory=str(FRONTEND_DIR / "agricultor"), html=True), name="agricultor")