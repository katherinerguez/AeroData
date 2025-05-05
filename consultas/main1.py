from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from database import execute_sql
import pandas as pd
import io

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Modelo para recibir consultas SQL
class SQLQuery(BaseModel):
    query: str

# --- Ruta para mostrar la interfaz web ---
@app.get("/", response_class=HTMLResponse)
async def mostrar_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# --- Ruta para ejecutar consultas SQL ---
@app.post("/execute")
async def run_sql(query: SQLQuery):
    if not query.query.strip().lower().startswith("select"):
        raise HTTPException(status_code=400, detail="Solo se permiten consultas SELECT")
    
    try:
        result = execute_sql(query.query)
        # Convertir resultado a DataFrame
        df = pd.DataFrame(result)
        return {"result": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Ruta para descargar como CSV o Excel ---
@app.post("/download/{formato}")
async def download_sql(query: SQLQuery, formato: str):
    if not query.query.strip().lower().startswith("select"):
        raise HTTPException(status_code=400, detail="Solo se permiten consultas SELECT")
    
    try:
        result = execute_sql(query.query)
        df = pd.DataFrame(result)

        # Generar archivo CSV o Excel
        if formato.lower() == "csv":
            stream = io.StringIO()
            df.to_csv(stream, index=False)
            media_type = "text/csv"
            filename = "consulta.csv"
        elif formato.lower() in ["xlsx", "excel"]:
            stream = io.BytesIO()
            df.to_excel(stream, index=False, engine='openpyxl')
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = "consulta.xlsx"
        else:
            raise HTTPException(status_code=400, detail="Formato no soportado. Usa 'csv' o 'xlsx'.")

        # Devolver archivo como descarga
        stream.seek(0)
        return StreamingResponse(
            stream,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))