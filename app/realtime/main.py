from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles  

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv('supabase_url_realtime')
SUPABASE_KEY = os.getenv('superbase_key_realtime')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")  

router = APIRouter(prefix="/realtime-flights")
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("diseno.html", {
        "request": request,
        "graph_html": graph_html,
        "titulo": "Vuelos en tiempo real"
    })

app.include_router(router)