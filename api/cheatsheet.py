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

from contextlib import asynccontextmanager # lifespan event

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

import pandas as pd
import numpy as np

#lifespan custom para cargar el dataset
@asynccontextmanager
async def lifespan(app: FastAPI):
    #startup
    print("Iniciando servidor, cargando data set")
    app.state.df = pd.read_csv("../data/processed/clean_food_delivery.csv")
    app.state.df = app.state.df.replace({float('nan'): None}) #evitar problemas con NaN en JSON
    #initialize resources
    yield
    #shutdown
    print("Apagando servidor")


class Estrategia(BaseModel):
    dia_semana: int = Field(ge=0, le=6)
    hora_inicio: int = Field(ge=0, le=23)
    porcentaje_descuento: int = Field(gt=0, le=100)

app = FastAPI(lifespan=lifespan)

@app.get("/api/")
def read_root():
    return {"Hello": "World"}

# Endpoint para obtener el dataset (solo una muestra)
@app.get("/api/dataset")
def obtener_dataset(request: Request):
    df = request.app.state.df
    return df.head().to_dict(orient="records")

@app.get("/api/analisis-retrasos")
def analizar_retrasos():
    return {"message": "Análisis de retrasos"}

@app.get("/api/sugerir-combos/{categoria}/{precio_maximo}")
def sugerir_combos(categoria: str, precio_maximo: float):
    return {"categoria": categoria, "precio_maximo": precio_maximo}

@app.post("/api/estrategias/")
async def simular_estrategia(estrategia: Estrategia, request: Request):
    df = request.app.state.df
    
    # A. FILTRADO HISTÓRICO (Día y Hora específicos)
    # Grupo Control: Sin descuento
    df_base = df[
        (df['order_day_of_week'] == estrategia.dia_semana) & 
        (df['order_hour'] == estrategia.hora_inicio) & 
        (df['discount_value'] == 0)
    ]
    
    # Grupo Prueba: Con cualquier descuento previo
    df_hist_desc = df[
        (df['order_day_of_week'] == estrategia.dia_semana) & 
        (df['order_hour'] == estrategia.hora_inicio) & 
        (df['discount_value'] > 0)
    ]
    
    # B. CÁLCULO DE MÉTRICAS BASE
    conteo_base = len(df_base)
    ticket_promedio_base = df_base['total_amount'].mean() if conteo_base > 0 else 0
    
    conteo_desc_hist = len(df_hist_desc)
    
# --- LOGÍCA REPARADA: PROMEDIO POR DÍA ---
    # 1. Contamos cuántos días únicos existen en cada grupo para ese horario
    dias_base = df_base['order_timestamp'].str[:10].nunique()
    dias_desc = df_hist_desc['order_timestamp'].str[:10].nunique()

    # 2. Calculamos el promedio de pedidos que caen por día
    avg_pedidos_base = conteo_base / dias_base if dias_base > 0 else 0
    avg_pedidos_desc = conteo_desc_hist / dias_desc if dias_desc > 0 else 0

    # 3. La sensibilidad ahora es real: comparamos promedios, no totales
    if avg_pedidos_base > 0 and avg_pedidos_desc > 0:
        total_original_hist = df_hist_desc['total_amount'] + df_hist_desc['discount_value']
        pct_desc_hist = (df_hist_desc['discount_value'] / total_original_hist).mean()
        
        factor_incremento_real = avg_pedidos_desc / avg_pedidos_base
        sensibilidad = (factor_incremento_real - 1) / pct_desc_hist if pct_desc_hist > 0 else 1.5
    else:
        sensibilidad = 1.2 # Fallback si no hay historia
        
    # D. PROYECCIÓN DEL NUEVO ESCENARIO
    pct_usuario = estrategia.porcentaje_descuento / 100
    ganancia_volumen_proyectada = 1 + (pct_usuario * sensibilidad)
    
    pedidos_estimados = int(conteo_base * ganancia_volumen_proyectada)
    nuevo_ticket = ticket_promedio_base * (1 - pct_usuario)
    
    ingreso_historico = conteo_base * ticket_promedio_base
    ingreso_proyectado = pedidos_estimados * nuevo_ticket
    
    # E. LOGÍSTICA (3 pedidos por hora por repartidor)
    repartidores = int(np.ceil(pedidos_estimados / 3)) if pedidos_estimados > 0 else 0
    
    return {
        "metadatos": {
            "dia_analizado": estrategia.dia_semana,
            "hora_analizada": estrategia.hora_inicio,
            "sensibilidad_detectada": round(sensibilidad, 2)
        },
        "escenario_actual_sin_promo": {
            "pedidos_promedio": conteo_base,
            "ticket_promedio": round(ticket_promedio_base, 2),
            "ingreso_total": round(ingreso_historico, 2)
        },
        "proyeccion_con_descuento": {
            "pedidos_esperados": pedidos_estimados,
            "ticket_estimado": round(nuevo_ticket, 2),
            "ingreso_estimado": round(ingreso_proyectado, 2),
            "repartidores_necesarios": repartidores
        },
        "analisis_rentabilidad": {
            "impacto_monetario": round(ingreso_proyectado - ingreso_historico, 2),
            "es_rentable": bool(ingreso_proyectado > ingreso_historico) # Casting a bool nativo
        }
    }