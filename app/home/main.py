from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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
    "analisis": "http://graficos:8002",
    "vuelos en tiempo real": 'https://realtime-wj1e.onrender.com/realtime-flights/',
    "predicciones": 'https://realtime-wj1e.onrender.com/realtime-flights/'
}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api")
def redirect_vuelos_en_tiempo_real():
    """
    Redirige a la página del microservicio de la api.
    """
    url = MICROSERVICIOS.get("api")
    if not url:
        raise HTTPException(status_code=503, detail="Api no disponible")
    return RedirectResponse(url)


@app.get("/consultas")
def redirect_vuelos_en_tiempo_real():
    """
    Redirige a la página del microservicio de las consultas.
    """
    url = MICROSERVICIOS.get("consultas")
    if not url:
        raise HTTPException(status_code=503, detail="Consultas bo disponibles")
    return RedirectResponse(url)
@app.get("/analisis")
def analisis():
    """
    Redirige a la página del microservicio de analisis de vuelos.
    """
    url = MICROSERVICIOS.get("analisis")
    if not url:
        raise HTTPException(status_code=503, detail="Análisis no disponibles")
    return RedirectResponse(url)
     
@app.get("/vuelos en tiempo real")
def vuelos_en_tiempo_real():
    """
    Redirige a la página del microservicio de vuelos en tiempo real.
    """
    url = MICROSERVICIOS.get("vuelos en tiempo real")
    if not url:
        raise HTTPException(status_code=503, detail="Vuelos en tiempo real no disponibles")
    return RedirectResponse(url)

@app.get("/predicciones")
def redirect_vuelos_en_tiempo_real():
    """
    Redirige a la página del microservicio de las predicciones.
    """
    url = MICROSERVICIOS.get("predicciones")
    if not url:
        raise HTTPException(status_code=503, detail="Prediccines no disponible")
    return RedirectResponse(url)

