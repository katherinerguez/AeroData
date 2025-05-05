from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import json
import plotly
from database import get_db_url
#from database import engine
import plots


app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, start_date: str = Query(None), end_date: str = Query(None)):    
    db_url = get_db_url()
    df, airports_df = plots.load_data(db_url)  # Desempaquetar ambos DataFrames

    if start_date and end_date:
        df = df[(df["fl_date"] >= start_date) & (df["fl_date"] <= end_date)]
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
        **{f"graph{i+1}": graph for i, graph in enumerate(graphs_json)}
    })
