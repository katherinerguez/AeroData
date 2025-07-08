from fastapi import FastAPI
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("supabase_url_realtime")
SUPABASE_KEY = os.getenv("superbase_key_realtime")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

@app.get("/")
def read_root():
    user=os.getenv('user')
    password=os.getenv('password')
    host=os.getenv('host')
    port=os.getenv('port')
    dbname=os.getenv('dbname')
    db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

    return db_url

@app.get("/realtime")
def read_root():
    user=os.getenv('user_realtime')
    password=os.getenv('password2')
    host=os.getenv('host_realtime')
    port=os.getenv('port')
    dbname=os.getenv('dbname')
    db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    return db_url

@app.get("/tabla/{nombre_tabla}")
def get_datos(nombre_tabla: str):
    try:
        
        datos = supabase.table(nombre_tabla).select('*').execute()
        
        return datos.data
    except Exception as e:
        return {"error": str(e)}
