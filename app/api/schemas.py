from pydantic import BaseModel, SecretStr, field_validator
from typing import Optional
from datetime import datetime, time

class UserCreate(BaseModel):
    username: str
    password: SecretStr
    
    @field_validator('password')
    def validate_password(cls, v):
        if len(v.get_secret_value()) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v

class UserOut(BaseModel):
    id: int
    username: str
    api_key: str  # Añadido para devolver la API key

    class Config:
        from_attributes = True
        
class ApiKeySchema(BaseModel):
    id: int
    user_id: int
    key: str
    created_at: datetime
    active: bool

    class Config:
        from_attributes = True
        
# ---------------- AIRPORT ----------------
class AirportSchema(BaseModel):
    airport_id: int
    airport_seq_id: int
    city_market_id: str
    code: str
    city_name: str
    state_abr: str
    state_fips: str
    state_name: str
    wac: int

    class Config:
        from_attributes = True

# ---------------- AIRLINE ----------------
class AirlineSchema(BaseModel):
    airline_id: int
    unique_carrier: str

    class Config:
        from_attributes = True

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
        from_attributes = True
