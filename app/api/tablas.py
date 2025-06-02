from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Time, ForeignKey
from app.api.database import Base
from datetime import datetime
from passlib.context import CryptContext

# Configuración para el hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)  # Cambiado a password_hash para consistencia
    
    def set_password(self, password: str):
        """Genera y almacena el hash de la contraseña"""
        self.password = pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Verifica si la contraseña coincide con el hash almacenado"""
        return pwd_context.verify(password, self.password)

class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    key = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)
       
# ---------------- AIRPORT ----------------
class Airport(Base):
    __tablename__ = "airports"

    airport_id = Column(Integer, primary_key=True, index=True)
    airport_seq_id = Column(Integer)
    city_market_id = Column(String)
    code = Column(String)
    city_name = Column(String)
    state_abr = Column(String)
    state_fips = Column(String)
    state_name = Column(String)
    wac = Column(Integer)

# ---------------- AIRLINE ----------------
class Airline(Base):
    __tablename__ = "airlines"

    airline_id = Column(Integer, primary_key=True, index=True)
    unique_carrier = Column(String)

# ---------------- FLIGHT ----------------
class Flight(Base):
    __tablename__ = "flights"

    flight_id = Column(Integer, primary_key=True, index=True)
    fl_date = Column(DateTime)
    op_unique_carrier = Column(String)
    op_carrier_airline_id = Column(Integer)
    op_carrier = Column(String)
    tail_num = Column(String, nullable=True)
    op_carrier_fl_num = Column(String)
    origin_airport_id = Column(Integer)
    dest_airport_id = Column(Integer)
    crs_dep_time = Column(Time)
    dep_time = Column(Time, nullable=True)
    dep_delay = Column(Float, nullable=True)
    wheels_off = Column(Time, nullable=True)
    wheels_on = Column(Time, nullable=True)
    crs_arr_time = Column(Time)
    arr_time = Column(Time, nullable=True)
    arr_delay = Column(Float, nullable=True)
    cancelled = Column(Boolean)
    diverted = Column(Boolean)
    air_time = Column(Float, nullable=True)
    distance = Column(Float, nullable=True)
    flights = Column(Float, nullable=True)
