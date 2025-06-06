from flask import Flask, render_template
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from waitress import serve 
import os

load_dotenv()

app = Flask(__name__)

# Configuración de Supabase
SUPABASE_URL = os.getenv('supabase_url_realtime')
SUPABASE_KEY = os.getenv('superbase_key_realtime') 

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/")
def index():
    try:
        # Obtener datos de Supabase
        result = supabase.table("current flights").select("origin_country, est_arrival_airport").execute()
        datos = result.data  
        
        df = pd.DataFrame(datos)
        df_vuelos_activos = df[df['est_arrival_airport'] != True]
       
        df_grouped = df_vuelos_activos.groupby("origin_country").size().reset_index(name="count")
        
        # Grafico de barras horizontales para la cantidad de vuelos por paises
        fig = px.bar(
            df_grouped,
            x="count",
            y="origin_country",  
            orientation='h',           
            title="Cantidad de vuelos activos por país",
            labels={"count": "Cantidad de vuelos", "origin_country": "País"}
        )
        graph_html = fig.to_html(full_html=False)
        
        return render_template("diseno.html", graph_html=graph_html)
    
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":

    serve(app, host='0.0.0.0', port=5000)  