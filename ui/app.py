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

    # --- PESTAÑAS INTERACTIVAS ---
    tab1, tab2 = st.tabs(["📊 Vista General", "📅 Desglose por Periodo"])

    with tab1:
        # --- VISUALIZACIONES EXISTENTES ---
        row1_col1, row1_col2 = st.columns(2)

        with row1_col1:
            st.subheader("📈 Tendencia de Recaudación Mensual")
            # Filtrar datos desde 2013
            df_consumo_filtered = df_consumo[df_consumo['Fpago'] >= '2013-01-01']
            df_trend = df_consumo_filtered.set_index('Fpago').resample('ME')['TOTAL'].sum().reset_index()
            df_trend['Fpago'] = df_trend['Fpago'].dt.strftime('%Y-%m')
            fig_trend = px.line(df_trend, x='Fpago', y='TOTAL', 
                                 labels={'TOTAL': 'Monto ($)', 'Fpago': 'Mes'},
                                 title="Ingresos por Cobranza de Agua (Desde 2013)")
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
            st.subheader("📍 Recaudación por Fraccionamiento")
            df_cons_lotes = df_consumo.merge(df_lotes[['id_lote', 'Fraccionamiento']], left_on='lote', right_on='id_lote')
            df_cons_agrupado = df_cons_lotes.groupby('Fraccionamiento')['TOTAL'].sum().reset_index()
            df_cons_final = df_cons_agrupado.merge(df_fracc, left_on='Fraccionamiento', right_on='Id_fraccionamiento')
            df_cons_final = df_cons_final.rename(columns={'Fraccionamiento_y': 'Nombre_Fraccionamiento'})
            
            fig_cons = px.bar(df_cons_final.sort_values('TOTAL', ascending=False).head(10), 
                               x='Nombre_Fraccionamiento', y='TOTAL', 
                               labels={'Nombre_Fraccionamiento': 'Fraccionamiento', 'TOTAL': 'Recaudación ($)'},
                               title="Top 10 Fraccionamientos por Recaudación",
                               color='TOTAL', color_continuous_scale='Viridis')
            st.plotly_chart(fig_cons, use_container_width=True)

    with tab2:
        st.subheader("🔍 Análisis Detallado por Periodo")
        
        # Filtros de periodo
        df_consumo['Año'] = df_consumo['Fpago'].dt.year
        df_consumo['Mes'] = df_consumo['Fpago'].dt.month
        
        years = sorted([y for y in df_consumo['Año'].dropna().unique().astype(int) if y >= 2013], reverse=True)
        
        col_f1, col_f2 = st.columns(2)
        selected_year = col_f1.selectbox("Selecciona el Año", options=years, index=0)
        
        available_months = sorted(df_consumo[df_consumo['Año'] == selected_year]['Mes'].unique().astype(int))
        month_names = {1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril', 5:'Mayo', 6:'Junio', 
                       7:'Julio', 8:'Agosto', 9:'Septiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre'}
        
        selected_month = col_f2.selectbox("Selecciona el Mes", 
                                          options=available_months, 
                                          format_func=lambda x: month_names[x])
        
        # Filtrado de datos
        df_periodo = df_consumo[(df_consumo['Año'] == selected_year) & (df_consumo['Mes'] == selected_month)]
        
        if not df_periodo.empty:
            m_recaudado = df_periodo['TOTAL'].sum()
            m_transacciones = len(df_periodo)
            
            st.info(f"**Resumen de {month_names[selected_month]} {selected_year}**")
            c1, c2 = st.columns(2)
            c1.metric("Recaudado en el Mes", f"${m_recaudado:,.2f}")
            c2.metric("Total de Pagos", m_transacciones)
            
            # Tabla detallada
            st.write("### Desglose por Concepto en el Periodo")
            df_desc = df_periodo.groupby('descripcion')['TOTAL'].agg(['sum', 'count']).reset_index()
            df_desc.columns = ['Concepto', 'Monto Total ($)', 'Número de Pagos']
            st.dataframe(df_desc.sort_values('Monto Total ($)', ascending=False), use_container_width=True)
            
            # Gráfico de barras por concepto
            fig_periodo = px.bar(df_desc, x='Concepto', y='Monto Total ($)', 
                                 title=f"Distribución de Ingresos - {month_names[selected_month]} {selected_year}",
                                 color='Monto Total ($)')
            st.plotly_chart(fig_periodo, use_container_width=True)
        else:
            st.warning("No hay datos disponibles para el periodo seleccionado.")

except Exception as e:
    st.error(f"Error al cargar o procesar los datos: {e}")
    st.info("Asegúrate de que los archivos CSV estén en 'data/processed/' y tengan el formato correcto.")
