from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import json
import plotly
from app.graficos.database import get_db_url
import dask.dataframe as dd
import app.graficos.plots as plots
from datetime import datetime, timedelta
import pandas as pd
from diskcache import Cache
import hashlib
import pickle

import logging
from logging.handlers import RotatingFileHandler
import sys
import os
from datetime import datetime

def setup_logging():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    log_filename = f"logs/app_{datetime.now().strftime('%Y%m%d')}.log"
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    
    file_handler = RotatingFileHandler(
        log_filename, maxBytes=1024*1024*5, backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

setup_logging()

logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="app.graficos.templates")
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
    logger.info(
        f"Iniciando dashboard con parámetros: start_date={start_date}, end_date={end_date}, "
        f"selected_route={selected_route}, selected_plane={selected_plane}, "
        f"selected_airline={selected_airline}, selected_airport={selected_airport}"
    )
    
    db_url = get_db_url()

    try:
        logger.info("Obteniendo rango de fechas mínimo y máximo")
        min_date, max_date = plots.get_min_max_dates(db_url)
        last_year = (max_date - timedelta(days=365)).strftime("%Y-%m-%d")
        max_date_str = max_date.strftime("%Y-%m-%d")

        try:
            user_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            user_end_date = None
            logger.debug("No se proporcionó end_date o formato inválido")

        if user_end_date and user_end_date > max_date:
            end_date = max_date_str
            warning_message = f"La fecha final seleccionada fue ajustada al último día disponible: {max_date_str}"
            logger.warning(warning_message)
        else:
            warning_message = None

        if start_date and end_date:
            if start_date > end_date:
                start_date, end_date = end_date, start_date
                logger.info("Fechas invertidas para corregir orden")
                
        start_date = start_date or last_year
        end_date = end_date or max_date_str
        logger.info(f"Fechas finales usadas: start_date={start_date}, end_date={end_date}")

        logger.info("Cargando datos filtrados por fecha")
        df, airports_df = plots.load_data(db_url, start_date=start_date, end_date=end_date)
        
        row_count = df.map_partitions(len).compute().sum()
        logger.info(f"Datos cargados - Número de registros: {row_count}")

        if not isinstance(df["fl_date"].dtype, pd.DatetimeTZDtype):
            logger.debug("Convirtiendo fl_date a datetime")
            df["fl_date"] = dd.to_datetime(df["fl_date"])

        if selected_airline:
            logger.info(f"Filtrando por aerolíneas: {selected_airline}")
            df = df[df["op_carrier"].isin(selected_airline)]
            new_count = df.map_partitions(len).compute().sum()
            logger.info(f"Registros después de filtrar aerolíneas: {new_count}")

        if selected_plane:
            logger.info(f"Filtrando por vuelo: {selected_plane}")
            df = df[df["op_carrier_fl_num"] == selected_plane]
            new_count = df.map_partitions(len).compute().sum()
            logger.info(f"Registros después de filtrar vuelo: {new_count}")

        df["route"] = df["origin_airport_id"].astype(str) + " → " + df["dest_airport_id"].astype(str)
        
        logger.info("Calculando listas únicas de rutas, aviones y aerolíneas")
        unique_routes = df["route"].dropna().unique().compute().tolist()
        unique_planes = df["op_carrier_fl_num"].dropna().unique().compute().tolist()
        unique_airlines = df["op_carrier"].dropna().unique().compute().tolist()
        logger.info(f"Encontradas {len(unique_routes)} rutas únicas, {len(unique_planes)} aviones únicos, {len(unique_airlines)} aerolíneas únicas")

        valid_airports = df["origin_airport_id"].dropna().unique().compute().tolist()
        valid_airports += df["dest_airport_id"].dropna().unique().compute().tolist()
        valid_airports = sorted(set(valid_airports))
        logger.info(f"Encontrados {len(valid_airports)} aeropuertos válidos")

        logger.info("Obteniendo top aerolíneas y aviones")
        top_planes = plots.get_top_planes(db_url, limit=5)
        top_airlines = plots.get_top_airlines(db_url, limit=5)
        
        selected_plane = selected_plane or (top_planes[0] if top_planes else None)
        selected_airline = selected_airline or (top_airlines if top_airlines else [])
        selected_route = selected_route or (unique_routes[0] if unique_routes else None)
        logger.info(f"Selecciones finales: route={selected_route}, plane={selected_plane}, airline={selected_airline}")

        if selected_airport:
            logger.info(f"Filtrando por aeropuerto: {selected_airport}")
            df = df[
                (df["origin_airport_id"] == selected_airport) |
                (df["dest_airport_id"] == selected_airport)
            ]
            new_count = df.map_partitions(len).compute().sum()
            logger.info(f"Registros después de filtrar aeropuerto: {new_count}")

        if row_count == 0:
            logger.warning("No hay datos disponibles para los filtros seleccionados")
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "start_date": start_date,
                "end_date": end_date,
                "warning_message": warning_message,
                "no_data": True,
                "routes": [],
                "selected_route": selected_route,
                "planes": [],
                "selected_plane": selected_plane,
                "airlines": [],
                "selected_airline": selected_airline,
                "valid_airports": valid_airports,
                "selected_airport": selected_airport,
            })
            
        logger.info("Generando gráficos")
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
        
        figs = []
        cache_hits = 0
        cache_misses = 0
        
        for i, func in enumerate(plot_funcs):
            func_name = func.__name__ if hasattr(func, "__name__") else f"plot_func_{i}"
            key = get_cache_key(func_name, start_date, end_date, selected_route, selected_plane, selected_airline)
            
            if key in cache:
                fig = cache[key]
                cache_hits += 1
                logger.debug(f"Gráfico {i+1} ({func_name}) obtenido de caché")
            else:
                fig = func(df) if func_name != "plot_delay_by_state" else func(df, airports_df)
                cache.set(key, fig, expire=3600)
                cache_misses += 1
                logger.debug(f"Gráfico {i+1} ({func_name}) generado y almacenado en caché")

            figs.append(fig)
        
        logger.info(f"Gráficos generados - Cache hits: {cache_hits}, Cache misses: {cache_misses}")
        graphs_json = [json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder) for fig in figs]

        logger.info("Preparando respuesta exitosa")
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
            **{f"graph{i+1}": graph for i, graph in enumerate(graphs_json)}}
        )

    except Exception as e:
        logger.error(f"Error en el dashboard: {str(e)}", exc_info=True)
        return f"Ha ocurrido un error {e}"
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)