from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.exc import SQLAlchemyError

from dotenv import load_dotenv
import os
import requests
from datetime import datetime

load_dotenv()

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)

class QueryHistory(Base):
    __tablename__ = 'query_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False)
    query = Column(String(500), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    execution_count = Column(Integer, nullable=False, default=1)
    type = Column(String(20), nullable=False, default='Consultas')

def get_db_url():
    resp = requests.get("https://database-realtime.onrender.com/")
    resp.raise_for_status()
    return resp.text.strip('"').strip("'")

engine = create_engine(get_db_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def get_session():
    """Retorna una nueva sesión de base de datos"""
    return SessionLocal()

def execute_sql(query: str):
    """Ejecuta consultas SQL """
    session = get_session()
    try:
        result = session.execute(text(query))
        return result.fetchall()
    except SQLAlchemyError as e:
        print(f"Error ejecutando SQL: {e}")
        return []
    finally:
        session.close()

def insert_usuario(username: str, hashed_pw: str, role: str):
    """Inserta un nuevo usuario """
    session = get_session()
    try:
        new_user = User(
            username=username,
            password=hashed_pw,
            role=role
        )
        session.add(new_user)
        session.commit()
        return new_user
    except SQLAlchemyError as e:
        session.rollback()
        raise ValueError(f"Error al registrar usuario: {str(e)}")
    finally:
        session.close()

def get_usuario(username: str):
    """Obtiene un usuario por username"""
    session = get_session()
    try:
        return session.query(User).filter(User.username == username).first()
    finally:
        session.close()

def save_query_to_history(username: str, query: str):
    """Guarda una consulta en el historial"""
    session = get_session()
    try:
        # Buscar consulta existente
        existing = session.query(QueryHistory).filter(
            QueryHistory.username == username,
            QueryHistory.query == query
        ).first()
        
        if existing:

            existing.execution_count += 1
            existing.timestamp = datetime.utcnow()
        else:
            
            new_entry = QueryHistory(
                username=username,
                query=query,
                type="Consultas"
            )
            session.add(new_entry)
        
        session.commit()
        return existing if existing else new_entry
    except SQLAlchemyError as e:
        session.rollback()
        raise RuntimeError(f"Error al guardar historial: {str(e)}")
    finally:
        session.close()

def get_user_query_history(username: str, limit: int = 10):
    """Obtiene historial de consultas usando ORM"""
    session = get_session()
    try:
        return (
            session.query(QueryHistory)
            .filter(QueryHistory.username == username)
            .order_by(QueryHistory.timestamp.desc())
            .limit(limit)
            .all()
        )
    finally:
        session.close()