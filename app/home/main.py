from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx

app = FastAPI(
    title="Microservicios de Vuelos",
    description="Interfaz principal para acceder a los microservicios de vuelos"
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

MICROSERVICIOS = {
    "api": "http://api:8000",
    "consultas": "http://consultas:8001",
    "analisis": "http://graficos:8002"
}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api")
async def api_service():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{MICROSERVICIOS['api']}/status")
            return response.json()
        except Exception:
            raise HTTPException(status_code=503, detail="Microservicio API no disponible")

@app.get("/consultas")
async def consultas_service():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{MICROSERVICIOS['consultas']}")
            return response.json()
        except Exception:
            raise HTTPException(status_code=503, detail="Microservicio Consultas no disponible")

@app.get("/analisis")
async def analisis_service():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{MICROSERVICIOS['analisis']}/status")
            return response.json()
        except Exception:
            raise HTTPException(status_code=503, detail="Microservicio Análisis no disponible")