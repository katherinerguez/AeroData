# main.py
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List
from database import SessionLocal, engine
import tablas, schemas

# Crear las tablas en la BD si no existen
tablas.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Flight API")

# Dependencia para obtener la sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/airports/", response_model=List[schemas.AirportSchema])
def get_airports(db: Session = Depends(get_db)):
    return db.query(tablas.Airport).all()

@app.get("/airlines/", response_model=List[schemas.AirlineSchema])
def get_airlines(db: Session = Depends(get_db)):
    return db.query(tablas.Airline).all()

@app.get("/flights/", response_model=List[schemas.FlightSchema])
def get_flights(db: Session = Depends(get_db)):
    return db.query(tablas.Flight).all()
