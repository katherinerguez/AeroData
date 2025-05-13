# ("admin", "admin123", "admin")
# ("lector", "lector123", "lector")

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import redis
import bcrypt
import os

security = HTTPBasic()
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    password = credentials.password

    # Verificar si el usuario existe
    if not r.exists(f"user:{username}"):
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    user_data = r.hgetall(f"user:{username}")
    stored_hash = user_data.get("password")

    if not stored_hash:
        raise HTTPException(status_code=500, detail="Contraseña no configurada")

    # Validar contraseña
    if not bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    return {
        "username": username,
        "role": user_data.get("role", "usuario")
    }

def registrar_usuario(username: str, password: str, role: str = "usuario"):
    if r.exists(f"user:{username}"):
        raise ValueError("El usuario ya existe")

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    r.hset(f"user:{username}", mapping={"password": hashed, "role": "lector"})