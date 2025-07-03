from fastapi import FastAPI, APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from supabase import create_client, Client
from dotenv import load_dotenv
import os
import logging
logging.basicConfig(level=logging.ERROR)

import pandas as pd
import plotly.express as px
import plotly.colors

load_dotenv()

SUPABASE_URL = os.getenv('supabase_url_realtime')
SUPABASE_KEY = os.getenv('superbase_key_realtime')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()
router = APIRouter(prefix="/realtime-flights")
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    try:
        # Obtener datos de Supabase
        result = supabase.table("current flights").select("origin_country, est_arrival_airport").execute()
        datos = result.data
        
        df = pd.DataFrame(datos)
        df_vuelos_activos = df[df['est_arrival_airport'] != True]
        
        df_grouped = df_vuelos_activos.groupby("origin_country").size().reset_index(name="count")
        df_grouped = df_grouped.sort_values('count', ascending=True)
        
        custom_colors = plotly.colors.qualitative.Dark2
        fig = px.bar(df_grouped,
                     x='count',
                     y='origin_country',
                     orientation='h',
                     title='Cantidad de vuelos activos por país',
                     color='origin_country',
                     color_discrete_sequence=custom_colors)
        
        fig.update_layout(
            xaxis_title='Cantidad de vuelos',
            yaxis_title='País',
            title_x=0.5,
            height=750,
            margin=dict(l=100, r=50, t=80, b=50),
            showlegend=False
        )
        
        graph_html = fig.to_html(full_html=False)
        return templates.TemplateResponse("diseno.html", {
            "request": request,
            "graph_html": graph_html,
            "titulo": "Vuelos en tiempo real"
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/get_location")
async def location():
    try:
        result = supabase.table("current flights").select("icao24, latitude, longitude").execute()
        return result.data
    except Exception as e:
        logging.error(f"Error al obtener posiciones: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

app.include_router(router)
