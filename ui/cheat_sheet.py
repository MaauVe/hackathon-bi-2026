import streamlit as st
import pandas as pd
import random

# CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Simulador BI", layout="wide")
st.title("Simulador de Demanda de Heladería")
st.markdown("Herramienta interactiva para predecir la producción diaria")

# BARRA LATERAL
st.sidebar.header("Parámetros de Simulación")
temperatura = st.sidebar.slider("Temperatura esperada (°C)", min_value=15, max_value=40, value=25)
dia_semana = st.sidebar.selectbox("Día de la semana", ["Lunes - Jueves", "Viernes", "Sábado", "Domingo"])
promocion = st.sidebar.checkbox("¿Hay promoción 2x1 activa?")

# LÓGICA DE NEGOCIO SIMULADA (FastAPI)
ventas_base = 50 if dia_semana == "Lunes - Jueves" else 150
ajuste_clima = (temperatura - 20) * 5 
ajuste_promo = 40 if promocion else 0

ventas_proyectadas = ventas_base + ajuste_clima + ajuste_promo

# MÉTRICAS DE IMPACTO
st.subheader("Proyecciones del Día")
col1, col2, col3 = st.columns(3)

col1.metric(label="Ventas Proyectadas (Litros)", value=f"{ventas_proyectadas}", delta=f"{ajuste_clima} por clima")
col2.metric(label="Sabor Recomendado", value="Limón" if temperatura > 30 else "Chocolate")
col3.metric(label="Riesgo de Merma", value="Alto" if temperatura < 20 else "Bajo", delta_color="inverse")

# TABLAS Y GRÁFICAS
st.subheader("Datos Históricos Simulados")

datos_ficticios = pd.DataFrame({
    'Sabor': ['Vainilla', 'Chocolate', 'Fresa', 'Limón', 'Menta'],
    'Litros Vendidos': [14, 25, 61, 72, 81]
})

# Gráfica de barras y tabla
st.bar_chart(datos_ficticios.set_index('Sabor'))
st.dataframe(datos_ficticios, use_container_width=True)