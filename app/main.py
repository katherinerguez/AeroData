from fastapi import FastAPI
from graficos.main import app as graficos_app
from api.main import app as api_app
from consultas.main import app as consultas_app

app = FastAPI()

app.mount("/graficos", graficos_app)
app.mount("/api", api_app)
app.mount("/consultas", consultas_app)
