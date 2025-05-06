# schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, time

# ---------------- AIRPORT ----------------
class AirportSchema(BaseModel):
    airport_id: int
    airport_seq_id: int
    city_market_id: int
    code: str
    city_name: str
    state_abr: str
    state_fips: str
    state_name: str
    wac: int

    class Config:
        orm_mode = True

# ---------------- AIRLINE ----------------
class AirlineSchema(BaseModel):
    airline_id: int
    unique_carrier: str

    class Config:
        orm_mode = True

# ---------------- FLIGHT ----------------
class FlightSchema(BaseModel):
    flight_id: int
    fl_date: datetime
    op_unique_carrier: str
    op_carrier_airline_id: int
    op_carrier: str
    tail_num: Optional[str]
    op_carrier_fl_num: str
    origin_airport_id: int
    dest_airport_id: int
    crs_dep_time: time
    dep_time: Optional[time]
    dep_delay: Optional[float]
    wheels_off: Optional[time]
    wheels_on: Optional[time]
    crs_arr_time: time
    arr_time: Optional[time]
    arr_delay: Optional[float]
    cancelled: bool
    diverted: bool
    air_time: Optional[float]
    distance: Optional[float]
    flights: Optional[float]

    class Config:
        orm_mode = True
