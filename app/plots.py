import dask.dataframe as dd
import plotly.express as px
import pandas as pd  
#from app.graficos.database import create_engine
from database import create_engine

from sqlalchemy import text ,select, Table, MetaData

def get_min_max_dates(db_url):
    """Obtiene la fecha mínima y máxima de la tabla flights"""
    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT MIN(fl_date), MAX(fl_date) FROM flights")).fetchone()
    return result[0], result[1]


def get_top_planes(db_url, limit=5):
    """Obtiene los aviones más frecuentes"""
    engine = create_engine(db_url)
    query = f"""
        SELECT op_carrier_fl_num, COUNT(*) AS count
        FROM flights
        GROUP BY op_carrier_fl_num
        ORDER BY count DESC
        LIMIT {limit}
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df["op_carrier_fl_num"].tolist()


def get_top_airlines(db_url, limit=5):
    """Obtiene las aerolíneas más frecuentes"""
    engine = create_engine(db_url)
    query = f"""
        SELECT op_carrier, COUNT(*) AS count
        FROM flights
        GROUP BY op_carrier
        ORDER BY count DESC
        LIMIT {limit}
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df["op_carrier"].tolist()


from sqlalchemy import select, Table, MetaData, create_engine

def load_data(db_url, start_date=None, end_date=None, filters=None,limit=1000,offset=None):
    """
    Versión corregida usando SQLAlchemy Core correctamente
    """
    engine = create_engine(db_url)
    metadata = MetaData()

    flights = Table('flights', metadata, autoload_with=engine)
    airports = Table('airports', metadata, autoload_with=engine)

    query = select(flights)
    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)
    # Aplicar filtros de fecha
    if start_date and end_date:
        query = query.where(flights.c.fl_date.between(start_date, end_date))
    # Aplicar filtros adicionales
    if filters:
        for col, val in filters.items():
            if val and col in flights.c:
                if isinstance(val, list):
                    query = query.where(flights.c[col].in_(val))
                else:
                    query = query.where(flights.c[col] == val)
    
    # Cargar datos de vuelos
    flights_df = dd.read_sql_query(
        query,
        db_url,  # Pasar la URL directamente
        index_col="flight_id",
        npartitions=10
    )
    # Cargar datos de aeropuertos (usando el nombre de la tabla como string)
    airports_df = dd.read_sql_table(
        "airports",
        db_url,
        index_col="airport_id"
        ).persist()

        # Al final de load_data():
    for col in ["arr_delay", "dep_delay", "air_time", "distance"]:
        if col in flights_df.columns:
            flights_df[col] = dd.to_numeric(flights_df[col], errors='coerce')
    return flights_df, airports_df



def plot_delay_by_airport(df):
    """Top 10 aeropuertos con mayor retraso - usando solo df"""

    # Asegurar que 'arr_delay' sea numérico
    df["arr_delay"] = dd.to_numeric(df["arr_delay"], errors="coerce")
    df["origin_airport_id"] = df["origin_airport_id"].astype(str)

    # Agrupar por aeropuerto y obtener el promedio de retraso
    delay_by_airport = (
        df.groupby("origin_airport_id")["arr_delay"]
        .mean()
        .compute()
        .nlargest(10)
    )

    # Crear DataFrame temporal para graficar
    temp_df = pd.DataFrame({
        "origin_airport_id": delay_by_airport.index.astype(str),
        "arr_delay": delay_by_airport.values
    })

    # Graficar
    return px.bar(
        temp_df,
        x="origin_airport_id",
        y="arr_delay",
        title="Top 10 Aeropuertos con Mayor Retraso Promedio",
        labels={"origin_airport_id": "Aeropuerto", "arr_delay": "Retraso Promedio (min)"},
        color="arr_delay",
        color_continuous_scale="Reds",
        category_orders={"origin_airport_id": temp_df["origin_airport_id"].tolist()},
    )


def plot_flight_counts(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])

    flight_counts = df["op_carrier"].value_counts().compute().nlargest(10)
    return px.pie(
        names=flight_counts.index,
        values=flight_counts.values,
        title="Distribución de Vuelos por Aerolínea"
    )

def plot_arrival_delay_distribution(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])

    delays = df["arr_delay"].dropna().compute()
    return px.histogram(
        delays, nbins=50,
        title="Distribución de Retrasos de Llegada",
        labels={"value": "Retraso (min)"}
    )

