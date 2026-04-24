import streamlit as st
import pandas as pd
import plotly.express as px
from database import run_query, execute_statement
from sqlalchemy import text
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Sistema de Gestión de Agua", layout="wide", initial_sidebar_state="expanded")

# Estilo personalizado para las métricas y botones
st.markdown("""
    <style>
    .stMetric {
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(128, 128, 128, 0.1);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        border-radius: 4px 4px 0px 0px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Funciones de Utilidad ---
@st.cache_data(ttl=5)
def get_catalogo(tabla):
    return run_query(f"SELECT * FROM {tabla}")

# --- BARRA LATERAL (Navegación Principal) ---
st.sidebar.title("Administración de Agua")
menu = st.sidebar.radio("Ir a:", [
    "Resumen", 
    "Pagos y Gastos", 
    "Lecturas de Agua", 
    "Administración"
])

# --- Lógica de Páginas ---

if menu == "Resumen":
    st.title("Resumen de Operaciones")
    st.markdown("Información general del sistema basada en registros reales.")

    # KPIs Superiores
    col1, col2, col3, col4 = st.columns(4)
    total_recaudado = run_query("SELECT SUM(total) FROM Consumo").iloc[0,0] or 0
    total_deuda = run_query("SELECT SUM(saldo) FROM Vivienda").iloc[0,0] or 0
    num_mora = run_query("SELECT COUNT(*) FROM Vivienda WHERE saldo > 0").iloc[0,0] or 0
    eficiencia = (total_recaudado / (total_recaudado + total_deuda)) * 100 if (total_recaudado + total_deuda) > 0 else 0

    col1.metric("Recaudación Total", f"${total_recaudado:,.2f}")
    col2.metric("Deuda Pendiente", f"${total_deuda:,.2f}", delta=f"-{total_deuda:,.2f}", delta_color="inverse")
    col3.metric("Eficiencia de Cobranza", f"{eficiencia:.2f}%")
    col4.metric("Viviendas en Mora", num_mora)

    st.divider()

    tab1, tab2 = st.tabs(["General", "Por Periodo"])

    with tab1:
        r1_c1, r1_c2 = st.columns(2)
        with r1_c1:
            st.subheader("Tendencia de Recaudación")
            df_trend = run_query("""
                SELECT DATE_FORMAT(fecha_inicio, '%Y-%m') as mes, SUM(c.total) as total
                FROM Consumo c JOIN Periodo p ON c.id_periodo = p.ID
                GROUP BY mes ORDER BY mes
            """)
            if not df_trend.empty:
                st.plotly_chart(px.line(df_trend, x='mes', y='total', title="Ingresos Mensuales"), use_container_width=True)

        with r1_c2:
            st.subheader("Deuda por Fraccionamiento")
            df_deuda = run_query("""
                SELECT f.Nombre as Fracc, SUM(v.saldo) as deuda
                FROM Vivienda v JOIN Lote l ON v.id_lote = l.ID JOIN Fraccionamiento f ON l.id_fraccionamiento = f.ID
                GROUP BY Fracc ORDER BY deuda DESC LIMIT 10
            """)
            if not df_deuda.empty:
                st.plotly_chart(px.bar(df_deuda, x='Fracc', y='deuda', color='deuda', color_continuous_scale='Reds'), use_container_width=True)

        r2_c1, r2_c2 = st.columns(2)
        with r2_c1:
            st.subheader("Distribución de Consumo")
            df_tipo = run_query("""
                SELECT ts.TipoServicio, SUM(c.total) as total FROM Consumo c
                JOIN TipoServicio ts ON c.id_tipo_de_servicio = ts.ID GROUP BY ts.TipoServicio
            """)
            if not df_tipo.empty:
                st.plotly_chart(px.pie(df_tipo, values='total', names='TipoServicio'), use_container_width=True)

        with r2_c2:
            st.subheader("Cobros por Fraccionamiento")
            df_rec = run_query("""
                SELECT f.Nombre as Fracc, SUM(c.total) as total
                FROM Consumo c JOIN Vivienda v ON c.id_vivienda = v.ID 
                JOIN Lote l ON v.id_lote = l.ID JOIN Fraccionamiento f ON l.id_fraccionamiento = f.ID
                GROUP BY Fracc ORDER BY total DESC LIMIT 10
            """)
            if not df_rec.empty:
                st.plotly_chart(px.bar(df_rec, x='Fracc', y='total', color='total', color_continuous_scale='Viridis'), use_container_width=True)

    with tab2:
        years_df = run_query("SELECT DISTINCT Anio FROM Periodo ORDER BY Anio DESC")
        if not years_df.empty:
            years = years_df['Anio'].tolist()
            col_y, col_s = st.columns(2)
            sel_y = col_y.selectbox("Año", years)
            weeks = run_query(f"SELECT DISTINCT semana FROM Periodo WHERE Anio={sel_y} ORDER BY semana")['semana'].tolist()
            sel_w = col_s.selectbox("Semana", weeks)
            
            df_p = run_query(f"""
                SELECT ts.TipoServicio, SUM(c.total) as total, COUNT(*) as registros
                FROM Consumo c JOIN Periodo p ON c.id_periodo = p.ID JOIN TipoServicio ts ON c.id_tipo_de_servicio = ts.ID
                WHERE p.Anio = {sel_y} AND p.semana = {sel_w} GROUP BY ts.TipoServicio
            """)
            if not df_p.empty:
                st.info(f"Resumen Semana {sel_w}, {sel_y} | Total: ${df_p['total'].sum():,.2f}")
                st.dataframe(df_p, use_container_width=True, hide_index=True)
                st.plotly_chart(px.bar(df_p, x='TipoServicio', y='total', color='total'), use_container_width=True)

elif menu == "Pagos y Gastos":
    st.title("Pagos y Gastos")
    t1, t2 = st.tabs(["Nuevo Registro", "Historial"])
    with t1:
        with st.form("f_fin", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                tipo = st.selectbox("Tipo de movimiento", ["ingreso", "egreso"])
                monto = st.number_input("Monto", min_value=0.0)
            with c2:
                cc_df = get_catalogo("CCostos")
                cc = {r['descripcion']: r['ID'] for _, r in cc_df.iterrows()}
                cc_sel = st.selectbox("Centro de costo", list(cc.keys()))
                con_df = get_catalogo("Conceptos")
                con = {r['concepto']: r['ID'] for _, r in con_df.iterrows()}
                con_sel = st.selectbox("Concepto", list(con.keys()))
            if st.form_submit_button("Guardar"):
                execute_statement(text("INSERT INTO Transacciones (fecha, monto, tipo_movimiento, id_ccostos, id_concepto) VALUES (NOW(), :m, :t, :cc, :c)"),
                                 {"m": monto, "t": tipo, "cc": cc[cc_sel], "c": con[con_sel]})
                st.success("Registro guardado.")
    with t2:
        st.dataframe(run_query("SELECT t.ID, t.fecha, t.monto, t.tipo_movimiento, cc.descripcion as CC, c.concepto FROM Transacciones t JOIN CCostos cc ON t.id_ccostos = cc.ID JOIN Conceptos c ON t.id_concepto = c.ID ORDER BY t.fecha DESC"), use_container_width=True, hide_index=True)

elif menu == "Lecturas de Agua":
    st.title("Registro de Agua")
    with st.form("f_cons", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            viv_df = run_query("SELECT v.ID, v.Clave, f.Nombre FROM Vivienda v JOIN Lote l ON v.id_lote = l.ID JOIN Fraccionamiento f ON l.id_fraccionamiento = f.ID")
            viv = {f"{r['Nombre']} - {r['Clave']}": r['ID'] for _, r in viv_df.iterrows()}
            v_sel = st.selectbox("Vivienda", list(viv.keys()))
            per_df = get_catalogo("Periodo")
            per = {f"{r['Anio']} - S{r['semana']}": r['ID'] for _, r in per_df.iterrows()}
            p_sel = st.selectbox("Periodo", list(per.keys()))
        with c2:
            ts_df = get_catalogo("TipoServicio")
            ts = {r['TipoServicio']: r['ID'] for _, r in ts_df.iterrows()}
            ts_sel = st.selectbox("Servicio", list(ts.keys()))
            cant = st.number_input("Cantidad (m3)", min_value=0.0)
            tot = st.number_input("Monto total", min_value=0.0)
        if st.form_submit_button("Guardar lectura"):
            execute_statement(text("INSERT INTO Consumo (IDordenCompra, Cantidad, total, id_tipo_de_servicio, id_vivienda, id_periodo) VALUES (:oc, :can, :tot, :ts, :v, :p)"),
                             {"oc": f"OC-{datetime.now().strftime('%M%S')}", "can": cant, "tot": tot, "ts": ts[ts_sel], "v": viv[v_sel], "p": per[p_sel]})
            st.success("Lectura guardada.")

elif menu == "Administración":
    st.title("Administración del Sistema")
    cat = st.tabs(["Lotes", "Viviendas", "Usuarios", "Fraccionamientos", "Conceptos y Costos"])
    
    with cat[0]: # LOTES
        c1, c2 = st.columns([2, 1])
        with c2:
            with st.expander("Agregar nuevo lote", expanded=True):
                f_df = get_catalogo("Fraccionamiento")
                f_map = {r['Nombre']: r['ID'] for _, r in f_df.iterrows()}
                f_sel = st.selectbox("Fraccionamiento", list(f_map.keys()))
                tl_df = get_catalogo("TipoLote")
                tl_map = {r['TipoLote']: r['ID'] for _, r in tl_df.iterrows()}
                tl_sel = st.selectbox("Tipo de lote", list(tl_map.keys()))
                l_c, l_m = st.text_input("Clave"), st.text_input("Manzana")
                if st.button("Guardar lote"):
                    execute_statement(text("INSERT INTO Lote (id_fraccionamiento, id_tipo, Clave, manzana) VALUES (:f, :t, :c, :m)"), {"f": f_map[f_sel], "t": tl_map[tl_sel], "c": l_c, "m": l_m})
                    st.rerun()
        with c1:
            st.dataframe(run_query("SELECT l.ID, f.Nombre as Fracc, tl.TipoLote as Tipo, l.Clave, l.manzana FROM Lote l JOIN Fraccionamiento f ON l.id_fraccionamiento = f.ID JOIN TipoLote tl ON l.id_tipo = tl.ID"), use_container_width=True, hide_index=True)

    with cat[1]: # VIVIENDAS
        c1, c2 = st.columns([2, 1])
        with c2:
            with st.expander("Agregar nueva vivienda", expanded=True):
                l_df = run_query("SELECT l.ID, l.Clave, f.Nombre FROM Lote l JOIN Fraccionamiento f ON l.id_fraccionamiento = f.ID")
                l_map = {f"{r['Nombre']} - {r['Clave']}": r['ID'] for _, r in l_df.iterrows()}
                l_sel = st.selectbox("Lote", list(l_map.keys()))
                u_df = get_catalogo("Usuario")
                u_map = {r['Nombre']: r['ID'] for _, r in u_df.iterrows()}
                u_sel = st.selectbox("Propietario", list(u_map.keys()))
                vc, vs = st.text_input("Clave vivienda"), st.number_input("Saldo inicial")
                if st.button("Guardar vivienda"):
                    execute_statement(text("INSERT INTO Vivienda (id_lote, id_user, Clave, saldo) VALUES (:l, :u, :c, :s)"), {"l": l_map[l_sel], "u": u_map[u_sel], "c": vc, "s": vs})
                    st.rerun()
        with c1:
            st.dataframe(run_query("SELECT v.ID, v.Clave, f.Nombre as Fracc, u.Nombre as Dueño, v.saldo FROM Vivienda v JOIN Lote l ON v.id_lote = l.ID JOIN Fraccionamiento f ON l.id_fraccionamiento = f.ID JOIN Usuario u ON v.id_user = u.ID"), use_container_width=True, hide_index=True)

    with cat[2]: # USUARIOS
        c1, c2 = st.columns([2, 1])
        with c2:
            with st.expander("Agregar nuevo usuario", expanded=True):
                n, t, e = st.text_input("Nombre completo"), st.text_input("Teléfono"), st.text_input("Correo electrónico")
                if st.button("Guardar usuario"):
                    execute_statement(text("INSERT INTO Usuario (Nombre, Telefono, Email) VALUES (:n, :t, :e)"), {"n": n, "t": t, "e": e})
                    st.rerun()
        with c1: st.dataframe(get_catalogo("Usuario"), use_container_width=True, hide_index=True)

    with cat[3]: # FRACC
        c1, c2 = st.columns([2, 1])
        with c2:
            with st.expander("Agregar nuevo fraccionamiento", expanded=True):
                c, n, l = st.text_input("Clave"), st.text_input("Nombre"), st.number_input("Número de lotes", min_value=0)
                if st.button("Guardar fraccionamiento"):
                    execute_statement(text("INSERT INTO Fraccionamiento (Clave, Nombre, No_lotes) VALUES (:c, :n, :l)"), {"c": c, "n": n, "l": l})
                    st.rerun()
        with c1: st.dataframe(get_catalogo("Fraccionamiento"), use_container_width=True, hide_index=True)

    with cat[4]: # CONCEPTOS
        cl, cr = st.columns(2)
        with cl:
            st.subheader("Conceptos")
            with st.expander("Agregar nuevo concepto"):
                with st.form("form_concept", clear_on_submit=True):
                    cn = st.text_input("Nombre del concepto")
                    cs = st.selectbox("Clasificación", [
                        "Ingresos por Suministro", 
                        "Ingresos Extraordinarios",
                        "Gastos de Operación", 
                        "Gastos Administrativos",
                        "Mantenimiento y Reparaciones",
                        "Impuestos y Cuotas",
                        "Gastos Bancarios"
                    ])
                    if st.form_submit_button("Guardar concepto"):
                        if cn:
                            check = run_query(text("SELECT ID FROM Conceptos WHERE concepto = :n"), {"n": cn})
                            if not check.empty:
                                st.error("Ese concepto ya existe.")
                            else:
                                execute_statement(text("INSERT INTO Conceptos (concepto, clasificacion) VALUES (:n, :s)"), {"n": cn, "s": cs})
                                st.rerun()
                        else:
                            st.error("El nombre es obligatorio.")
            st.dataframe(get_catalogo("Conceptos"), use_container_width=True, hide_index=True)
        with cr:
            st.subheader("Centros de costo")
            with st.expander("Agregar nuevo centro"):
                with st.form("form_cc", clear_on_submit=True):
                    cd = st.text_input("Descripción")
                    if st.form_submit_button("Guardar centro"):
                        if cd:
                            check = run_query(text("SELECT ID FROM CCostos WHERE descripcion = :d"), {"d": cd})
                            if not check.empty:
                                st.error("Ese centro de costo ya existe.")
                            else:
                                execute_statement(text("INSERT INTO CCostos (descripcion) VALUES (:d)"), {"d": cd})
                                st.rerun()
                        else:
                            st.error("La descripción es obligatoria.")
            st.dataframe(get_catalogo("CCostos"), use_container_width=True, hide_index=True)
