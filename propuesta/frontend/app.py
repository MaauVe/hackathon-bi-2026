import streamlit as st
import pandas as pd
import plotly.express as px
from database import run_query, execute_statement
from sqlalchemy import text
from datetime import datetime

st.set_page_config(page_title="Sistema de Gestión de Agua Potable - BI", layout="wide")

st.sidebar.title("Navegación")
page = st.sidebar.radio("Ir a:", ["Dashboard BI", "Registrar Consumo", "Registrar Transacción", "Catálogos"])

if page == "Dashboard BI":
    st.title("📊 Dashboard de Inteligencia de Negocios")
    
    col1, col2, col3 = st.columns(3)
    
    # KPIs Reales
    total_ingresos = run_query("SELECT SUM(monto) FROM Transacciones WHERE tipo_movimiento='ingreso'").iloc[0,0] or 0
    total_egresos = run_query("SELECT SUM(monto) FROM Transacciones WHERE tipo_movimiento='egreso'").iloc[0,0] or 0
    total_consumo = run_query("SELECT SUM(total) FROM Consumo").iloc[0,0] or 0
    
    col1.metric("Total Ingresos", f"${total_ingresos:,.2f}")
    col2.metric("Total Egresos", f"${total_egresos:,.2f}")
    col3.metric("Total Facturado (Consumo)", f"${total_consumo:,.2f}")
    
    st.divider()
    
    # 1. Gráfico de Ingresos vs Egresos por Tiempo
    st.subheader("📈 Evolución Financiera")
    df_finanzas = run_query("""
        SELECT DATE_FORMAT(fecha, '%Y-%m') as mes, tipo_movimiento, SUM(monto) as total 
        FROM Transacciones 
        GROUP BY mes, tipo_movimiento 
        ORDER BY mes
    """)
    if not df_finanzas.empty:
        fig_fin = px.line(df_finanzas, x="mes", y="total", color="tipo_movimiento", 
                         title="Ingresos vs Egresos Mensuales", markers=True)
        st.plotly_chart(fig_fin, use_container_width=True)
    
    # 2. Distribución por Fraccionamiento
    st.subheader("🏘️ Situación por Fraccionamiento")
    df_frac = run_query("""
        SELECT f.Nombre, SUM(v.saldo) as deuda_total, COUNT(v.ID) as num_viviendas
        FROM Fraccionamiento f
        JOIN Lote l ON f.ID = l.id_fraccionamiento
        JOIN Vivienda v ON l.ID = v.id_lote
        GROUP BY f.Nombre
    """)
    if not df_frac.empty:
        fig_frac = px.bar(df_frac, x="Nombre", y="deuda_total", color="num_viviendas",
                         title="Adeudos Totales por Fraccionamiento",
                         labels={"Nombre": "Fraccionamiento", "deuda_total": "Saldo Pendiente ($)"})
        st.plotly_chart(fig_frac, use_container_width=True)

    # 3. Consumo por Tipo de Servicio
    st.subheader("💧 Consumo por Tipo de Servicio")
    df_cons = run_query("""
        SELECT ts.TipoServicio, SUM(c.total) as total_ventas, SUM(c.Cantidad) as vol_total
        FROM Consumo c
        JOIN TipoServicio ts ON c.id_tipo_de_servicio = ts.ID
        GROUP BY ts.TipoServicio
    """)
    if not df_cons.empty:
        fig_cons = px.pie(df_cons, values="total_ventas", names="TipoServicio", title="Distribución de Ingresos por Tipo de Servicio")
        st.plotly_chart(fig_cons, use_container_width=True)

