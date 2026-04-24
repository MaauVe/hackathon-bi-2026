import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard de Gestión de Agua - BI", layout="wide")

st.title("📊 Inteligencia de Negocios: Gestión de Agua Potable")
st.markdown("### Análisis basado en registros de consumo, viviendas y lotes")

# 1. Carga de datos
@st.cache_data
def load_data():
    viviendas = pd.read_csv('data/processed/viviendas.csv', encoding='latin1')
    consumo = pd.read_csv('data/processed/consumo_agua.csv', encoding='latin1')
    fraccionamientos = pd.read_csv('data/processed/fraccionamientos.csv', encoding='latin1')
    lotes = pd.read_csv('data/processed/lotes.csv', encoding='latin1')
    
    # Preprocesamiento de fechas
    consumo['Fpago'] = pd.to_datetime(consumo['Fpago'], dayfirst=True, errors='coerce')
    
    return viviendas, consumo, fraccionamientos, lotes

try:
    df_viviendas, df_consumo, df_fracc, df_lotes = load_data()

    # --- CÁLCULO DE KPIs ---
    
    # 1. Recaudación Total (basado en consumo pagado)
    total_recaudado = df_consumo['TOTAL'].sum()
    
    # 2. Deuda Total y Viviendas en Mora
    total_deuda = df_viviendas['saldo_deudor'].sum()
    viviendas_con_deuda = df_viviendas[df_viviendas['saldo_deudor'] > 0]
    num_mora = len(viviendas_con_deuda)
    
    # 3. Eficiencia de Cobranza (Recaudado vs Facturado proyectado)
    # Proyectamos el facturado como lo recaudado + la deuda actual
    total_facturado_est = total_recaudado + total_deuda
    eficiencia = (total_recaudado / total_facturado_est) * 100 if total_facturado_est > 0 else 0

    # 4. Saldo a Favor
    total_favor = df_viviendas['saldo_favor'].sum()

    # --- INTERFAZ DE USUARIO (KPIs) ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Recaudación Histórica", f"${total_recaudado:,.2f}")
    col2.metric("Deuda Pendiente", f"${total_deuda:,.2f}", delta=f"-{total_deuda:,.2f}", delta_color="inverse")
    col3.metric("Eficiencia de Cobranza", f"{eficiencia:.2f}%")
    col4.metric("Viviendas en Mora", num_mora)

    st.divider()

    # --- VISUALIZACIONES ---
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.subheader("📈 Tendencia de Recaudación Mensual")
        df_trend = df_consumo.set_index('Fpago').resample('ME')['TOTAL'].sum().reset_index()
        df_trend['Fpago'] = df_trend['Fpago'].dt.strftime('%Y-%m')
        fig_trend = px.line(df_trend, x='Fpago', y='TOTAL', 
                             labels={'TOTAL': 'Monto ($)', 'Fpago': 'Mes'},
                             title="Ingresos por Cobranza de Agua")
        st.plotly_chart(fig_trend, use_container_width=True)

    with row1_col2:
        st.subheader("🏘️ Deuda por Fraccionamiento")
        df_deuda_fracc = df_viviendas.groupby('fraccionamiento_id')['saldo_deudor'].sum().reset_index()
        df_deuda_fracc = df_deuda_fracc.merge(df_fracc, left_on='fraccionamiento_id', right_on='Id_fraccionamiento')
        fig_deuda = px.bar(df_deuda_fracc.sort_values('saldo_deudor', ascending=False).head(10), 
                            x='Fraccionamiento', y='saldo_deudor', 
                            title="Top 10 Fraccionamientos con mayor deuda",
                            color='saldo_deudor', color_continuous_scale='Reds')
        st.plotly_chart(fig_deuda, use_container_width=True)

    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.subheader("💧 Distribución de Consumo por Tipo")
        df_tipo = df_consumo.groupby('descripcion')['TOTAL'].sum().reset_index()
        fig_tipo = px.pie(df_tipo, values='TOTAL', names='descripcion', title="Composición de Ingresos")
        st.plotly_chart(fig_tipo, use_container_width=True)

    with row2_col2:
        st.subheader("📍 Consumo por Fraccionamiento")
        # Unir consumo con lotes para obtener el ID del fraccionamiento
        df_cons_lotes = df_consumo.merge(df_lotes[['id_lote', 'Fraccionamiento']], left_on='lote', right_on='id_lote')
        # Agrupar por el ID del fraccionamiento (columna 'Fraccionamiento' de df_lotes)
        df_cons_agrupado = df_cons_lotes.groupby('Fraccionamiento')['TOTAL'].sum().reset_index()
        # Unir con nombres reales de fraccionamientos
        df_cons_final = df_cons_agrupado.merge(df_fracc, left_on='Fraccionamiento', right_on='Id_fraccionamiento')
        df_cons_final = df_cons_final.rename(columns={'Fraccionamiento_y': 'Nombre_Fraccionamiento'})
        
        fig_cons = px.bar(df_cons_final.sort_values('TOTAL', ascending=False).head(10), 
                           x='Nombre_Fraccionamiento', y='TOTAL', 
                           labels={'Nombre_Fraccionamiento': 'Fraccionamiento', 'TOTAL': 'Recaudación ($)'},
                           title="Top 10 Fraccionamientos por Recaudación",
                           color='TOTAL', color_continuous_scale='Viridis')
        st.plotly_chart(fig_cons, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar o procesar los datos: {e}")
    st.info("Asegúrate de que los archivos CSV estén en 'data/processed/' y tengan el formato correcto.")
