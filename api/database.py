# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Cambia según tu contraseña y configuración
DATABASE_URL = "postgresql://postgres:Jennifer2004*@localhost:5432/fligth-database"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
