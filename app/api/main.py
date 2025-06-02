from fastapi import FastAPI, Depends,HTTPException , Header
from sqlalchemy.orm import Session
from typing import List, Optional
from database import SessionLocal, engine
import tablas as tablas
import schemas as schemas
import uuid


tablas.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Flight API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_api_key(x_api_key: str = Header(...), db: Session = Depends(get_db)):
    user = db.query(tablas.ApiKey).filter(tablas.ApiKey.key == x_api_key).first()
    if not user:
        raise HTTPException(status_code=401, detail="API Key inválida")
    return user
    
@app.post("/register/", response_model=schemas.UserOut)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(tablas.User).filter(tablas.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    try:
        # Crear usuario
        new_user = tablas.User(username=user.username)
        new_user.set_password(user.password.get_secret_value())
        db.add(new_user)
        db.flush()  # Para obtener el ID
        
        # Crear API Key
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
    
from fastapi.responses import HTMLResponse

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

@app.get("/airports/", response_model=List[schemas.AirportSchema], dependencies=[Depends(verify_api_key)])
def get_airports(db: Session = Depends(get_db)):
    return db.query(tablas.Airport).all()

@app.get("/airlines/", response_model=List[schemas.AirlineSchema], dependencies=[Depends(verify_api_key)])
def get_airlines(db: Session = Depends(get_db)):
    flights = db.query(tablas.Airline).limit(5).all()
    print("Mostrando primeros 5 vuelos:")
    for flight in flights:
        print(flight.flight_id, flight.fl_date, flight.op_carrier)
    return flights
    # db.query(tablas.Airline).all()
    # return db.query(tablas.Airline).all()

from fastapi import Query

@app.get("/airlines/", response_model=List[schemas.AirlineSchema], dependencies=[Depends(verify_api_key)])
def get_airlines(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(50, ge=1, le=1000, description="Tamaño de la página"),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * page_size
    airlines = db.query(tablas.Airline).offset(offset).limit(page_size).all()
    
    print(f"Mostrando aerolíneas {offset + 1} a {offset + len(airlines)}:")
    for airline in airlines:
        print(airline.airline_id, airline.name)
    
    return airlines

@app.get("/flights/", response_model=List[schemas.FlightSchema], dependencies=[Depends(verify_api_key)])
def get_flights(
    airline_id: Optional[int] = None,
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(50, ge=1, le=1000, description="Tamaño de la página"),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * page_size
    query = db.query(tablas.Flight)

    if airline_id is not None:
        query = query.filter(tablas.Flight.op_carrier_airline_id == airline_id)

    flights = query.offset(offset).limit(page_size).all()
    
    print(f"Mostrando vuelos {offset + 1} a {offset + len(flights)}:")
    for flight in flights:
        print(flight.flight_id, flight.fl_date, flight.op_carrier)
    
    return flights
