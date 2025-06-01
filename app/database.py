# database.py
from sqlalchemy import create_engine,text
from sqlalchemy.orm import sessionmaker, declarative_base

from dotenv import load_dotenv
import os
load_dotenv()

# local_Jenni=os.getenv('local_Jenni')
# db_url = f"postgresql://{local_Jenni}"
user=os.getenv('user')
password=os.getenv('password')
host=os.getenv('host')
port=os.getenv('port')
dbname=os.getenv('dbname')
db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_engine():
    return create_engine(db_url)

def get_db_url():
    return db_url
engine = get_engine()  

def execute_sql(query: str):
    """Ejecuta una consulta SQL y devuelve los resultados"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))  
            return result.fetchall()
    except Exception as e:
        print(f"Error ejecutando SQL: {e}")
        return []
