from fastapi import FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from typing import List

# Crea la aplicación FastAPI
app = FastAPI()

# Configura la conexión a PostgreSQL usando SQLAlchemy
db_url = "postgresql+psycopg2://usuario:contraseña@localhost:5432/nombre_base_de_datos"
engine = create_engine(db_url, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Modelo de Pydantic para estructurar la respuesta de la API
class Flight(BaseModel):
    flight_id: int
    origin_airport_id: str
    dest_airport_id: str
    arr_delay: float

    class Config:
        orm_mode = True

# Función para obtener los datos de la base de datos
def get_flights(db, limit: int = 10):
    query = text("SELECT flight_id, origin_airport_id, dest_airport_id, arr_delay FROM flights LIMIT :limit")
    result = db.execute(query, {"limit": limit}).fetchall()
    return result

# Endpoint para obtener los vuelos
@app.get("/flights", response_model=List[Flight])
async def get_flights_endpoint(limit: int = 10):
    # Crea una sesión para interactuar con la base de datos
    db = SessionLocal()
    try:
        flights = get_flights(db, limit)
        # Convertir los resultados a un formato adecuado para la respuesta
        return [Flight(**dict(row)) for row in flights]
    finally:
        db.close()

# Endpoint para la ruta raíz '/'
@app.get("/")
async def read_root():
    return {"message": "Bienvenido a la API de vuelos"}

# Endpoint para manejar favicon.ico
@app.get("/favicon.ico")
async def favicon():
    return {"message": "Favicon no disponible"}

# Ejecutar la API con Uvicorn
# uvicorn main:app --reload
