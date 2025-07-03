from fastapi import FastAPI, HTTPException,Body, Form, Depends, Request
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from auth import get_current_user,registrar_usuario
import pandas as pd
import io
import os

from database import execute_sql, save_query_to_history,get_user_query_history

from datetime import datetime

app = FastAPI()

# Modelo para recibir consultas SQL
class SQLQuery(BaseModel):
    query: str

# --- Ruta para mostrar la interfaz web ---
@app.get("/login", response_class=HTMLResponse)
async def mostrar_login():
    html_path = os.path.join(os.path.dirname(__file__), "login.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo login.html no encontrado")

from fastapi.responses import RedirectResponse

@app.get("/", response_class=HTMLResponse)
async def raiz(request: Request):
    auth_header = request.headers.get("authorization")
    if auth_header:
        return RedirectResponse(url="/dashboar")
    return RedirectResponse(url="/login")


@app.get("/dashboar", response_class=HTMLResponse)
async def mostrar_dashboard():
    # Leer el archivo HTML directamente
    html_path = os.path.join(os.path.dirname(__file__), "consultas.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo consultas.html no encontrado")

@app.get("/register", response_class=HTMLResponse)
async def mostrar_registro():
    html_path = os.path.join(os.path.dirname(__file__), "register.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo register.html no encontrado")

@app.post("/register")
async def register(username: str = Form(...), password: str = Form(...)):
    if not username or not password:
        raise HTTPException(status_code=400, detail="Faltan usuario o contraseña")
    
    try:
        registrar_usuario(username, password, role="usuario")
        return {"message": "Usuario registrado correctamente"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
  
# --- Ruta para descargar como CSV  ---
@app.post("/download/{formato}")
async def download_sql(query: SQLQuery, formato: str):
    if not query.query.strip().lower().startswith("select"):
        raise HTTPException(status_code=400, detail="Solo se permiten consultas SELECT")
    
    try:
        result = execute_sql(query.query)
        df = pd.DataFrame(result)

        # Generar archivo CSV 
        if formato.lower() == "csv":
            stream = io.StringIO()
            df.to_csv(stream, index=False)
            media_type = "text/csv"
            filename = "consulta.csv"
        else:
            raise HTTPException(status_code=400, detail="Formato no soportado. Usa 'csv' .")

        # Devolver archivo como descarga
        stream.seek(0)
        return StreamingResponse(
            stream,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_history(user: dict = Depends(get_current_user)):
    """Obtiene el historial de consultas del usuario con manejo de valores nulos"""
    try:
        history = get_user_query_history(user["username"])
        
        # Asegurar que todos los campos tengan valores válidos
        processed_history = []
        for item in history:
            processed_item = {
                "id": item.get("id"),
                "query": item.get("query", ""),
                "timestamp": item["timestamp"].isoformat() if item.get("timestamp") else None,
                "execution_count": item.get("execution_count", 1),
                "username": item.get("username", user["username"]),
                "type": item.get("type", "Consultas")
            }
            processed_history.append(processed_item)
        
        return {"history": processed_history}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener historial: {str(e)}"
        )


@app.post("/execute")
async def run_sql(query: SQLQuery, user: dict = Depends(get_current_user)):
    try:
        # Guardar en el historial primero
        save_query_to_history(user["username"], query.query)
        
        # Si no es admin, aplicar restricciones
        if user["role"] != "admin":
            # Verificar que sea SELECT
            if not query.query.strip().lower().startswith("select"):
                raise HTTPException(
                    status_code=403,
                    detail="Solo puedes realizar consultas SELECT"
                )
            
            # Verificar tablas permitidas
            tablas_permitidas = ['airports', 'airlines', 'flights']
            query_lower = query.query.lower()
            
            if not any(f"from {tabla}" in query_lower or f"join {tabla}" in query_lower 
                      for tabla in tablas_permitidas):
                raise HTTPException(
                    status_code=403,
                    detail="Solo puedes consultar las tablas: airports, airlines y flights"
                )
        
        # Ejecutar la consulta
        result = execute_sql(query.query)
        df = pd.DataFrame(result)
        return {"result": df.to_dict(orient="records")}
    
    except HTTPException:
        raise  # Re-lanzar excepciones HTTP que ya hemos capturado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))