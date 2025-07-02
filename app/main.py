from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.main import app as api_app
from app.consultas.main import app as consultas_app
from app.graficos.main import app as graficos_app

app = FastAPI()

app.mount("/api", api_app)
app.mount("/consultas", consultas_app)
app.mount("/graficos", graficos_app)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
