# models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Time
from database import Base

from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    api_key = Column(String, unique=True, index=True)
    
# ---------------- AIRPORT ----------------
class Airport(Base):
    __tablename__ = "airports"

    airport_id = Column(Integer, primary_key=True, index=True)
    airport_seq_id = Column(Integer)
    city_market_id = Column(Integer)
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
