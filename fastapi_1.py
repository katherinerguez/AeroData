from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import dask.dataframe as dd
from sqlalchemy import create_engine
import plotly.express as px
import plotly
import json
import os

# Crear carpeta de templates si no existe
os.makedirs("templates", exist_ok=True)

# Crear archivo dashboard.html si no existe
html_template_path = "templates/dashboard.html"
if not os.path.exists(html_template_path):
    with open(html_template_path, "w") as f:
        f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard de Vuelos</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f9f9f9; }
        h1 { color: #333; }
        #graph1, #graph2 { margin-top: 40px; }
    </style>
</head>
<body>
    <h1>📊 Dashboard de Vuelos</h1>
    <div id="graph1"></div>
    <div id="graph2"></div>

    <script>
        var graph1 = {{ graph1 | safe }};
        var graph2 = {{ graph2 | safe }};
        Plotly.newPlot("graph1", graph1.data, graph1.layout);
        Plotly.newPlot("graph2", graph2.data, graph2.layout);
    </script>
</body>
</html>
        """)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Conexión a PostgreSQL (asegúrate que los datos son correctos)
db_url = "postgresql+psycopg2://postgres:Jennifer2004*@localhost:5432/fligth-database"

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    # Leer la tabla flights con Dask
    df = dd.read_sql_table(
        table_name='flights',  # Nombre de la tabla
        con=db_url,            # Usar la cadena de conexión directamente
        index_col='flight_id'  # Columna de índice para particionar los datos
    )

    # Procesar: calcular delay promedio por aeropuerto y vuelos por aerolínea
    delay_by_airport = df.groupby("origin_airport_id")["arr_delay"].mean().compute().nlargest(10)
    flight_counts = df["op_carrier"].value_counts().compute().nlargest(10)

    # Gráfico 1: delay promedio
    fig1 = px.bar(
        x=delay_by_airport.index.astype(str),
        y=delay_by_airport.values,
        labels={"x": "ID del Aeropuerto", "y": "Delay Promedio (min)"},
        title="Top 10 Aeropuertos con Mayor Delay Promedio",
        color=delay_by_airport.values,
        color_continuous_scale="Reds"
    )

    # Gráfico 2: vuelos por aerolínea
    fig2 = px.pie(
        names=flight_counts.index,
        values=flight_counts.values,
        title="Distribución de Vuelos por Aerolínea"
    )

    # Convertir gráficos a JSON
    graph1JSON = json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder)
    graph2JSON = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "graph1": graph1JSON,
        "graph2": graph2JSON
    })

