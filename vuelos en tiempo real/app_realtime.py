from flask import Flask, render_template, jsonify
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from waitress import serve 
import os
import plotly.colors

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
        df_grouped = df_grouped.sort_values('count', ascending=True) #ordenarlos de maner ascendente
        # Grafico de barras horizontales para la cantidad de vuelos por paises
        custom_colors = plotly.colors.qualitative.Dark2 # predefinir colores para cada pais
        fig = px.bar(df_grouped, 
                 x='count',
                 y='origin_country',
                 orientation='h',
                 title='Cantidad de vuelos activos por país',
                 color='origin_country',  
                 color_discrete_sequence=custom_colors  
                )

        fig.update_layout(
            xaxis_title='Cantidad de vuelos',
            yaxis_title='País',
            title_x=0.5,
            height=750,  
            margin=dict(l=100, r=50, t=80, b=50),  
            showlegend=False 
        )  

        graph_html = fig.to_html(full_html=False)
        return render_template("diseno.html", graph_html=graph_html)
    
    except Exception as e:
        return f"Error: {str(e)}", 500
@app.route('/get_location')
def location(): 
    """
    Esta funcion es para extraer las localizaciones de los vuelos y 
    representarlos en un mapa donde se muestra su ubicacion en tiempo real en un mapa interactivo
    """
    try:
        location = supabase.table("current flights").select("icao24, latitude, longitude").execute()
        data_location = location.data  
            
        return jsonify(data_location)

    except Exception as e:
        return f"Error en obtener las posiciones"

if __name__ == "__main__":

    serve(app, host='0.0.0.0', port=5000)  