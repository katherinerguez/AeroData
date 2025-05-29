from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import json
import plotly
from database import get_db_url
import dask.dataframe as dd
import plots
from datetime import datetime, timedelta
import pandas as pd
from diskcache import Cache
import hashlib
import pickle

app = FastAPI()
templates = Jinja2Templates(directory="templates")
cache = Cache("./plot_cache")

def get_cache_key(*args, **kwargs):
    """Genera un hash de los argumentos para usarlo como clave"""
    return hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

@app.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    start_date: str = Query(None),
    end_date: str = Query(None),
    selected_route: str = Query(None),
    selected_plane: str = Query(None),
    selected_airline: list = Query(None),
    selected_airport: str = Query(None)
):
    db_url = get_db_url()

    try:
        # Obtener rango de fechas mínimo y máximo
        min_date, max_date = plots.get_min_max_dates(db_url)
        last_year = (max_date - timedelta(days=365)).strftime("%Y-%m-%d")
        max_date_str = max_date.strftime("%Y-%m-%d")

        # Validar end_date: si es mayor que max_date, usar max_date
        try:
            user_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()  # Convertimos a date
        except (TypeError, ValueError):
            user_end_date = None

        if user_end_date and user_end_date > max_date:
            end_date = max_date_str  # Ajustar al máximo disponible
            warning_message = f"La fecha final seleccionada fue ajustada al último día disponible: {max_date_str}"
        else:
            warning_message = None
    
        if start_date and end_date:
            if start_date>end_date:
                start_date,end_date=end_date,start_date
                
        # Establecer fechas por defecto
        start_date = start_date or last_year
        end_date = end_date or max_date_str
        print(end_date)
        # Cargar datos filtrados por fecha
        df, airports_df = plots.load_data(db_url, start_date=start_date, end_date=end_date)
        print("data cargada")
        # Convertir fl_date a datetime si no lo está ya
        if not isinstance(df["fl_date"].dtype, pd.DatetimeTZDtype):
            print(0)
            df["fl_date"] = dd.to_datetime(df["fl_date"])
        print(9)
        # Filtrar por aerolínea si hay selección
        if selected_airline:
            df = df[df["op_carrier"].isin(selected_airline)]
        print(8)
        # Filtrar por número de vuelo si hay selección
        if selected_plane:
            df = df[df["op_carrier_fl_num"] == selected_plane]
        print(10)
        # Crear columna de ruta
        df["route"] = df["origin_airport_id"].astype(str) + " → " + df["dest_airport_id"].astype(str)
        # Obtener listas únicas basadas SOLO en los datos filtrados
        print(10.0)
        unique_routes = df["route"].dropna().unique().compute().tolist()
        unique_planes = df["op_carrier_fl_num"].dropna().unique().compute().tolist()
        unique_airlines = df["op_carrier"].dropna().unique().compute().tolist()
        print(11)

        valid_airports = df["origin_airport_id"].dropna().unique().compute().tolist()
        valid_airports += df["dest_airport_id"].dropna().unique().compute().tolist()
        valid_airports = sorted(set(valid_airports))
        print(12)

        # Top aerolíneas y aviones globales (opcional)
        top_planes = plots.get_top_planes(db_url, limit=5)
        top_airlines = plots.get_top_airlines(db_url, limit=5)
        print("top creados")
        # Valores por defecto
        selected_plane = selected_plane or (top_planes[0] if top_planes else None)
        selected_airline = selected_airline or (top_airlines if top_airlines else [])
        selected_route = selected_route or (unique_routes[0] if unique_routes else None)
        print("select configurados")
        # Validar selecciones contra listas filtradas
        if selected_route and selected_route not in unique_routes:
            selected_route = unique_routes[0] if unique_routes else None

        if selected_plane and selected_plane not in unique_planes:
            selected_plane = unique_planes[0] if unique_planes else None

        if selected_airline:
            if isinstance(selected_airline, list):
                selected_airline = [a for a in selected_airline if a in unique_airlines]
            else:
                selected_airline = [selected_airline] if selected_airline in unique_airlines else []

        if selected_airport and selected_airport not in valid_airports:
            selected_airport = valid_airports[0] if valid_airports else None

        # Aplicar filtro por aeropuerto si existe
        if selected_airport:
            df = df[
                (df["origin_airport_id"] == selected_airport) |
                (df["dest_airport_id"] == selected_airport)
            ]
            
        if df.map_partitions(len).compute().sum() == 0:
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "start_date": start_date,
                "end_date": end_date,
                "warning_message": warning_message,
                "no_data": True,  # Usamos esta variable para mostrar un mensaje en HTML
                "routes": [],
                "selected_route": selected_route,
                "planes": [],
                "selected_plane": selected_plane,
                "airlines": [],
                "selected_airline": selected_airline,
                "valid_airports": valid_airports,
                "selected_airport": selected_airport,
            })
            
        print("vamos a empezar con los graficos")
        # Generar gráficos
        plot_funcs = [
            plots.plot_delay_by_airport,
            plots.plot_flight_counts,
            plots.plot_arrival_delay_distribution,
            plots.plot_cancelled_flights,
            plots.plot_airtime_by_route,
            plots.plot_flights_by_date,
            plots.plot_delay_by_hour,
            plots.plot_delay_by_airline,
            plots.plot_distance_vs_airtime,
            plots.plot_cancellation_rate,
            plots.plot_most_common_routes,
            plots.plot_delay_by_weekday,
            lambda df: plots.plot_delay_by_state(df, airports_df),
            plots.plot_most_diverted_airports,
            plots.plot_monthly_delay_trend,
        ]
        print("graficos creados")
        figs = []
        for i, func in enumerate(plot_funcs):
            func_name = func.__name__ if hasattr(func, "__name__") else f"plot_func_{i}"
            key = get_cache_key(func_name, start_date, end_date, selected_route, selected_plane, selected_airline)
            print("grafico",i)
            if key in cache:
                fig = cache[key]
            else:
                fig = func(df) if func_name != "plot_delay_by_state" else func(df, airports_df)
                cache.set(key, fig, expire=3600)  # Cache por 1 hora

            figs.append(fig)
        print("creadas las figs")
        graphs_json = [json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder) for fig in figs]

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "start_date": start_date,
            "end_date": end_date,
            "routes": unique_routes,
            "selected_route": selected_route,
            "planes": unique_planes,
            "selected_plane": selected_plane,
            "airlines": top_airlines,
            "selected_airline": selected_airline,
            "valid_airports": valid_airports,
            "selected_airport": selected_airport,
            **{f"graph{i+1}": graph for i, graph in enumerate(graphs_json)}
        })

    except Exception as e:
        print(f"Error en el dashboard: {e}")
        return f"error,{e}"
