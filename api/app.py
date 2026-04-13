from contextlib import asynccontextmanager # lifespan event

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

import pandas as pd

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
def simular_estrategia(estrategia: Estrategia):
    return estrategia