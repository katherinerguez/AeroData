# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os
load_dotenv()
local_Jenni= os.getenv('local_Jenni')
# Cambia según tu contraseña y configuración
db_url = f"postgresql://{local_Jenni}"

engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_engine():
    return create_engine(db_url)

def get_db_url():
    return db_url
engine = get_engine()  # Usamos la función para crear el motor

def get_db_url():
    return db_url

def execute_sql(query: str):
    """Ejecuta una consulta SQL y devuelve los resultados"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))  # Ahora 'text' está importado
            return result.fetchall()
    except Exception as e:
        # Manejo básico de errores
        print(f"Error ejecutando SQL: {e}")
        return []