elif page == "Registrar Consumo":
    st.title("🚰 Registro de Consumo de Agua")
    
    with st.form("form_consumo"):
        viviendas = run_query("SELECT ID, Clave FROM Vivienda")
        v_options = {row['Clave']: row['ID'] for _, row in viviendas.iterrows()}
        vivienda_sel = st.selectbox("Vivienda", options=list(v_options.keys()))
        
        periodos = run_query("SELECT ID, Anio, semana FROM Periodo ORDER BY Anio DESC, semana DESC")
        p_options = {f"{row['Anio']} - Sem {row['semana']}": row['ID'] for _, row in periodos.iterrows()}
        periodo_sel = st.selectbox("Periodo", options=list(p_options.keys()))
        
        servicios = run_query("SELECT ID, TipoServicio FROM TipoServicio")
        s_options = {row['TipoServicio']: row['ID'] for _, row in servicios.iterrows()}
        servicio_sel = st.selectbox("Tipo de Servicio", options=list(s_options.keys()))
        
        cantidad = st.number_input("Cantidad", min_value=0.0, step=0.1)
        total = st.number_input("Monto Total ($)", min_value=0.0, step=0.1)
        orden = st.text_input("ID Orden de Compra", value=f"OC-{datetime.now().strftime('%M%S')}")
        
        submitted = st.form_submit_button("Registrar Consumo")
        if submitted:
            execute_statement(text("""
                INSERT INTO Consumo (IDordenCompra, Cantidad, total, id_tipo_de_servicio, id_vivienda, id_periodo)
                VALUES (:oc, :can, :tot, :ts, :v, :p)
            """), {
                "oc": orden, "can": cantidad, "tot": total, 
                "ts": s_options[servicio_sel], "v": v_options[vivienda_sel], "p": p_options[periodo_sel]
            })
            st.success("Consumo registrado correctamente.")

elif page == "Registrar Transacción":
    st.title("💸 Registro de Transacción (Ingreso/Egreso)")
    
    with st.form("form_transaccion"):
        tipo = st.selectbox("Tipo de Movimiento", ["ingreso", "egreso"])
        monto = st.number_input("Monto ($)", min_value=0.0, step=0.1)
        
        conceptos = run_query("SELECT ID, concepto FROM Conceptos")
        c_options = {row['concepto']: row['ID'] for _, row in conceptos.iterrows()}
        concepto_sel = st.selectbox("Concepto", options=list(c_options.keys()))
        
        ccostos = run_query("SELECT ID, descripcion FROM CCostos")
        cc_options = {row['descripcion']: row['ID'] for _, row in ccostos.iterrows()}
        ccosto_sel = st.selectbox("Centro de Costos", options=list(cc_options.keys()))
        
        fecha = st.date_input("Fecha", datetime.now())
        
        submitted = st.form_submit_button("Guardar Transacción")
        if submitted:
            execute_statement(text("""
                INSERT INTO Transacciones (fecha, monto, tipo_movimiento, id_ccostos, id_concepto)
                VALUES (:f, :m, :tm, :cc, :c)
            """), {
                "f": fecha, "m": monto, "tm": tipo, 
                "cc": cc_options[ccosto_sel], "c": c_options[concepto_sel]
            })
            st.success("Transacción guardada correctamente.")

elif page == "Catálogos":
    st.title("📂 Administración de Catálogos")
    cat = st.tabs(["Fraccionamientos", "Viviendas", "Usuarios"])
    
    with cat[0]:
        st.subheader("Lista de Fraccionamientos")
        df = run_query("SELECT * FROM Fraccionamiento")
        st.dataframe(df, use_container_width=True)
        
    with cat[1]:
        st.subheader("Lista de Viviendas")
        df = run_query("""
            SELECT v.ID, v.Clave, f.Nombre as Fraccionamiento, u.Nombre as Propietario, v.saldo
            FROM Vivienda v
            JOIN Lote l ON v.id_lote = l.ID
            JOIN Fraccionamiento f ON l.id_fraccionamiento = f.ID
            JOIN Usuario u ON v.id_user = u.ID
        """)
        st.dataframe(df, use_container_width=True)
        
    with cat[2]:
        st.subheader("Usuarios Registrados")
        df = run_query("SELECT * FROM Usuario")
        st.dataframe(df, use_container_width=True)
