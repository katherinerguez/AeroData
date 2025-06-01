import os
import sys
import json
import hashlib
import pickle
import logging
from datetime import datetime, timedelta
import logging.handlers

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import pandas as pd
import dask.dataframe as dd
import plotly

from diskcache import Cache
from app.graficos.database import get_db_url
import app.graficos.plots as plots
# from app.graficos.database import get_db_url
# import app.graficos.plots as plots

# ———————————— Configuración de logging ————————————
def setup_logging():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    log_filename = f"logs/app_{datetime.now().strftime('%Y%m%d')}.log"
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    if not logger.hasHandlers():
        file_handler = logging.handlers.RotatingFileHandler(
            log_filename, maxBytes=5*1024*1024, backupCount=5
        )
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

setup_logging()
logger = logging.getLogger(__name__)

# App y configuración
app = FastAPI()
templates = Jinja2Templates(directory="app/graficos/templates")
cache = Cache("./plot_cache")

def get_cache_key(func_name: str, start_date: str, end_date: str,
                  selected_route: str, selected_plane: str,
                  selected_airline: tuple, selected_airport: str) -> str:
    args = (func_name, start_date, end_date, selected_route,
            selected_plane, selected_airline, selected_airport)
    return hashlib.md5(pickle.dumps(args)).hexdigest()

@app.on_event("startup")
def precompute_default_graphs():
    logger.info("=== INICIANDO precomputación de gráficos por defecto ===")
    db_url = get_db_url()

    min_date, max_date = plots.get_min_max_dates(db_url)
    last_year = (max_date - timedelta(days=365)).strftime("%Y-%m-%d")
    max_date_str = max_date.strftime("%Y-%m-%d")

    start_date = last_year
    end_date = max_date_str
    selected_route = None
    selected_plane = None
    selected_airline = tuple()
    selected_airport = None

    df, airports_df = plots.load_data(db_url, start_date=start_date, end_date=end_date)
    df["fl_date"] = dd.to_datetime(df["fl_date"], errors="coerce")
    df["route"] = df["origin_airport_id"].astype(str) + " → " + df["dest_airport_id"].astype(str)

    plot_funcs = [
       # plots.plot_delay_by_airport,
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
        lambda d: plots.plot_delay_by_state(d, airports_df),
        plots.plot_most_diverted_airports,
        plots.plot_monthly_delay_trend,
    ]

    for func in plot_funcs:
        func_name = func.__name__ if hasattr(func, "__name__") else repr(func)
        key = get_cache_key(func_name, start_date, end_date,
                            selected_route or "", selected_plane or "",
                            selected_airline, selected_airport or "")
        if key not in cache:
            logger.info(f"Precomputando gráfico '{func_name}'...")
            try:
                fig = func(df) if "delay_by_state" not in func_name else func(df, airports_df)
                cache.set(key, fig, expire=24 * 3600)
                logger.info(f"  → Guardado en caché (key={key[:8]}…)")
            except Exception as e:
                logger.error(f"  ❌ Error precomputando '{func_name}': {e}", exc_info=True)
    logger.info("=== FIN precomputación de gráficos por defecto ===")

