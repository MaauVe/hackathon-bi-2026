import streamlit as st
import pandas as pd

st.set_page_config(page_title="Simulador BI", layout="wide")
st.title("Asistente Inteligente de Optimización", text_alignment="center")
st.markdown("Buenos dias, ¿Que vamos a calcular hoy?",text_alignment="center")

#---------------------------------------------------
st.subheader("Metricas Generales")
col1, col2, col3 = st.columns(3, border = True)
with col1:
    st.markdown("Ticket promedio (AOV)")
    col1.subheader("10 tickets / 5 min")
with col2:
    st.markdown("Tiempo promedio de entrega")
    col2.subheader("33.50 minutos")
with col3:
    st.markdown("Tasa de cancelación")
    col3.subheader("4.2%")
st.space(size="small")

#---------------------------------------------------
st.subheader("Detector de Fugas de Dinero")
col1, col2, col3 = st.columns([0.2, 0.2, 0.6], border = True)
with col1:
    st.markdown("Tiempos de Entrega Promedio en la Zona")
    col1.subheader("53.12 minutos")
with col2:
    st.markdown("Clientes Insatisfechos")
    col2.subheader("12")
with col3:
    df = pd.DataFrame({
        "lat": [40.72984562595833],
        "lon": [-74.06750605942786]
    })
    st.map(df, zoom = 13)
st.space(size="small")

#---------------------------------------------------
st.subheader("Combos Recurrentes")
col1, col2 = st.columns(2, border = True)
with col1:
    st.markdown("Hamburgesa de Queso + 1 Coca Cola 600ml",text_alignment="center")
with col2:
    st.markdown("Alitas Buffalo + 1 Cerveza Corona 500ml",text_alignment="center")
col3, col4 = st.columns(2, border = True)
with col3:
    st.markdown("Burrito Grande + Agua de Horchata 1L", text_alignment="center")
with col4:
    st.markdown("Tostada de Ceviche + 1 7up 600ml",text_alignment="center")
st.space(size="small")

#---------------------------------------------------
st.subheader("Calculo de Descuentos")
#dia, hora, no repartidores, perdida o ganancia
hora = st.slider("Hora")
# order_id
# customer_id
# customer_loyalty_tier
# customer_acquisition_channel
# customer_signup_date
# restaurant_id
# restaurant_cuisine
# restaurant_city
# restaurant_rating
# restaurant_avg_prep_time
# menu_item_id
# menu_item_name
# menu_item_category,item_pric
# quantity
# order_timestamp
# delivery_timestamp
# delivery_duration_actual
# delivery_duration_estimated
# delivery_fee
# tip
# total_amount
# discount_code
# discount_type
# discount_value
# order_status
# weather_temperature
# weather_precipitation
# is_weekend
# is_holiday
# event_flag
# delivery_delay
# order_hour
# order_day_of_week
# calculated_total
# total_amount_consistent
