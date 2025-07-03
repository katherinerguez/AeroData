from sqlalchemy import create_engine,text
from sqlalchemy.orm import sessionmaker, declarative_base

from dotenv import load_dotenv
import os

from datetime import datetime

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
            result = conn.execute(text(query))  # Ahora 'text' está importado
            return result.fetchall()
    except Exception as e:
        # Manejo básico de errores
            print(f"Error ejecutando SQL: {e}")
            result = conn.execute(text(query))  
            return result.fetchall()

def save_query_to_history(username: str, query: str):
    """Guarda una consulta en el historial con valores explícitos"""

    with engine.connect() as conn:
        # Verificar si la consulta ya existe para este usuario
        existing = conn.execute(
            text("""
            SELECT id, execution_count FROM query_history 
            WHERE username = :username AND query = :query
            """),
            {"username": username, "query": query}
        ).fetchone()
        
        if existing:
            # Actualizar el conteo y timestamp si ya existe
            conn.execute(
                text("""
                UPDATE query_history 
                SET execution_count = :count, 
                    timestamp = :timestamp
                WHERE id = :id
                """),
                {
                    "count": existing[1] + 1,
                    "timestamp": datetime.now(),  # Actualiza el timestamp también
                    "id": existing[0]
                }
            )
        else:
            # Insertar nueva consulta con valores explícitos
            conn.execute(
                text("""
                INSERT INTO query_history 
                    (username, query, timestamp, execution_count, type) 
                VALUES 
                    (:username, :query, :timestamp, :execution_count, :type)
                """),
                {
                    "username": username,
                    "query": query,
                    "timestamp": datetime.now(),  # Momento exacto
                    "execution_count": 1,        # Siempre 1 para nuevas consultas
                    "type": "Api"          # Valor fijo explícito
                }
            )
        conn.commit()