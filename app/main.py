from fastapi import FastAPI, Request, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import aiohttp

app = FastAPI()

# URLs de los microservicios (tal como están en Docker Compose o en tu proxy)
SERVICES = {
    "graficos": "http://graficos:8000",
    "consultas": "http://consultas:8001",
    "api": "http://api:8002",
}

# Sirve los archivos estáticos (CSS, imágenes, JS…)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Plantillas Jinja2
templates = Jinja2Templates(directory="app/templates")


async def call_service(service: str, path: str):
    if service not in SERVICES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Servicio desconocido: {service}"
        )
    url = f"{SERVICES[service]}/{path.lstrip('/')}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=2) as resp:
                resp.raise_for_status()
                return await resp.json()
    except aiohttp.ClientError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"El servicio {service} no respondió"
        )


@app.get("/")
async def home(request: Request):
    # Llamadas paralelas a cada microservicio
    graficos_data, consultas_data, api_data = await aiohttp.gather(
        call_service("graficos", "data/chart"),
        call_service("consultas", "stats/summary"),
        call_service("api", "process/status"),
    )

    # URLs para los botones de navegación
    service_urls = {
        "graficos": SERVICES["graficos"],
        "consultas": SERVICES["consultas"],
        "api": SERVICES["api"],
    }

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "graficos": graficos_data,
            "consultas": consultas_data,
            "api_data": api_data,
            "service_urls": service_urls,
        },
    )
