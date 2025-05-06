from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

db_url = "postgresql://postgres:Jennifer2004*@localhost:5432/fligth-database"

def get_engine():
    return create_engine(db_url)

def get_db_url():
    return db_url
engine = get_engine()  # ✅ Usamos la función para crear el motor
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db_url():
    return db_url

def execute_sql(query: str):
    """Ejecuta una consulta SQL y devuelve los resultados"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))  # ✅ Ahora 'text' está importado
            return result.fetchall()
    except Exception as e:
        # ✅ Manejo básico de errores
        print(f"Error ejecutando SQL: {e}")
        return []