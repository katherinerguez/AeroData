import dask.dataframe as dd
import plotly.express as px
import pandas as pd  


def load_data(db_url):
    """Carga datos de las tablas flights y airports desde la base de datos"""
    # Cargar tabla de vuelos
    flights_df = dd.read_sql_table(
        table_name="flights",
        con=db_url,
        index_col="flight_id"
    )
    
    # Cargar tabla de aeropuertos
    airports_df = dd.read_sql_table(
        table_name="airports",
        con=db_url,
        index_col="airport_id"  # Usamos airport_id como índice principal
    )
    
    
    return flights_df, airports_df



def plot_delay_by_airport(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])
    
    delay_by_airport = df.groupby("origin_airport_id")["arr_delay"].mean().compute().nlargest(10)
    temp_df = pd.DataFrame({
        "airport_id": delay_by_airport.index.astype(str),
        "avg_delay": delay_by_airport.values
    })

    return px.bar(
        temp_df,
        x="airport_id",
        y="avg_delay",
        labels={"airport_id": "ID del Aeropuerto", "avg_delay": "Retraso Promedio (min)"},
        title="Top 10 Aeropuertos con Mayor Retraso Promedio",
        color="avg_delay",
        color_continuous_scale="Reds"
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

    df_subset = df[["origin_airport_id", "dest_airport_id", "air_time"]].dropna().compute()
    df_subset["route"] = df_subset["origin_airport_id"].astype(str) + " → " + df_subset["dest_airport_id"].astype(str)
    airtime_by_route = df_subset.groupby("route")["air_time"].mean().nlargest(10)
    return px.bar(
        x=airtime_by_route.index,
        y=airtime_by_route.values,
        labels={"x": "Ruta", "y": "Tiempo Promedio (min)"},
        title="Top 10 Rutas con Mayor Tiempo Promedio de Vuelo",
        color=airtime_by_route.values,
        color_continuous_scale="Purples"
    )

def plot_flights_by_date(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])

    date_counts = df["fl_date"].value_counts().compute().sort_index()
    return px.line(
        x=date_counts.index.astype(str),
        y=date_counts.values,
        labels={"x": "Fecha", "y": "Cantidad de Vuelos"},
        title="Vuelos por Día"
    )

def plot_delay_by_hour(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])

    df_subset = df[["crs_dep_time", "arr_delay"]].dropna().compute()
    df_subset["hour"] = df_subset["crs_dep_time"].astype(str).str.slice(0,2).astype(int)
    hourly_delay = df_subset.groupby("hour")["arr_delay"].mean()
    return px.bar(
        x=hourly_delay.index,
        y=hourly_delay.values,
        labels={"x": "Hora del Día", "y": "Retraso Promedio (min)"},
        title="Retraso Promedio por Hora del Día",
        color=hourly_delay.values,
        color_continuous_scale="Oranges"
    )

def plot_delay_by_airline(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])

    delay_by_airline = df.groupby("op_carrier")["arr_delay"].mean().compute().nlargest(10)
    return px.bar(
        x=delay_by_airline.index,
        y=delay_by_airline.values,
        title="Top 10 Aerolíneas con Mayor Retraso Promedio",
        labels={"x": "Aerolínea", "y": "Retraso Promedio (min)"},
        color=delay_by_airline.values,
        color_continuous_scale="reds",
    )
    
def plot_distance_vs_airtime(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])

    df_subset = df[["distance", "air_time"]].dropna().compute()
    return px.scatter(
        df_subset, x="distance", y="air_time",
        title="Distancia vs. Tiempo de Vuelo",
        labels={"distance": "Distancia (millas)", "air_time": "Tiempo de Vuelo (min)"},
        trendline="lowess",
    )  

def plot_cancellation_rate(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])

    cancelled = df[df["cancelled"] == True]["op_carrier"].value_counts().compute()
    total = df["op_carrier"].value_counts().compute()
    cancellation_rate = (cancelled / total * 100).nlargest(10)
    return px.bar(
        x=cancellation_rate.index,
        y=cancellation_rate.values,
        title="Porcentaje de Cancelaciones por Aerolínea (Top 10)",
        labels={"x": "Aerolínea", "y": "% Cancelaciones"},
        color=cancellation_rate.values,
        color_continuous_scale="blues",
    )
    
def plot_most_common_routes(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])
    df_subset = df[["origin_airport_id", "dest_airport_id"]].compute()
    df_subset["route"] = df_subset["origin_airport_id"].astype(str) + " → " + df_subset["dest_airport_id"].astype(str)
    route_counts = df_subset["route"].value_counts().nlargest(10)
    return px.bar(
        x=route_counts.index,
        y=route_counts.values,
        title="Top 10 Rutas más Comunes",
        labels={"x": "Ruta", "y": "Número de Vuelos"},
        color=route_counts.values,
        color_continuous_scale="greens",
    )
def plot_delay_by_weekday(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])
    df_subset = df[["fl_date", "arr_delay"]].dropna().compute()
    df_subset["weekday"] = pd.to_datetime(df_subset["fl_date"]).dt.day_name()
    weekday_delay = df_subset.groupby("weekday")["arr_delay"].mean().reindex(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    )
    return px.line(
        x=weekday_delay.index,
        y=weekday_delay.values,
        title="Retraso Promedio por Día de la Semana",
        labels={"x": "Día", "y": "Retraso Promedio (min)"},
    )
    
def plot_delay_by_state(df, airports_df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])
    merged_df = df.merge(airports_df, left_on="origin_airport_id", right_on="airport_id").compute()
    delay_by_state = merged_df.groupby("state_name")["arr_delay"].mean().nlargest(10)
    return px.bar(
        x=delay_by_state.index,
        y=delay_by_state.values,
        title="Top 10 Estados con Mayor Retraso Promedio",
        labels={"x": "Estado", "y": "Retraso Promedio (min)"},
    )

def plot_most_diverted_airports(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])
    diverted = df[df["diverted"] == True]["dest_airport_id"].value_counts().compute().nlargest(10)
    return px.bar(
        x=diverted.index.astype(str),
        y=diverted.values,
        title="Top 10 Aeropuertos con Más Vuelos Desviados",
        labels={"x": "Aeropuerto", "y": "Número de Desviamientos"},
    )

def plot_monthly_delay_trend(df):
    df["fl_date"] = dd.to_datetime(df["fl_date"])
    df_subset = df[["fl_date", "arr_delay"]].dropna().compute()
    df_subset["month"] = pd.to_datetime(df_subset["fl_date"]).dt.month_name()
    monthly_delay = df_subset.groupby("month")["arr_delay"].mean().reindex(
        ["January", "February", "March", "April", "May", "June", 
         "July", "August", "September", "October", "November", "December"]
    )
    return px.line(
        x=monthly_delay.index,
        y=monthly_delay.values,
        title="Retraso Promedio por Mes",
        labels={"x": "Mes", "y": "Retraso Promedio (min)"},
    )
