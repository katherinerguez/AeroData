from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

from datetime import datetime
import requests

db_url=requests.get('https://database-realtime.onrender.com/')

engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class QueryHistory(Base):
    __tablename__ = 'query_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False)
    query = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    execution_count = Column(Integer, nullable=False)
    type = Column(String, nullable=False)

def get_db():
    """Generador de sesiones de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def execute_sql(query: str):
    """Ejecuta una consulta SQL y devuelve los resultados"""
    try:
        with SessionLocal() as session:
            result = session.execute(text(query))
            return result.fetchall()
    except Exception as e:
        print(f"Error ejecutando SQL: {e}")
        raise

def save_query_to_history(username: str, query: str):
    """Guarda una consulta en el historial usando ORM"""
    with SessionLocal() as session:
        # Buscar consulta existente
        existing = session.query(QueryHistory).filter(
            QueryHistory.username == username,
            QueryHistory.query == query
        ).first()
        
        if existing:
            # Actualizar registro existente
            existing.execution_count += 1
            existing.timestamp = datetime.now()
        else:
            # Crear nuevo registro
            new_entry = QueryHistory(
                username=username,
                query=query,
                timestamp=datetime.now(),
                execution_count=1,
                type="Api"
            )
            session.add(new_entry)
        
        session.commit()