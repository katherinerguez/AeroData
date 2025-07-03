from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import bcrypt
from database import get_usuario, insert_usuario

security = HTTPBasic()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    password = credentials.password

    user_data = get_usuario(username)

    if not user_data:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    stored_hash = user_data[1]

    # Validar contraseña
    if not bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    return {
        "username": user_data[0],
        "role": user_data[2]
    }

def registrar_usuario(username: str, password: str, role: str = "usuario"):
    if get_usuario(username):
        raise ValueError("El usuario ya existe")

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    insert_usuario(username, hashed, role)