def plot_cancelled_flights(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])

    cancelled_df = df[df["cancelled"] == True]["op_carrier"].value_counts().compute().nlargest(10)
    
    temp_df = pd.DataFrame({
        "op_carrier": cancelled_df.index,
        "cancelled_count": cancelled_df.values
    })

    return px.bar(
        temp_df,
        x="op_carrier",
        y="cancelled_count",
        labels={"op_carrier": "Aerolínea", "cancelled_count": "Cancelaciones"},
        title="Cancelaciones por Aerolínea",
        color="cancelled_count",
        color_continuous_scale="Blues"
    )


def plot_airtime_by_route(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])
    df["air_time"] = dd.to_numeric(df["air_time"], errors='coerce')

    df_subset = df[["origin_airport_id", "dest_airport_id", "air_time"]].dropna().compute()
    df_subset["route"] = df_subset["origin_airport_id"].astype(str) + " → " + df_subset["dest_airport_id"].astype(str)

    airtime_by_route = df_subset.groupby("route", as_index=False)["air_time"].mean()
    top_routes = airtime_by_route.nlargest(10, "air_time")
    top_routes.rename(columns={"air_time": "avg_air_time"}, inplace=True)

    plot_df = top_routes

    return px.bar(
        plot_df,  # Pasamos el DataFrame completo
        x="route",
        y="avg_air_time",
        labels={"route": "Ruta", "avg_air_time": "Tiempo Promedio (min)"},
        title="Top 10 Rutas con Mayor Tiempo Promedio de Vuelo",
        color="avg_air_time",
        color_continuous_scale="Purples"
    )

def plot_flights_by_date(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])
    date_counts = df["fl_date"].value_counts().compute().sort_index()

    # Convertir a DataFrame para Plotly
    plot_df = pd.DataFrame({
        'date': date_counts.index.astype(str),
        'count': date_counts.values
    })

    return px.line(
        plot_df,                   # Pasamos el DataFrame completo
        x='date',                  # Nombre de columna en el DataFrame
        y='count',                 # Nombre de columna en el DataFrame
        labels={"x": "Fecha", "y": "Cantidad de Vuelos"},
        title="Vuelos por Día"
    )

def plot_delay_by_hour(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])
    df["arr_delay"] = dd.to_numeric(df["arr_delay"], errors='coerce')
    df["crs_dep_time"] = df["crs_dep_time"].astype(str).str.slice(0,2).astype(int)

    hourly_delay = df.groupby("crs_dep_time")["arr_delay"].mean().compute()

    # Aseguramos que no tenga NaN
    hourly_delay = hourly_delay.dropna()

    # Convertimos a DataFrame explícito
    plot_df = pd.DataFrame({
        "hour": hourly_delay.index,
        "avg_delay": hourly_delay.values
    })

    return px.bar(
        plot_df,
        x="hour",
        y="avg_delay",
        labels={"hour": "Hora del Día", "avg_delay": "Retraso Promedio (min)"},
        title="Retraso Promedio por Hora del Día",
        color="avg_delay",
        color_continuous_scale="Oranges"
    )

def plot_delay_by_airline(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])
    df["arr_delay"] = dd.to_numeric(df["arr_delay"], errors='coerce')
    
    delay_by_airline = df.groupby("op_carrier")["arr_delay"].mean().compute().nlargest(10)

    plot_df = pd.DataFrame({
        "Aerolínea": delay_by_airline.index,
        "Retraso Promedio": delay_by_airline.values
    })

    return px.bar(
        plot_df,
        x="Aerolínea",
        y="Retraso Promedio",
        title="Top 10 Aerolíneas con Mayor Retraso Promedio",
        color="Retraso Promedio",
        color_continuous_scale="reds"
    )
    
def plot_distance_vs_airtime(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])
    df["distance"] = dd.to_numeric(df["distance"], errors='coerce')  
    df["air_time"] = dd.to_numeric(df["air_time"], errors='coerce')  
    df_subset = df[["distance", "air_time"]].dropna().compute()
    return px.scatter(
        df_subset, x="distance", y="air_time",
        title="Distancia vs. Tiempo de Vuelo",
        labels={"distance": "Distancia (millas)", "air_time": "Tiempo de Vuelo (min)"},
        trendline="lowess"
    )

def plot_cancellation_rate(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])
    df["arr_delay"] = dd.to_numeric(df["arr_delay"], errors='coerce')  # Añadido opcional si se usa después

    cancelled = df[df["cancelled"] == True]["op_carrier"].value_counts().compute()
    total = df["op_carrier"].value_counts().compute()

    cancellation_rate = (cancelled / total * 100).nlargest(10)

    # Convertir a DataFrame
    plot_df = pd.DataFrame({
        "Aerolínea": cancellation_rate.index,
        "% Cancelaciones": cancellation_rate.values
    })

    return px.bar(
        plot_df,
        x="Aerolínea",
        y="% Cancelaciones",
        title="Porcentaje de Cancelaciones por Aerolínea (Top 10)",
        color="% Cancelaciones",
        color_continuous_scale="blues"
    )
    
