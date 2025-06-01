from fastapi import FastAPI
from app.graficos.main import app as graficos_app
from app.api.main import app as api_app
from app.consultas.main import app as consultas_app

app = FastAPI()

app.mount("/api", api_app)
app.mount("/graficos", graficos_app)
app.mount("/consultas", consultas_app)