@app.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    start_date: str = Query(None),
    end_date: str = Query(None),
    selected_route: str = Query(None),
    selected_plane: str = Query(None),
    selected_airline: list[str] = Query(default_factory=list),
    selected_airport: str = Query(None)
):
    logger.info(
        f"[REQUEST] dashboard -> start_date={start_date}, "
        f"end_date={end_date}, route={selected_route}, "
        f"plane={selected_plane}, airline={selected_airline}, airport={selected_airport}"
    )

    db_url = get_db_url()
    min_date, max_date = plots.get_min_max_dates(db_url)
    last_year = (max_date - timedelta(days=365)).strftime("%Y-%m-%d")
    max_date_str = max_date.strftime("%Y-%m-%d")

    try:
        user_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        user_end_date = None

    warning_message = None
    if user_end_date and user_end_date > max_date:
        end_date = max_date_str
        warning_message = f"La fecha final seleccionada fue ajustada al último día disponible: {max_date_str}"
        logger.warning(warning_message)

    if start_date and end_date and start_date > end_date:
        start_date, end_date = end_date, start_date
        logger.info("Fechas invertidas para corregir orden")

    start_date = start_date or last_year
    end_date = end_date or max_date_str
    logger.info(f"Fechas usadas → start_date={start_date}, end_date={end_date}")

    df, airports_df = plots.load_data(db_url, start_date=start_date, end_date=end_date)
    df["fl_date"] = dd.to_datetime(df["fl_date"], errors="coerce")

    if selected_airline:
        df = df[df["op_carrier"].isin(selected_airline)]
    if selected_plane:
        df = df[df["op_carrier_fl_num"] == selected_plane]

    df["route"] = df["origin_airport_id"].astype(str) + " → " + df["dest_airport_id"].astype(str)

    if selected_route:
        df = df[df["route"] == selected_route]

    if selected_airport:
        df = df[
            (df["origin_airport_id"] == selected_airport) |
            (df["dest_airport_id"] == selected_airport)
        ]

    row_count = df.map_partitions(len).compute().sum()
    if row_count == 0:
        logger.warning("No hay datos para los filtros especificados.")
        full_df, _ = plots.load_data(db_url, start_date=start_date, end_date=end_date)
        full_df["route"] = full_df["origin_airport_id"].astype(str) + " → " + full_df["dest_airport_id"].astype(str)
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "start_date": start_date,
            "end_date": end_date,
            "warning_message": warning_message,
            "no_data": True,
            "routes": full_df["route"].dropna().unique().compute().tolist(),
            "selected_route": selected_route,
            "planes": full_df["op_carrier_fl_num"].dropna().unique().compute().tolist(),
            "selected_plane": selected_plane,
            "airlines": full_df["op_carrier"].dropna().unique().compute().tolist(),
            "selected_airline": selected_airline,
            "valid_airports": sorted(
                set(full_df["origin_airport_id"].dropna().unique().compute().tolist() +
                    full_df["dest_airport_id"].dropna().unique().compute().tolist())
            ),
            "selected_airport": selected_airport,
        })

    graph_data = {}
    plot_funcs = [
        #plots.plot_delay_by_airport,
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
        lambda d: plots.plot_delay_by_state(d, airports_df),
        plots.plot_most_diverted_airports,
        plots.plot_monthly_delay_trend,
    ]

    for i, func in enumerate(plot_funcs, start=1):
        func_name = func.__name__ if hasattr(func, "__name__") else repr(func)
        key = get_cache_key(func_name, start_date, end_date,
                            selected_route or "", selected_plane or "",
                            tuple(selected_airline), selected_airport or "")
        if key in cache:
            fig = cache[key]
            logger.info(f"Usando gráfico cacheado: {func_name}")
        else:
            logger.info(f"Generando gráfico en vivo: {func_name}")
            fig = func(df) if "delay_by_state" not in func_name else func(df, airports_df)
            cache.set(key, fig, expire=24 * 3600)

        graph_data[f"graph{i}"] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "start_date": start_date,
        "end_date": end_date,
        "warning_message": warning_message,
        "no_data": False,
        "graph_data": graph_data,
        "routes": df["route"].dropna().unique().compute().tolist(),
        "selected_route": selected_route,
        "planes": df["op_carrier_fl_num"].dropna().unique().compute().tolist(),
        "selected_plane": selected_plane,
        "airlines": df["op_carrier"].dropna().unique().compute().tolist(),
        "selected_airline": selected_airline,
        "valid_airports": (
            set(df["origin_airport_id"].dropna().unique().compute().tolist() +
                df["dest_airport_id"].dropna().unique().compute().tolist())
        ),
        "selected_airport": selected_airport,
    })
