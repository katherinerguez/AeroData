from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles  
import os

from supabase import create_client, Client
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import requests

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")  

router = APIRouter(prefix="/realtime-flights")
templates = Jinja2Templates(directory="templates")

def generate_flight_chart():
    """Genera el gráfico HTML de vuelos activos"""
    try:
        # Obtener datos de Supabase
        database=requests.get('https://database-realtime.onrender.com/tabla/current%20flights')
        
        result = database.json()
        datos = pd.DataFrame(result)  
        
        df = datos[["origin_country", "est_arrival_airport"]]
        
        df_vuelos_activos = df[df['est_arrival_airport'] != True]
       
        df_grouped = df_vuelos_activos.groupby("origin_country").size().reset_index(name="count")
        
        # Ordenar por cantidad de vuelos
        df_grouped = df_grouped.sort_values("count", ascending=False)
        
        fig = px.bar(
            df_grouped,
            x="count",
            y="origin_country",  
            orientation='h',
            title="Cantidad de vuelos activos por país",
            labels={"count": "Cantidad de vuelos", "origin_country": "País"},
            color="count",
            color_continuous_scale=px.colors.sequential.Viridis,
            height=800
        )
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    except Exception as e:
        return f"<div class='error'>Error generando gráfico: {str(e)}</div>"

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
   
    graph_html = generate_flight_chart()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "graph_html": graph_html,
        "titulo": "Vuelos en tiempo real"
    })

app.include_router(router)