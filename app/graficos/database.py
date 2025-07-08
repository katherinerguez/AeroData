from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from models import User, QueryHistory  

db_url = 'https://database-realtime.onrender.com/'
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def insert_usuario(username: str, hashed_pw: str, role: str, db: Session):
    """
    Crea un nuevo usuario 
    """
    nuevo = User(
        username=username,
        password=hashed_pw,
        role=role
    )
    db.add(nuevo)
    try:
        db.commit()
        db.refresh(nuevo)
        return nuevo
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error al registrar usuario: {e}")


def get_usuario(username: str, db: Session):
    """
    Recupera un objeto User filtrado por username.
    Devuelve None si no existe.
    """
    return db.query(User).filter(User.username == username).first()


def save_query_to_history(username: str, query_text: str, db: Session):
    """Guarda una consulta en el historial con valores explícitos"""
    if not username:
        raise ValueError("El nombre de usuario es requerido")

    existing: QueryHistory = (
        db.query(QueryHistory)
          .filter(
            QueryHistory.username == username,
            QueryHistory.query == query_text
          )
          .first()
    )

    if existing:
        existing.execution_count += 1
        existing.timestamp = datetime.utcnow()
    else:
        existing = QueryHistory(
            username=username,
            query=query_text,
            timestamp=datetime.utcnow(),
            execution_count=1,
            type="Graficos"
        )
        db.add(existing)

    try:
        db.commit()
        db.refresh(existing)
        return existing
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error guardando el historial: {e}")


def get_user_query_history(username: str, limit: int = 10, db: Session = None):
    """Obtiene el historial de consultas de un usuario con valores por defecto"""
    return (
        db.query(QueryHistory)
          .filter(QueryHistory.username == username)
          .order_by(QueryHistory.timestamp.desc())
          .limit(limit)
          .all()
    )
