from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import json
import plotly
from database import get_db_url
import dask.dataframe as dd
import plots


app = FastAPI()
templates = Jinja2Templates(directory="templates")

# @app.get("/", response_class=HTMLResponse)
# async def dashboard(request: Request, start_date: str = Query(None), end_date: str = Query(None)):    
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, start_date: str = Query(None), end_date: str = Query(None), selected_route: str = Query(None), selected_plane: str = Query(None)):

    db_url = get_db_url()
    df, airports_df = plots.load_data(db_url)  # Desempaquetar ambos DataFrames
    
    df["route"] = df["origin_airport_id"].astype(str) + " → " + df["dest_airport_id"].astype(str)
    unique_routes = df["route"].dropna().unique().compute().tolist()

    unique_planes = df["op_carrier_fl_num"].dropna().unique().compute().tolist()

    df["fl_date"] = dd.to_datetime(df["fl_date"])

    if start_date and end_date:
        df = df[(df["fl_date"] >= start_date) & (df["fl_date"] <= end_date)]
    if selected_route:
        origin, dest = selected_route.split(" → ")
        df = df[(df["origin_airport_id"].astype(str) == origin) & (df["dest_airport_id"].astype(str) == dest)]
    if selected_plane:
        df = df[df["op_carrier_fl_num"] == selected_plane]

    #print(df.head())
    figs = [
        plots.plot_delay_by_airport(df),
        plots.plot_flight_counts(df),
        plots.plot_arrival_delay_distribution(df),
        plots.plot_cancelled_flights(df),
        plots.plot_airtime_by_route(df),
        plots.plot_flights_by_date(df),
        plots.plot_delay_by_hour(df),
        plots.plot_delay_by_airline(df),
        plots.plot_distance_vs_airtime(df),
        plots.plot_cancellation_rate(df),
        plots.plot_most_common_routes(df),
        plots.plot_delay_by_weekday(df),
        plots.plot_delay_by_state(df, airports_df),
        plots.plot_most_diverted_airports(df),
        plots.plot_monthly_delay_trend(df),
    ]
    graphs_json = [json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder) for fig in figs]

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "start_date": start_date,
        "end_date": end_date,
        "routes": unique_routes,
        "selected_route": selected_route,
        "planes": unique_planes,
        "selected_plane": selected_plane,

        **{f"graph{i+1}": graph for i, graph in enumerate(graphs_json)}
    })
