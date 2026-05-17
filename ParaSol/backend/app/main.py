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

SPICH_DIR = BASE_DIR / "frontend" / "web" / "spich"

app = FastAPI()

@app.on_event("startup")
def startup_event():
    init_ee()

app.include_router(rainfall_router)
app.include_router(vegetation_router)

app.mount("/static", StaticFiles(directory=str(SPICH_DIR)), name="static")

@app.get("/")
def serve_index():
    return FileResponse(str(SPICH_DIR / "index.html"))