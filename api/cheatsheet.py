from fastapi import FastAPI, HTTPException, Query, Path, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# FastAPI Cheatsheet for Business Intelligence Hackaton


# ===== APP SETUP =====
app = FastAPI(title="BI API", version="1.0.0")

# ===== DATA MODELS =====
class DataPoint(BaseModel):
    id: int
    name: str
    value: float
    category: str

class Report(BaseModel):
    title: str
    data: List[DataPoint]
    timestamp: Optional[str] = None

# ===== BASIC ROUTES =====
@app.get("/")
async def root():
    return {"message": "BI API Running"}

@app.get("/health")
async def health():
    return {"status": "ok"}

# ===== GET REQUESTS =====
@app.get("/data")
async def get_data(skip: int = Query(0), limit: int = Query(10)):
    """Get paginated data"""
    return {"data": [], "skip": skip, "limit": limit}

@app.get("/data/{item_id}")
async def get_item(item_id: int = Path(..., gt=0)):
    """Get specific item by ID"""
    return {"id": item_id}

# ===== POST REQUESTS =====
@app.post("/reports")
async def create_report(report: Report):
    """Create new report"""
    return {"status": "created", "data": report}

# ===== PUT/DELETE =====
@app.put("/data/{item_id}")
async def update_item(item_id: int, data: DataPoint):
    return {"id": item_id, "updated": data}

@app.delete("/data/{item_id}")
async def delete_item(item_id: int):
    return {"deleted": item_id}

# ===== FILTERS & SEARCH =====
@app.get("/search")
async def search(q: str = Query(..., min_length=1), category: Optional[str] = None):
    return {"query": q, "category": category}

# ===== ERROR HANDLING =====
@app.get("/item/{item_id}")
async def get_item_error(item_id: int):
    if item_id < 1:
        raise HTTPException(status_code=400, detail="Invalid ID")
    if item_id == 999:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item_id}

# ===== RUN SERVER =====
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# USEFUL COMMANDS:
# pip install fastapi uvicorn
# python cheatsheet.py
# Visit: http://localhost:8000/docs (Swagger UI)
# Visit: http://localhost:8000/redoc (ReDoc)

from fastapi import FastAPI, Request
from pydantic import BaseModel
import pandas as pd
import numpy as np

app = FastAPI()

# 1. CARGA AUTOMÁTICA (Mañana solo cambias el nombre del archivo)
@app.on_event("startup")
def startup_event():
    try:
        df = pd.read_csv("archivo_que_te_den.csv")
        # Limpieza básica universal
        df = df.replace({np.nan: None})
        app.state.df = df
        print("✅ Datos listos para la batalla")
    except:
        print("❌ Aún no tienes el archivo, cárgalo mañana")

# 2. MODELO DINÁMICO (Lo ajustas según la problemática)
class Consulta(BaseModel):
    variable_filtro: str # Ej: 'Categoria' o 'Ciudad'
    valor_buscado: float # Ej: Un precio o un descuento

# 3. EL ENDPOINT QUE TE DA PUNTOS (Análisis Predictivo)
@app.post("/api/analizar")
def analizar(datos: Consulta, request: Request):
    df = request.app.state.df
    
    # FILTRO UNIVERSAL (Boolean Mask)
    # Mañana cambias 'columna_ejemplo' por la columna real
    mask = (df['columna_ejemplo'] == datos.variable_filtro)
    subset = df[mask]
    
    # CÁLCULOS RÁPIDOS
    resultado = subset['columna_numerica'].mean()
    
    return {
        "analisis": "Descriptivo",
        "resultado": round(resultado, 2),
        "conteo": len(subset)
    }