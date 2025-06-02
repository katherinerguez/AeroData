from sqlalchemy import create_engine, text  
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

def get_engine():
    return create_engine(db_url)

engine = get_engine()  

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db_url():
    return db_url

def execute_sql(query: str):
    """Ejecuta una consulta SQL y devuelve los resultados"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))  
            return result.fetchall()
    except Exception as e:
       
        print(f"Error ejecutando SQL: {e}")
        return []
    
def insert_usuario(username: str, hashed_pw: str, role: str):
    with engine.connect() as conn:
        try:
            conn.execute(
                text("INSERT INTO users (username, password, role) VALUES (:username, :password, :role)"),
                {"username": username, "password": hashed_pw, "role": role}
            )
            conn.commit()
        except Exception as e:
            raise ValueError(f"Error al registrar usuario: {str(e)}")

def get_usuario(username: str):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT username, password, role FROM users WHERE username = :username"),
            {"username": username}
        ).fetchone()
        return result
    