from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import pandas as pd
from extraccion import get_flights
from datetime import datetime

# import subprocess
# import sys

# print("✅ Ejecutando tests antes de arrancar la app…")
# result = subprocess.run([sys.executable, "-m", "pytest", "--disable-warnings"], capture_output=True, text=True)
# print("Test ejecutados")
# if result.returncode != 0:
#     print("❌ Los tests fallaron. Detalles:")
#     print(result.stdout)
#     print(result.stderr)
#     sys.exit(1)  # Detener la app si los tests fallan
# else:
#     print("🎉 Todos los tests pasaron. Arrancando app.\n")


app = FastAPI(title="Sistema de Búsqueda de Vuelos")

# Configuración de templates y archivos estáticos
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def show_search_form(request: Request):
    """Endpoint para mostrar el formulario de búsqueda"""
    try:
        df = get_flights()

        # Procesamiento de datos optimizado
        airports = sorted(df['departure_airport_name'].dropna().unique().tolist())
        airports_a = sorted(df['arrival_airport_name'].dropna().unique().tolist())
        aereoline = sorted(df['airline_name'].dropna().unique().tolist())

        flight_nums = sorted(df['op_carrier_fl_num'].dropna().astype(str).unique().tolist())
        hours = list(range(24))
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "airports1": airports,
            "airports2": airports_a,
            "aereoline":aereoline,
            "flight_nums": flight_nums,
            "hours": hours,
            "flights": None,
            "current_year": datetime.now().year,
            "page_title": "Búsqueda de Vuelos"
        })
        
    except Exception as e:
        print(e)
        return 
        # templates.TemplateResponse("error.html", {
        #     "request": request,
        #     "error_message": f"Error al cargar datos: {str(e)}"
        # })

@app.post("/search", response_class=HTMLResponse)
async def search_flights(
    request: Request,
    origin_airport_id: str = Form(None),
    destination_airport_id: str = Form(None),
    airline_name: str = Form(None),
    op_carrier_fl_num: str = Form(None),
    dep_hour: str = Form(None),
):
    try:
        df = get_flights()
        df['op_carrier_fl_num'] = df['op_carrier_fl_num'].astype(str)

        # Inicializa el query como todos verdaderos
        query = pd.Series(True, index=df.index)

        if origin_airport_id:
            query &= (df['departure_airport_name'] == origin_airport_id)

        if destination_airport_id:
            query &= (df['arrival_airport_name'] == destination_airport_id)

        if airline_name:
            query &= (df['airline_name'] == airline_name)

        if op_carrier_fl_num:
            query &= (df['op_carrier_fl_num'] == op_carrier_fl_num)

        if dep_hour:
            df['scheduled_dep_hour'] = pd.to_datetime(df['scheduled_dep']).dt.strftime('%H')
            query &= (df['scheduled_dep_hour'] == dep_hour)

        filtered_df = df[query]
        columns_to_show = ["flight_date","flight_status","departure_airport_name","arrival_airport_name","airline_name",
            "scheduled_dep_time", "scheduled_arr_time", "distance","predicted_delay"
        ]
        column_names_map = {
            "flight_status": "Estado del Vuelo",
            "departure_airport_name": "Aeropuerto de Salida",
            "arrival_airport_name": "Aeropuerto de Llegada",
            "airline_name": "Aerolínea",
            "scheduled_dep_time": "Hora Programada de Salida",
            "scheduled_arr_time": "Hora Programada de Llegada",
            "distance": "Distancia (millas)",
            "predicted_delay": "Retraso Predicho",
            "flight_date":"Fecha"}
        filtered_df_renamed = filtered_df[columns_to_show].rename(columns=column_names_map)
        
        flights = filtered_df_renamed.to_dict(orient="records")

        airports1 = sorted(df['departure_airport_name'].dropna().unique().tolist())
        airports2 = sorted(df['arrival_airport_name'].dropna().unique().tolist())
        aereoline = sorted(df['airline_name'].dropna().unique().tolist())
        flight_nums = sorted(df['op_carrier_fl_num'].dropna().astype(str).unique().tolist())
        hours = list(range(24))  # esto está bien

        message = None
        if not flights:
            message = "No se encontraron vuelos con los criterios seleccionados."

        return templates.TemplateResponse("index.html", {
            "request": request,
            "airports1": airports1,
            "airports2": airports2,
            "aereoline": aereoline,
            "flight_nums": flight_nums,
            "hours": hours,
            "flights": flights,
            "selected_airport1": origin_airport_id,
            "selected_airport2": destination_airport_id,
            "selected_aereoline": airline_name,
            "selected_flight": op_carrier_fl_num,
            "selected_hour": dep_hour,
            "message": message,
            "current_year": datetime.now().year,
            "page_title": "Resultados de Búsqueda"
        })
    except Exception as e:
        print(e)
        return HTMLResponse("Error en la búsqueda", status_code=500)


@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """Página de información sobre el sistema"""
    return templates.TemplateResponse("about.html", {
        "request": request,
        "page_title": "Acerca del Sistema"
    })