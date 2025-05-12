from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

# users.py
usuarios = {
    "admin": {"username": "admin", "password": "admin123", "role": "admin"},
    "lector": {"username": "lector", "password": "lector123", "role": "lector"}
}

security = HTTPBasic()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    password = credentials.password

    user = usuarios.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    return {"username": username, "role": user["role"]}
