import os
import sys
import json
import hashlib
import pickle
import logging
import logging.handlers
from diskcache import Cache
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from fastapi import FastAPI, Request, Query, HTTPException, Form, Request, Body, Depends
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from urllib.parse import urlparse, parse_qs
import bcrypt
import pandas as pd
import dask.dataframe as dd
import plotly
from datetime import datetime, timedelta
from auth import get_current_user,registrar_usuario
from database import get_db_url,get_usuario,save_query_to_history,get_user_query_history
import plots as plots
# from app.graficos.database import get_db_url
# import app.graficos.plots as plots

security = HTTPBasic()
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
templates = Jinja2Templates(directory="app/templates")
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
async def raiz(request: Request):
    print(1)
    auth_header = request.headers.get("authorization")
    if auth_header:
        return RedirectResponse(url="/dashboard")
    return RedirectResponse(url="/login")
from fastapi import Body

@app.post("/login_comprobar")
async def login(payload: dict = Body(...)):
    username = payload.get("username")
    password = payload.get("password")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Faltan usuario o contraseña")

    user_data = get_usuario(username)

    if not user_data:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    stored_hash = user_data[1]

    if not bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    return {"message": "Login exitoso", "username": username}

@app.get("/login", response_class=HTMLResponse)
async def mostrar_login():
    html_path = os.path.join(os.path.dirname(__file__), "login.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo login.html no encontrado")
@app.get("/register", response_class=HTMLResponse)
async def mostrar_registro():
    html_path = os.path.join(os.path.dirname(__file__), "register.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo register.html no encontrado")

@app.post("/register")
async def register(username: str = Form(...), password: str = Form(...)):
    if not username or not password:
        raise HTTPException(status_code=400, detail="Faltan usuario o contraseña")
    
    try:
        registrar_usuario(username, password, role="usuario")
        return {"message": "Usuario registrado correctamente"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/history", response_class=HTMLResponse)
async def get_history(request: Request, user: dict = Depends(get_current_user)):
    """Muestra el historial del usuario filtrado solo con type='Graficos', y descompone los filtros desde la URL"""
    try:
        history = get_user_query_history(user["username"])

        # Traducción de nombres de filtros a etiquetas más amigables
        filtro_labels = {
            "start_date": "Fecha inicial",
            "end_date": "Fecha final",
            "selected_route": "Ruta seleccionada",
            "selected_plane": "Avión seleccionado",
            "selected_airline": "Aerolínea seleccionada",
            "selected_airport": "Aeropuerto seleccionado"
        }

        processed_history = []
        for item in history:
            if item.get("type") != "Graficos":
                continue

            url = item.get("query", "#")
            filtros = {}

            try:
                parsed = urlparse(url)
                query_params = parse_qs(parsed.query)

                for key, val in query_params.items():
                    etiqueta = filtro_labels.get(key, key)
                    filtros[etiqueta] = ", ".join(val)

            except Exception as e:
                filtros = {"Error": "No se pudieron leer los filtros"}

            processed_history.append({
                "query": url,
                "filtros": filtros
            })

        return templates.TemplateResponse("history.html", {
            "request": request,
            "username": user["username"],
            "history": processed_history
        })

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener historial: {str(e)}"
        )



# @app.post("/execute")
# async def run_sql(query: SQLQuery, user: dict = Depends(get_current_user)):
#     try:
#         # Guardar en el historial primero
#         save_query_to_history(user["username"], query.query)
        
#         # Si no es admin, aplicar restricciones
#         if user["role"] != "admin":
#             # Verificar que sea SELECT
#             if not query.query.strip().lower().startswith("select"):
#                 raise HTTPException(
#                     status_code=403,
#                     detail="Solo puedes realizar consultas SELECT"
#                 )
            
#             # Verificar tablas permitidas
#             tablas_permitidas = ['airports', 'airlines', 'flights']
#             query_lower = query.query.lower()
            
#             if not any(f"from {tabla}" in query_lower or f"join {tabla}" in query_lower 
#                       for tabla in tablas_permitidas):
#                 raise HTTPException(
#                     status_code=403,
#                     detail="Solo puedes consultar las tablas: airports, airlines y flights"
#                 )
        
#         # Ejecutar la consulta
#         result = execute_sql(query.query)
#         df = pd.DataFrame(result)
#         return {"result": df.to_dict(orient="records")}
    
#     except HTTPException:
#         raise  # Re-lanzar excepciones HTTP que ya hemos capturado
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    start_date: str = Query(None),
    end_date: str = Query(None),
    selected_route: str = Query(None),
    selected_plane: str = Query(None),
    selected_airline: list[str] = Query(default_factory=list),
    selected_airport: str = Query(None), 
    username: str = Query(None),
    credentials: HTTPBasicCredentials = Depends(security)
):
    # Obtener y validar usuario
    try:
        user = get_current_user(credentials)
        current_username = user["username"]
    except HTTPException as e:
        logger.error(f"Error de autenticación: {str(e)}")
        return RedirectResponse(url="/login")

    # Verificar consistencia entre parámetro y usuario autenticado
    if username and username != current_username:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    username = username or current_username
    # Obtener el usuario autenticado desde los headers
    auth_header = request.headers.get("authorization")
    
    
    logger.info(
        f"[REQUEST] dashboard -> start_date={start_date}, "
        f"end_date={end_date}, route={selected_route}, "
        f"plane={selected_plane}, airline={selected_airline}, airport={selected_airport}"
    )
    
    db_url = get_db_url()
    min_date, max_date = plots.get_min_max_dates(db_url)
    last_year = (max_date - timedelta(days=365)).strftime("%Y-%m-%d")
    max_date_str = max_date.strftime("%Y-%m-%d")
    
    # Guardar la URL de la consulta como historial
    base_url = str(request.url_for("dashboard"))
    query_params = []
    print(base_url)
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
        
        for airline in selected_airline:
            query_params.append(f"selected_airline={airline}")
            
    if selected_plane:
        df = df[df["op_carrier_fl_num"] == selected_plane]
        
        query_params.append(f"selected_plane={selected_plane}")

    df["route"] = df["origin_airport_id"].astype(str) + " → " + df["dest_airport_id"].astype(str)

    if selected_route:
        df = df[df["route"] == selected_route]

    if selected_airport:
        df = df[
            (df["origin_airport_id"] == selected_airport) |
            (df["dest_airport_id"] == selected_airport)
        ]

    if start_date:
        query_params.append(f"start_date={start_date}")
    if end_date:
        query_params.append(f"end_date={end_date}")
    if selected_route:
        query_params.append(f"selected_route={selected_route}")
    if selected_airport:
        query_params.append(f"selected_airport={selected_airport}")

    full_query = base_url + "?" + "&".join(query_params) if query_params else base_url
    logger.info(f"URL guardada en historial: {full_query}")

    try:
        if not username:
            raise ValueError("Nombre de usuario no puede ser nulo")
            
        save_query_to_history(username, full_query)
    except Exception as e:
        logger.error(f"Error guardando historial: {str(e)}")
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

# if __name__ == "__main__":
#     import uvicorn
#     port = int(os.environ.get("PORT", 8000))
#     uvicorn.run("app.graficos.main:app", host="0.0.0.0", port=port, reload=False)
