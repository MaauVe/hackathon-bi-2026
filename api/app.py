from fastapi import FastAPI
from pydantic import BaseModel, Field

class Estrategia(BaseModel):
    dia_semana: int = Field(ge=0, le=6)
    hora_inicio: int = Field(ge=0, le=23)
    porcentaje_descuento: int = Field(gt=0, le=100)

app = FastAPI()

@app.get("/api/")
def read_root():
    return {"Hello": "World"}

@app.get("/api/analisis-retrasos")
def analizar_retrasos():
    return {"message": "Análisis de retrasos"}

@app.get("/api/sugerir-combos/{categoria}/{precio_maximo}")
def sugerir_combos(categoria: str, precio_maximo: float):
    return {"categoria": categoria, "precio_maximo": precio_maximo}

@app.post("/api/estrategias/")
def simular_estrategia(estrategia: Estrategia):
    return estrategia