def plot_most_common_routes(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])
    df_subset = df[["origin_airport_id", "dest_airport_id"]].compute()
    df_subset["route"] = df_subset["origin_airport_id"].astype(str) + " → " + df_subset["dest_airport_id"].astype(str)
    route_counts = df_subset["route"].value_counts().nlargest(10)

    plot_df = pd.DataFrame({
        "route": route_counts.index,
        "count": route_counts.values
    })

    return px.bar(
        plot_df,
        x="route",
        y="count",
        title="Top 10 Rutas más Comunes",
        labels={"route": "Ruta", "count": "Número de Vuelos"},
        color="count",
        color_continuous_scale="greens",
    )
    
def plot_delay_by_weekday(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])
    df["arr_delay"] = dd.to_numeric(df["arr_delay"], errors='coerce')

    df_subset = df[["fl_date", "arr_delay"]].dropna().compute()
    df_subset["weekday"] = pd.to_datetime(df_subset["fl_date"]).dt.day_name()

    weekday_delay = df_subset.groupby("weekday")["arr_delay"].mean().reindex([
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    ]).dropna()

    plot_df = pd.DataFrame({
        "Día": weekday_delay.index,
        "Retraso Promedio (min)": weekday_delay.values
    })

    return px.line(
        plot_df,
        x="Día",
        y="Retraso Promedio (min)",
        title="Retraso Promedio por Día de la Semana"
    )
    
def plot_delay_by_state(df, airports_df):
    """Gráfico de los 10 estados con mayor retraso promedio"""
    # Asegurar tipos correctos para columnas de merge
    df["origin_airport_id"] = df["origin_airport_id"].astype(str)
    
    # Resetear el índice si airport_id es el índice
    if 'airport_id' not in airports_df.columns and airports_df.index.name == 'airport_id':
        airports_df = airports_df.reset_index()
    
    airports_df["airport_id"] = airports_df["airport_id"].astype(str)

    # Asegurar que arr_delay sea numérico
    df["arr_delay"] = dd.to_numeric(df["arr_delay"], errors='coerce')

    # Realizar merge y computar
    merged_df = df.merge(
        airports_df, 
        left_on="origin_airport_id", 
        right_on="airport_id"
    ).compute()

    # Agrupar por estado y obtener top 10 por retraso promedio
    delay_by_state = merged_df.groupby("state_name")["arr_delay"].mean().nlargest(10)
    
    # Convertir delay_by_state en DataFrame
    delay_df = delay_by_state.reset_index()
    delay_df.columns = ['state_name', 'mean_delay']

    # Graficar usando Plotly Express
    fig = px.bar(
        data_frame=delay_df,
        x='state_name',
        y='mean_delay',
        title="Top 10 Estados con Mayor Retraso Promedio",
        labels={'state_name': 'Estado', 'mean_delay': 'Retraso Promedio (min)'},
        color='mean_delay',
        color_continuous_scale='reds'
    )
    return fig



def plot_most_diverted_airports(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])
    diverted = df[df["diverted"] == True]["dest_airport_id"].value_counts().compute().nlargest(10)

    plot_df = pd.DataFrame({
        "Aeropuerto": diverted.index.astype(str),
        "Desviamientos": diverted.values
    })

    return px.bar(
        plot_df,
        x="Aeropuerto",
        y="Desviamientos",
        title="Top 10 Aeropuertos con Más Vuelos Desviados",
        labels={"Aeropuerto": "Aeropuerto", "Desviamientos": "Número de Desviamientos"},
        color="Desviamientos",
        color_continuous_scale="blues"
    )
    
def plot_monthly_delay_trend(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])
    df["arr_delay"] = dd.to_numeric(df["arr_delay"], errors='coerce')

    df_subset = df[["fl_date", "arr_delay"]].dropna().compute()
    df_subset["month"] = pd.to_datetime(df_subset["fl_date"]).dt.month_name()

    monthly_delay = df_subset.groupby("month")["arr_delay"].mean().reindex([
        "January", "February", "March", "April", "May", "June", 
        "July", "August", "September", "October", "November", "December"
    ]).dropna()

    plot_df = pd.DataFrame({
        "Mes": monthly_delay.index,
        "Retraso Promedio (min)": monthly_delay.values
    })

    return px.line(
        plot_df,
        x="Mes",
        y="Retraso Promedio (min)",
        title="Retraso Promedio por Mes",
        labels={"Mes": "Mes", "Retraso Promedio (min)": "Retraso Promedio (min)"}
    )
