from fastapi import FastAPI, Depends,HTTPException , Header,Query
from fastapi.responses import JSONResponse, StreamingResponse,HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from database import SessionLocal, engine, save_query_to_history
import tablas as tablas
import schemas as schemas

import uuid
import io
import csv

tablas.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Flight API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_api_key(x_api_key: Optional[str] = Header(None), db: Session = Depends(get_db)):

    api_key_entry = db.query(tablas.ApiKey).filter(tablas.ApiKey.key == x_api_key).first()
    if not api_key_entry:
        raise HTTPException(status_code=401, detail="API Key inválida")
    
    user = db.query(tablas.User).filter(tablas.User.id == api_key_entry.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {"user_id": user.id, "username": user.username}



@app.post("/register/", response_model=schemas.UserOut)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(tablas.User).filter(tablas.User.username == user.username).first()

    try:
        if existing_user:
            # Validar contraseña
            if not existing_user.verify_password(user.password.get_secret_value()):
                raise HTTPException(status_code=401, detail="Contraseña incorrecta")
            
            # Revisar si ya tiene API Key
            existing_api_key = db.query(tablas.ApiKey).filter(tablas.ApiKey.user_id == existing_user.id).first()
            if existing_api_key:
                return {
                    "id": existing_user.id,
                    "username": existing_user.username,
                    "api_key": existing_api_key.key
                }
            else:
                # Generar nueva API Key para usuario existente sin clave
                api_key = str(uuid.uuid4())
                new_api_key = tablas.ApiKey(user_id=existing_user.id, key=api_key)
                db.add(new_api_key)
                db.commit()
                return {
                    "id": existing_user.id,
                    "username": existing_user.username,
                    "api_key": api_key
                }

        # Crear nuevo usuario
        new_user = tablas.User(username=user.username)
        new_user.set_password(user.password.get_secret_value())
        db.add(new_user)
        db.flush()  # Obtener ID para clave API

        api_key = str(uuid.uuid4())
        new_api_key = tablas.ApiKey(user_id=new_user.id, key=api_key)
        db.add(new_api_key)
        db.commit()

        return {
            "id": new_user.id,
            "username": new_user.username,
            "api_key": api_key
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    

@app.get("/register/", response_class=HTMLResponse)
async def show_register_form():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Registro de Usuario</title>
        <style>
            /* [Mantén todos tus estilos actuales] */
            /* Añade esto para el campo de contraseña */
            input[type="password"] {
                padding: 0.5rem;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 1rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Registro de Usuario</h2>
            <form id="registerForm">
                <label for="email">Correo electrónico:</label>
                <input type="email" id="email" name="email" required placeholder="tu@email.com">
                
                <label for="password">Contraseña:</label>
                <input type="password" id="password" name="password" required placeholder="Mínimo 8 caracteres">
                
                <button type="button" onclick="submitForm()">Generar API Key</button>
            </form>
            
            <div id="apiKeyContainer">
                <span id="apiKeyLabel">Tu API Key:</span>
                <div id="apiKey"></div>
            </div>
            <div id="error" style="color:red; margin-top:1rem;"></div>
        </div>

        <script>
            async function submitForm() {
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                const errorElement = document.getElementById('error');
                
                // Validación básica del frontend
                if (password.length < 8) {
                    errorElement.textContent = 'La contraseña debe tener al menos 8 caracteres';
                    return;
                }
                
                try {
                    const response = await fetch('/register/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            username: email,
                            password: password
                        }),
                    });
                    
                    const data = await response.json();
                    
                    if (!response.ok) {
                        throw new Error(data.detail || 'Error al registrar');
                    }
                    
                    document.getElementById('apiKey').textContent = data.api_key;
                    document.getElementById('apiKeyContainer').style.display = 'block';
                    errorElement.textContent = '';
                    
                } catch (error) {
                    errorElement.textContent = error.message;
                    console.error('Error:', error);
                }
            }
        </script>
    </body>
    </html>
    """
    

@app.get("/api-keys", response_model=List[schemas.ApiKeySchema], dependencies=[Depends(verify_api_key)])
def get_api_keys(db: Session = Depends(get_db)):
    return db.query(tablas.ApiKey).all()

@app.get("/airlines/", response_model=List[schemas.AirlineSchema], dependencies=[Depends(verify_api_key)])
def get_airlines(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    format: str = Query("json", enum=["json", "csv"]),
    db: Session = Depends(get_db),
    user=Depends(verify_api_key)
):
    save_query_to_history(username=user["username"], query=f"/airlines/?page={page}&page_size={page_size}&format={format}")
    offset = (page - 1) * page_size
    airlines = db.query(tablas.Airline).offset(offset).limit(page_size).all()

    if format == "json":
        return airlines

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["airline_id", "unique_carrier"])
    for a in airlines:
        writer.writerow([a.airline_id, a.unique_carrier])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=airlines.csv"})


@app.get("/flights/", response_model=List[schemas.FlightSchema], dependencies=[Depends(verify_api_key)])
def get_flights(
    airline_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    format: str = Query("json", enum=["json", "csv"]),
    db: Session = Depends(get_db),
    user=Depends(verify_api_key)
):
    query_str = f"/flights/?airline_id={airline_id}&page={page}&page_size={page_size}&format={format}"
    save_query_to_history(username=user["username"], query=query_str)

    offset = (page - 1) * page_size
    query = db.query(tablas.Flight)
    if airline_id is not None:
        query = query.filter(tablas.Flight.op_carrier_airline_id == airline_id)

    flights = query.offset(offset).limit(page_size).all()

    if format == "json":
        return flights

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "flight_id", "fl_date", "op_unique_carrier", "op_carrier_airline_id",
        "op_carrier", "tail_num", "op_carrier_fl_num", "origin_airport_id",
        "dest_airport_id", "crs_dep_time", "dep_time", "dep_delay",
        "wheels_off", "wheels_on", "crs_arr_time", "arr_time", "arr_delay",
        "cancelled", "diverted", "air_time", "distance", "flights"
    ])
    for f in flights:
        writer.writerow([
            f.flight_id, f.fl_date, f.op_unique_carrier, f.op_carrier_airline_id,
            f.op_carrier, f.tail_num, f.op_carrier_fl_num, f.origin_airport_id,
            f.dest_airport_id, f.crs_dep_time, f.dep_time, f.dep_delay,
            f.wheels_off, f.wheels_on, f.crs_arr_time, f.arr_time, f.arr_delay,
            f.cancelled, f.diverted, f.air_time, f.distance, f.flights
        ])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=flights.csv"})


@app.get("/airports/", response_model=List[schemas.AirportSchema], dependencies=[Depends(verify_api_key)])
def get_airports(
    format: str = Query("json", enum=["json", "csv"]),
    db: Session = Depends(get_db),
    user=Depends(verify_api_key)
): 
    save_query_to_history(username=user["username"], query=f"/airports/?format={format}")
    airports = db.query(tablas.Airport).all()

    if format == "json":
        return airports

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["airport_id", "airport_seq_id", "city_market_id", "code", "city_name", "state_abr", "state_fips", "state_name", "wac"])
    for a in airports:
        writer.writerow([
            a.airport_id,
            a.airport_seq_id,
            a.city_market_id,
            a.code,
            a.city_name,
            a.state_abr,
            a.state_fips,
            a.state_name,
            a.wac
        ])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=airports.csv"})
