from fastapi import FastAPI
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("supabase_url")
SUPABASE_KEY = os.getenv("supabase_key")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Microservicio conectado a Supabase"}

@app.get("/tabla/{nombre_tabla}")
def get_datos(nombre_tabla: str):
    try:
        
        datos = supabase.table(nombre_tabla).select('*').execute()
        
        return datos.data
    except Exception as e:
        return {"error": str(e)}
