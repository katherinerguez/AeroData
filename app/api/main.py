# main.py
from fastapi import FastAPI, Depends,HTTPException , Header
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import SessionLocal, engine
import app.tablas as tablas
import app.schemas as schemas
import uuid


tablas.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Flight API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Registro de usuario
@app.post("/register/", response_model=schemas.UserOut)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(tablas.User).filter(tablas.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    api_key = str(uuid.uuid4())
    new_user = tablas.User(username=user.username, api_key=api_key)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def verify_api_key(x_api_key: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API Key requerida")

    user = db.query(tablas.User).filter(tablas.User.api_key == x_api_key).first()
    if not user:
        raise HTTPException(status_code=401, detail="API Key inválida")


@app.get("/airports/", response_model=List[schemas.AirportSchema], dependencies=[Depends(verify_api_key)])
def get_airports(db: Session = Depends(get_db)):
    return db.query(tablas.Airport).all()

@app.get("/airlines/", response_model=List[schemas.AirlineSchema], dependencies=[Depends(verify_api_key)])
def get_airlines(db: Session = Depends(get_db)):
    return db.query(tablas.Airline).all()

@app.get("/flights/", response_model=List[schemas.FlightSchema], dependencies=[Depends(verify_api_key)])
def get_flights(db: Session = Depends(get_db)):
    return db.query(tablas.Flight).all()
